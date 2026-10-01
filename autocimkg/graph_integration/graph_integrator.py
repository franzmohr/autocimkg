from datetime import datetime

import age
import json
import numpy as np
from ..models import KnowledgeGraph, Relationship, Entity, EntityProperties, RelationshipProperties
from .base import BaseGraphIntegrator
from ..utils.errors import storage_error
from typing import Union

class GraphIntegrator(BaseGraphIntegrator):
    """
    Designed to integrate and manage graph data in a PostgreSQL (and Apache AGE) database.
    Implements the storage backend interface BaseGraphIntegrator.
    """

    def __init__(self, host: str, port: int, dbname: str, username: str, password: str):
        """
        Initializes the GraphIntegrator with database connection parameters.
        
        :param host: URI for the database
        :param port: Port for the database
        :param dbname: Database name
        :param username: Username for database access
        :param password: Password for database access
        """

        super().__init__()

        self.host = host
        self.port = port
        self.dbname = dbname
        self.username = username
        self.password = password

    def create_graph(self, graph_name: str):
        """
        Creates a named graph in the database.

        :param graph_name: Graph name in the PGSQL/AAGE database
        """
        connection = None
        try:
            # implicitly creates kg (if not already present) ...
            connection = self.connect(graph_name)
            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, f"Creating graph '{graph_name}'", e)
        finally:
            if connection: connection.close()

    def delete_graph(self, graph_name: str):
        """
        Deletes a named graph in the database (if present).

        :param graph_name: Graph name in the PGSQL/AAGE database
        """
        connection = None
        try:
            connection = self.connect()
            if GraphIntegrator.graph_exists(connection, graph_name):
                age.deleteGraph(connection.connection, graph_name)
            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, f"Deleting graph '{graph_name}'", e)
        finally:
            if connection: connection.close()

    def read_graph(self, graph_name: str) -> KnowledgeGraph:
        """
        Runs the necessary queries to read a graph structure from the PGSQL/AAGE database.

        :param graph_name: Graph name in the PGSQL/AAGE database
        :returns: KnowledgeGraph containing the graph structure
        :raises StorageError: Graph doesn't exist or can't be read
        """

        connection = None
        cursor = None
        try:
            connection = self.connect()  # w/o graph name, which would create a missing graph
            if not GraphIntegrator.graph_exists(connection, graph_name):
                raise LookupError("graph doesn't exist")
            cursor = connection.connection.cursor()

            # basic assumption: reading all (!) nodes and all (!) relations leads to consistent result!
            # results are read as agtype text, i.e. JSON: the agtype parser of apache-age-python doesn't unescape
            # strings (e.g. backslashes or double quotes) correctly

            # NODES
            cursor.execute("SELECT v::text from cypher(%s, $$ MATCH (n) RETURN [label(n), properties(n)] $$) "
                           "as (v agtype);", (graph_name,))
            entities = []
            for row in cursor:
                label, properties = json.loads(row[0])
                entities.append(GraphIntegrator.transform_to_entity(label, properties))

            # EDGES
            cursor.execute("SELECT v::text from cypher(%s, $$ MATCH (n)-[r]->(m) RETURN [label(n), properties(n), "
                           "label(r), properties(r), label(m), properties(m)] $$) as (v agtype);", (graph_name,))
            relationships = []
            for row in cursor:
                start_label, start_properties, name, properties, end_label, end_properties = json.loads(row[0])
                relationship = Relationship(startEntity=GraphIntegrator.transform_to_entity(start_label, start_properties),
                                            endEntity=GraphIntegrator.transform_to_entity(end_label, end_properties),
                                            name=name)
                GraphIntegrator.transform_to_properties(properties, relationship.properties)
                relationships.append(relationship)

            # = KG
            knowledge_graph = KnowledgeGraph(relationships=relationships, entities=entities)

            return knowledge_graph

        except Exception as e:
            if connection: connection.rollback()  # even w/o change!
            raise storage_error(self.logger, f"Reading graph '{graph_name}'", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def write_graph(self, graph_name: str, knowledge_graph: KnowledgeGraph) -> None:
        """
        Runs the necessary queries to write a graph structure into the PGSQL/AAGE database.

        :param graph_name: Graph name in the PGSQL/AAGE database
        :param knowledge_graph: KnowledgeGraph containing the graph structure
        """

        node_write_queries, relationship_write_queries = (
            self.create_node_write_queries(knowledge_graph=knowledge_graph),
            self.create_relationship_write_queries(knowledge_graph=knowledge_graph),
        )

        connection = None
        cursor = None
        try:
            connection = self.connect(graph_name)  # creates the graph, if not already present
            cursor = connection.connection.cursor()

            for node_write_query in node_write_queries:
                cursor.execute(f"SELECT * from cypher(%s, $$ {node_write_query} $$) as (v agtype);", (graph_name,))
                # execCypher() and cypher() do not work due to invalid escaping of special characters (e.g. umlauts) ...
            for relationship_write_query in relationship_write_queries:
                cursor.execute(f"SELECT * from cypher(%s, $$ {relationship_write_query} $$) as (v agtype);", (graph_name,))
                # execCypher() and cypher() do not work due to invalid escaping of special characters (e.g. umlauts) ...

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, f"Writing graph '{graph_name}'", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def connect(self, graph_name: str = None):
        """
        Connects to the database and sets up Apache AGE.

        :param graph_name: Graph to create, if not already present (none by default)
        :returns: Apache AGE connection
        """

        return age.connect(host=self.host, port=self.port, dbname=self.dbname, user=self.username,
                           password=self.password, graph=graph_name)

    @staticmethod
    def graph_exists(connection, graph_name: str) -> bool:
        """
        Checks whether a named graph exists in the database.

        :param connection: Apache AGE connection
        :param graph_name: Graph name in the PGSQL/AAGE database
        :returns: True, if the graph exists
        """

        with connection.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = %s", (graph_name,))
            return cursor.fetchone()[0] > 0

    @staticmethod
    def create_node_write_queries(knowledge_graph: KnowledgeGraph) -> list[str]:
        """
        Constructs Cypher queries for creating nodes in the graph database from a KnowledgeGraph object.

        :param knowledge_graph: KnowledgeGraph containing entities
        :returns: List of Cypher queries for node creation
        """

        queries = []
        for node in knowledge_graph.entities:
            properties = []
            for prop, value in node.properties.model_dump().items():
                if prop == "embeddings":
                    value = GraphIntegrator.transform_embeddings_to_str_list(value)
                elif prop == "generated_at_time":
                    value = GraphIntegrator.transform_datetime_to_str(value)
                elif prop == "invalidated_at_time":
                    value = GraphIntegrator.transform_datetime_to_str(value)

                properties.append(f'SET n.{prop.replace(" ", "_")} = {GraphIntegrator.transform_to_cypher_literal(value)}')

            query = (f'CREATE (n:{node.label} {{name: {GraphIntegrator.transform_to_cypher_literal(node.name)}}}) '
                     + ' '.join(properties))
            queries.append(query)
        return queries

    @staticmethod
    def create_relationship_write_queries(knowledge_graph: KnowledgeGraph) -> list:
        """
        Constructs Cypher queries for creating relationships in the graph database from a KnowledgeGraph object.

        :param knowledge_graph: KnowledgeGraph containing relationships
        :returns: List of Cypher queries for relationship creation
        """

        rels = []
        for rel in knowledge_graph.relationships:
            properties = []
            for key, value in rel.properties.model_dump().items():
                if key == "embeddings":
                    value = GraphIntegrator.transform_embeddings_to_str_list(value)
                elif key == "generated_at_time":
                    value = GraphIntegrator.transform_datetime_to_str(value)
                elif key == "invalidated_at_time":
                    value = GraphIntegrator.transform_datetime_to_str(value)

                properties.append(f'SET r.{key.replace(" ", "_")} = {GraphIntegrator.transform_to_cypher_literal(value)}')

            query = (
                f'MATCH (n:{rel.startEntity.label} {{name: {GraphIntegrator.transform_to_cypher_literal(rel.startEntity.name)}}}), '
                f'(m:{rel.endEntity.label} {{name: {GraphIntegrator.transform_to_cypher_literal(rel.endEntity.name)}}}) '
                f'CREATE (n)-[r:{rel.name}]->(m) ' + ' '.join(properties)
            )
            rels.append(query)

        return rels

    @staticmethod
    def transform_datetime_to_str(ts: Union[datetime, None]) -> str:
        """
        Transforms a datetime object to a string representation.
        Format: %Y:%M:%D %h%m%s.%f (e.g. 2025-02-28 14:55:02.775121)

        :param ts: Datetime object (or None)
        :return: String representation of datetime object
        """

        if ts is None: return ""
        return ts.__str__()

    @staticmethod
    def transform_str_to_datetime(ts_str: str) -> Union[datetime, None]:
        """
        Transforms a string representation to a datetime object.
        Format: '%Y:%M:%D %h%m%s.%f' (e.g. 2025-02-28 14:55:02.775121)

        :param ts_str: String representation of datetime object
        :return: Datetime object (or None)
        """

        if ts_str is None or ts_str == "": return None
        return datetime.fromisoformat(ts_str)

    @staticmethod
    def transform_embeddings_to_str_list(embeddings: np.array):
        """
        Transforms a NumPy array of embeddings into a comma-separated string.

        :param embeddings: Array of embeddings
        :returns: Comma-separated string of embeddings
        """

        if embeddings is None:
            return ""
        return ",".join(list(embeddings.astype("str")))

    @staticmethod
    def transform_str_list_to_embeddings(embeddings: str):
        """
        Transforms a comma-separated string of embeddings back into a NumPy array.

        :param embeddings: Comma-separated string of embeddings
        :returns: NumPy array of embeddings (or None, if the entity or relationship has none)
        """

        if embeddings is None or embeddings == "":  # written as "" w/o embeddings (see transform_embeddings_to_str_list)
            return None
        return np.array(embeddings.split(",")).astype(np.float64)

    @staticmethod
    def transform_to_cypher_literal(value: Union[str, list]) -> str:
        """
        Transforms a string (or list of strings) into a Cypher literal, escaping special characters (e.g. quotes,
        backslashes and line breaks). '$' is escaped as well, as '$$' would end the query passed to cypher().

        :param value: String or list of strings
        :returns: Cypher literal (e.g. "o'brien" or ["doc 1.pdf", "doc 2.pdf"])
        """

        if isinstance(value, list):
            return "[" + ", ".join(GraphIntegrator.transform_to_cypher_literal(item) for item in value) + "]"
        return json.dumps(str(value), ensure_ascii=False).replace("$", "\\u0024")

    @staticmethod
    def transform_to_entity(label: str, properties: dict) -> Entity:
        """
        Transforms the label and properties of a node read from the database into an entity.

        :param label: Node label
        :param properties: Node properties
        :returns: Entity
        """

        entity = Entity(label=label, name=properties.get("name", ""))
        GraphIntegrator.transform_to_properties(properties, entity.properties)
        return entity

    @staticmethod
    def transform_to_properties(properties: dict, target: Union[EntityProperties, RelationshipProperties]) -> None:
        """
        Transforms the properties of a node or edge read from the database into entity or relationship properties.

        :param properties: Node or edge properties
        :param target: Entity or relationship properties to fill
        """

        target.embeddings = GraphIntegrator.transform_str_list_to_embeddings(properties.get("embeddings"))
        target.generated_at_time = GraphIntegrator.transform_str_to_datetime(properties.get("generated_at_time"))
        target.invalidated_at_time = GraphIntegrator.transform_str_to_datetime(properties.get("invalidated_at_time"))
        target.agents = properties.get("agents", [])
        target.origins = properties.get("origins", [])