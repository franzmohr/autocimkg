import psycopg2
import json
from ast import literal_eval
from typing import Union

from ..models import Document, Ontology, KnowledgeGraphVersion, Log
from .base import BaseMetadataIntegrator
from ..utils.errors import storage_error

class MetadataIntegrator(BaseMetadataIntegrator):
    """
    Designed to integrate and manage metadata in a PostgreSQL database.
    Implements the storage backend interface BaseMetadataIntegrator.
    """

    def __init__(self, host: str, port: int, dbname: str, username: str, password: str):
        """
        Initializes the GraphIntegrator with database connection parameters.
        The default PGSQL "public" schema is used!

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
        self.schema = "public"
        self.username = username
        self.password = password

    def init_db(self):
        """
        Creates the metadata tables in the database.
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            # data source
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.schema}.data_source(id SERIAL PRIMARY KEY, file_name text, "
                           "author text, full_text text, file_lang text, file_type text)")

            # knowledge graph version
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.schema}.kg_version(kg_name TEXT PRIMARY KEY, agent text, "
                           "start_proc_ts timestamp, end_proc_ts timestamp)")

            # configurations
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.schema}.ontology(id SERIAL PRIMARY KEY, kg_name text references "
                           "kg_version(kg_name), ontology jsonb)")
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.schema}.llm_config(id SERIAL PRIMARY KEY, kg_name text "
                           "references kg_version(kg_name), config jsonb)")
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.schema}.autocimkg_config(id SERIAL PRIMARY KEY, kg_name text "
                           "references kg_version(kg_name), config jsonb)")

            # logs
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.schema}.log(id SERIAL PRIMARY KEY, kg_name text references "
                           "kg_version(kg_name), ts timestamp, log_level text, logger_name text, message text)")

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.init_db()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def create_kg_version(self, kg_version: KnowledgeGraphVersion):
        """
        Creates graph version metadata in the database.

        :param kg_version: KG metadata to persist
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(
                f"INSERT INTO {self.schema}.kg_version(kg_name, agent, start_proc_ts, end_proc_ts) VALUES (%s, %s, %s, %s)",
                (kg_version.kg_name, kg_version.agent, kg_version.start_proc_ts, kg_version.end_proc_ts))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.create_kg_version()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_kg_version(self, kg_name: str):
        """
        Deletes graph version metadata from the database.

        :param kg_name: KG version to delete
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.kg_version WHERE kg_name = %s", (kg_name,))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_kg_version()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_kg_versions(self) -> list[KnowledgeGraphVersion]:
        """
        Reads all graph version metadata from the database.

        :returns: List of KG version metadata
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"SELECT kg_name, agent, start_proc_ts, end_proc_ts FROM {self.schema}.kg_version")
            rows = cursor.fetchall()

            kg_versions = []
            for row in rows:
                kg_versions.append(KnowledgeGraphVersion(kg_name=row[0], agent=row[1],
                                                         start_proc_ts=row[2], end_proc_ts=row[3]))

            return kg_versions
        except Exception as e:
            if connection: connection.rollback()  # even w/o change!
            raise storage_error(self.logger, "MetadataIntegrator.read_kg_versions()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def create_logs(self, kg_name: str, logs: list[Log]):
        """
        Creates construction log data in the database.

        :param kg_name: KG version for which to create log entries
        :param logs: List of log entries
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            for log in logs:
                cursor.execute(
                    f"INSERT INTO {self.schema}.log(kg_name, ts, log_level, logger_name, message) VALUES (%s, %s, %s, %s, %s)",
                    (kg_name, log.ts, log.log_level, log.logger_name, log.message))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.create_logs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_logs(self, kg_name: str) -> list[Log]:
        """
        Reads construction log data from the database.

        :param kg_name: KG version for which to read log entries
        :returns: List of construction log data
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"SELECT ts, log_level, logger_name, message FROM {self.schema}.log WHERE kg_name = %s", (kg_name,))
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                logs.append(Log(ts=row[0], log_level=row[1], logger_name=row[2], message=row[3]))

            return logs
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.read_logs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_logs(self, kg_name: str):
        """
        Deletes construction log data from the database.

        :param kg_name: KG version for which to delete log entries
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.log WHERE kg_name = %s", (kg_name,))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_logs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def create_data_sources(self, documents: list[Document]):
        """
        Creates data sources in the database.
        In the case of AutoCimKG this means documents!

        :param documents: List of data sources
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            for doc in documents:
                authors = MetadataIntegrator.transform_authors_to_str(doc.authors)
                content = MetadataIntegrator.transform_content_to_str(doc.content)
                cursor.execute(
                    f"INSERT INTO {self.schema}.data_source(file_name, author, full_text, file_lang, file_type) VALUES (%s, %s, %s , %s, %s)",
                    (doc.name, authors, content, doc.language, doc.doc_type))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.create_data_sources()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_data_sources(self) -> list[Document]:
        """
        Reads all data sources from the database.

        :returns: List of data sources (i.e. documents)
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"SELECT file_name, author, full_text, file_lang, file_type FROM {self.schema}.data_source")
            rows = cursor.fetchall()

            documents = []
            for row in rows:
                authors = MetadataIntegrator.transform_str_to_authors(row[1])
                documents.append(
                    Document(name=row[0], authors=authors, content=MetadataIntegrator.transform_str_to_content(row[2]),
                             language=row[3], doc_type=row[4]))

            return documents
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.read_data_sources()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_data_sources_by_name(self, name: str) -> list[Document]:
        """
        Reads data sources with specific name from the database.

        :param name: Data source name
        :returns: List of data sources (i.e. documents)
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(
                f"SELECT file_name, author, full_text, file_lang, file_type FROM {self.schema}.data_source WHERE file_name = %s",
                (name,))
            rows = cursor.fetchall()

            documents = []
            for row in rows:
                authors = MetadataIntegrator.transform_str_to_authors(row[1])
                documents.append(
                    Document(name=row[0], authors=authors, content=MetadataIntegrator.transform_str_to_content(row[2]),
                             language=row[3], doc_type=row[4]))

            return documents
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.read_data_sources_by_name()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_data_sources_by_name(self, name: str):
        """
        Deletes data sources with specific name from the database.

        :param name: Data source name
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.data_source WHERE file_name = %s", (name,))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_data_sources_by_name()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_data_sources(self):
        """
        Deletes data sources from the database.
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.data_source")

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_data_sources()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def create_ontology(self, kg_name: str, ont: Ontology):
        """
        Creates an ontology in the database.

        :param kg_name: KG version for which to create ontology for
        :param ont: Ontology to create
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"INSERT INTO {self.schema}.ontology(kg_name, " \
                           + " ontology) VALUES (%s, %s)",
                           (kg_name, json.dumps(ont.__dict__)))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.create_ontology()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_ontologies(self, kg_name: str) -> list[Ontology]:
        """
        Reads ontologies from the database.

        :param kg_name: KG version for which to read log entries
        :returns: List of ontologies
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"SELECT ontology FROM {self.schema}.ontology WHERE kg_name = %s", (kg_name,))
            rows = cursor.fetchall()

            ontologies = []
            for row in rows:
                ontologies.append(Ontology(**row[0]))

            return ontologies
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.read_ontologies()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_ontologies(self, kg_name: str):
        """
        Deletes ontologies from the database.

        :param kg_name: KG version for which to delete ontologies
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.ontology WHERE kg_name = %s", (kg_name,))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_ontologies()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def create_llm_config(self, kg_name: str, llm_config: dict):
        """
        Creates an LLM config in the database.

        :param kg_name: KG version for which to create LLM config for
        :param llm_config: LLM config to create
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"INSERT INTO {self.schema}.llm_config(kg_name, config) VALUES (%s, %s)",
                           (kg_name, json.dumps(llm_config)))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.create_llm_config()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_llm_configs(self, kg_name: str) -> list[dict]:
        """
        Reads LLM configs from the database.

        :param kg_name: KG version for which to read LLM configs
        :returns: List of LLM configs
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"SELECT config FROM {self.schema}.llm_config WHERE kg_name = %s", (kg_name,))
            rows = cursor.fetchall()

            llm_configs = []
            for row in rows:
                llm_configs.append(row[0])

            return llm_configs
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.read_llm_configs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_llm_configs(self, kg_name: str):
        """
        Deletes LLM configs from the database.

        :param kg_name: KG version for which to delete LLM configs
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.llm_config WHERE kg_name = %s", (kg_name,))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_llm_configs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def create_autocimkg_config(self, kg_name: str, autocimkg_config: dict):
        """
        Creates an AutoCimKG config in the database.

        :param kg_name: KG version for which to create AutoCimKG config for
        :param autocimkg_config: AutoCimKG config to create
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"INSERT INTO {self.schema}.autocimkg_config(kg_name, config) VALUES (%s, %s)",
                           (kg_name, json.dumps(autocimkg_config)))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.create_autocimkg_config()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def read_autocimkg_configs(self, kg_name: str) -> list[dict]:
        """
        Reads AutoCimKG configs from the database.

        :param kg_name: KG version for which to read AutoCimKG configs
        :returns: List of AutoCimKG configs
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"SELECT config FROM {self.schema}.autocimkg_config WHERE kg_name = %s", (kg_name,))
            rows = cursor.fetchall()

            autocimkg_configs = []
            for row in rows:
                autocimkg_configs.append(row[0])

            return autocimkg_configs
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.read_autocimkg_configs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def delete_autocimkg_configs(self, kg_name: str):
        """
        Deletes AutoCimKG configs from the database.

        :param kg_name: KG version for which to delete AutoCimKG configs
        """

        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password,
                                          host=self.host, port=self.port, database=self.dbname)
            cursor = connection.cursor()

            cursor.execute(f"DELETE FROM {self.schema}.autocimkg_config WHERE kg_name = %s", (kg_name,))

            connection.commit()
        except Exception as e:
            if connection: connection.rollback()
            raise storage_error(self.logger, "MetadataIntegrator.delete_autocimkg_configs()", e)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    @staticmethod
    def transform_authors_to_str(authors: list[str]) -> str:
        """
        Transforms a document's authors into their text representation in the database: a JSON array
        (e.g. ["Martin Summer", "Doe, Jane"]), or "" w/o authors.

        :param authors: List of author names
        :returns: Text representation of the authors
        """

        if not authors: return ""
        return json.dumps(list(authors), ensure_ascii=False)

    @staticmethod
    def transform_str_to_authors(authors_str: str) -> list[str]:
        """
        Transforms the text representation of a document's authors in the database back into a list (see
        transform_authors_to_str). Authors written by earlier versions as comma-separated names are read as well.

        :param authors_str: Text representation of the authors
        :returns: List of author names
        """

        if not authors_str: return []
        if authors_str.startswith("[") and authors_str.endswith("]"):
            try:
                authors = json.loads(authors_str)
                if isinstance(authors, list) and all(isinstance(author, str) for author in authors):
                    return authors
            except ValueError:
                pass
        return authors_str.split(",")  # earlier versions

    @staticmethod
    def transform_content_to_str(content: Union[str, list[str]]) -> str:
        """
        Transforms a document's content into its text representation in the database.
        Text is stored as is, a list of text blocks as JSON array (e.g. ["block 1", "block 2"]).

        :param content: Text or list of text blocks
        :returns: Text representation of the content
        """

        if isinstance(content, list): return json.dumps(content, ensure_ascii=False)
        return content

    @staticmethod
    def transform_str_to_content(content_str: str) -> Union[str, list[str]]:
        """
        Transforms the text representation of a document's content in the database back into text or a list of
        text blocks (see transform_content_to_str). Lists written by earlier versions as quoted Python lists
        (e.g. '['block 1', 'block 2']') are read as well.

        :param content_str: Text representation of the content
        :returns: Text or list of text blocks
        """

        if not content_str: return content_str
        candidates = []
        if content_str.startswith("[") and content_str.endswith("]"):
            candidates.append(lambda: json.loads(content_str))
        if content_str.startswith("'[") and content_str.endswith("]'"):  # earlier versions
            candidates.append(lambda: literal_eval(content_str[1:-1]))
        for parse in candidates:
            try:
                content = parse()
            except (ValueError, SyntaxError):
                continue
            if isinstance(content, list) and all(isinstance(block, str) for block in content):
                return content
        return content_str