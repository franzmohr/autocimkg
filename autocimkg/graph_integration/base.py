from abc import ABC, abstractmethod

from ..models import KnowledgeGraph
from ..utils.logger import create_logger


class BaseGraphIntegrator(ABC):
    """
    Interface of a storage backend for knowledge graphs (e.g. PostgreSQL/Apache AGE, see GraphIntegrator).
    AutoCimKG's pipeline itself works on KnowledgeGraph objects only, so further backends (e.g. Delta tables)
    implement this interface and can be used interchangeably.

    Contract: writing a graph and reading it back yields the same entities and relationships, incl. their labels,
    names and properties (embeddings, generated and invalidated timestamps, agents and origins; embeddings and
    timestamps may be None). Labels and relationship names are identifiers as produced by Entity.process() and
    Relationship.process() (letters, digits and '_', not starting w/ a digit). Relationships refer
    to their start and end entity by label and name.
    A failed operation raises a StorageError (and is logged via self.logger), incl. reading a graph that doesn't
    exist; deleting a graph that doesn't exist does nothing.
    """

    def __init__(self):
        """
        Initializes the stdout logger shared by AutoCimKG's components.
        """

        self.logger = create_logger()

    @abstractmethod
    def create_graph(self, graph_name: str):
        """
        Creates an empty, named graph (if not already present).

        :param graph_name: Graph name
        """

    @abstractmethod
    def delete_graph(self, graph_name: str):
        """
        Deletes a named graph incl. all of its entities and relationships (if present).

        :param graph_name: Graph name
        """

    @abstractmethod
    def read_graph(self, graph_name: str) -> KnowledgeGraph:
        """
        Reads a named graph.

        :param graph_name: Graph name
        :returns: KnowledgeGraph containing the graph structure
        :raises StorageError: Graph doesn't exist or can't be read
        """

    @abstractmethod
    def write_graph(self, graph_name: str, knowledge_graph: KnowledgeGraph) -> None:
        """
        Writes a graph structure into a named graph (which is created, if not already present).

        :param graph_name: Graph name
        :param knowledge_graph: KnowledgeGraph containing the graph structure
        """
