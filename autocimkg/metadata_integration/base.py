from abc import ABC, abstractmethod

from ..models import Document, Ontology, KnowledgeGraphVersion, Log
from ..utils.logger import create_logger


class BaseMetadataIntegrator(ABC):
    """
    Interface of a storage backend for AutoCimKG's metadata repository (e.g. PostgreSQL, see MetadataIntegrator).
    AutoCimKG's pipeline itself doesn't depend on a specific backend, so further backends (e.g. Delta tables)
    implement this interface and can be used interchangeably.

    Contract: metadata is stored per KG version (kg_name), except data sources (documents), which are shared
    across versions. Whatever is created can be read back unchanged (incl. timestamps, a document's content as text
    or list of text blocks, and nested dicts) and deleted again.
    Errors are logged via self.logger and don't interrupt the program flow; reading then returns None.
    """

    def __init__(self):
        """
        Initializes the stdout logger shared by AutoCimKG's components.
        """

        self.logger = create_logger()

    @abstractmethod
    def init_db(self):
        """
        Creates the storage structures of the metadata repository (if not already present).
        """

    # KG versions

    @abstractmethod
    def create_kg_version(self, kg_version: KnowledgeGraphVersion):
        """
        Creates graph version metadata.

        :param kg_version: KG metadata to persist
        """

    @abstractmethod
    def delete_kg_version(self, kg_name: str):
        """
        Deletes graph version metadata.

        :param kg_name: KG version to delete
        """

    @abstractmethod
    def read_kg_versions(self) -> list[KnowledgeGraphVersion]:
        """
        Reads all graph version metadata.

        :returns: List of KG version metadata
        """

    # construction logs

    @abstractmethod
    def create_logs(self, kg_name: str, logs: list[Log]):
        """
        Creates construction log data.

        :param kg_name: KG version for which to create log entries
        :param logs: List of log entries
        """

    @abstractmethod
    def read_logs(self, kg_name: str) -> list[Log]:
        """
        Reads construction log data.

        :param kg_name: KG version for which to read log entries
        :returns: List of construction log data
        """

    @abstractmethod
    def delete_logs(self, kg_name: str):
        """
        Deletes construction log data.

        :param kg_name: KG version for which to delete log entries
        """

    # data sources (i.e. documents)

    @abstractmethod
    def create_data_sources(self, documents: list[Document]):
        """
        Creates data sources (i.e. documents, incl. name, authors, content, language and type).

        :param documents: List of data sources
        """

    @abstractmethod
    def read_data_sources(self) -> list[Document]:
        """
        Reads all data sources.

        :returns: List of data sources (i.e. documents)
        """

    @abstractmethod
    def read_data_sources_by_name(self, name: str) -> list[Document]:
        """
        Reads data sources with specific name.

        :param name: Data source name
        :returns: List of data sources (i.e. documents)
        """

    @abstractmethod
    def delete_data_sources_by_name(self, name: str):
        """
        Deletes data sources with specific name.

        :param name: Data source name
        """

    @abstractmethod
    def delete_data_sources(self):
        """
        Deletes all data sources.
        """

    # configurations

    @abstractmethod
    def create_ontology(self, kg_name: str, ont: Ontology):
        """
        Creates an ontology.

        :param kg_name: KG version for which to create ontology for
        :param ont: Ontology to create
        """

    @abstractmethod
    def read_ontologies(self, kg_name: str) -> list[Ontology]:
        """
        Reads ontologies.

        :param kg_name: KG version for which to read ontologies
        :returns: List of ontologies
        """

    @abstractmethod
    def delete_ontologies(self, kg_name: str):
        """
        Deletes ontologies.

        :param kg_name: KG version for which to delete ontologies
        """

    @abstractmethod
    def create_llm_config(self, kg_name: str, llm_config: dict):
        """
        Creates an LLM config (e.g. from get_model_config()).

        :param kg_name: KG version for which to create LLM config for
        :param llm_config: LLM config to create
        """

    @abstractmethod
    def read_llm_configs(self, kg_name: str) -> list[dict]:
        """
        Reads LLM configs.

        :param kg_name: KG version for which to read LLM configs
        :returns: List of LLM configs
        """

    @abstractmethod
    def delete_llm_configs(self, kg_name: str):
        """
        Deletes LLM configs.

        :param kg_name: KG version for which to delete LLM configs
        """

    @abstractmethod
    def create_autocimkg_config(self, kg_name: str, autocimkg_config: dict):
        """
        Creates an AutoCimKG config (i.e. the parameters of a build_graph() run).

        :param kg_name: KG version for which to create AutoCimKG config for
        :param autocimkg_config: AutoCimKG config to create
        """

    @abstractmethod
    def read_autocimkg_configs(self, kg_name: str) -> list[dict]:
        """
        Reads AutoCimKG configs.

        :param kg_name: KG version for which to read AutoCimKG configs
        :returns: List of AutoCimKG configs
        """

    @abstractmethod
    def delete_autocimkg_configs(self, kg_name: str):
        """
        Deletes AutoCimKG configs.

        :param kg_name: KG version for which to delete AutoCimKG configs
        """
