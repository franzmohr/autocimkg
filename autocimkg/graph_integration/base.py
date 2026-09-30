from abc import ABC, abstractmethod

from ..models import KnowledgeGraph
from ..utils.logger import create_logger


class BaseGraphIntegrator(ABC):
    """
    Interface of a storage backend for knowledge graphs (e.g. PostgreSQL/Apache AGE, see GraphIntegrator).
    AutoCimKG's pipeline itself works on KnowledgeGraph objects only, so further backends (e.g. Delta tables)
    implement this interface and can be used interchangeably.

    Contract: writing a graph and reading it back yields the same entities and relationships, incl. their labels,
    names and properties (embeddings, generated and invalidated timestamps, agents and origins). Relationships refer
    to their start and end entity by label and name.
    Errors are logged via self.logger and don't interrupt the program flow; reading then returns None.
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
        Deletes a named graph incl. all of its entities and relationships.

        :param graph_name: Graph name
        """

    @abstractmethod
    def read_graph(self, graph_name: str) -> KnowledgeGraph:
        """
        Reads a named graph.

        :param graph_name: Graph name
        :returns: KnowledgeGraph containing the graph structure
        """

    @abstractmethod
    def write_graph(self, graph_name: str, knowledge_graph: KnowledgeGraph) -> None:
        """
        Writes a graph structure into a named graph (which is created, if not already present).

        :param graph_name: Graph name
        :param knowledge_graph: KnowledgeGraph containing the graph structure
        """
