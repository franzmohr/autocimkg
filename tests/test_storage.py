"""
Tests of the storage backend interfaces (BaseGraphIntegrator, BaseMetadataIntegrator) and a contract test that every
backend has to pass. The contract test runs against PostgreSQL/Apache AGE if AUTOCIMKG_TEST_DB_HOST is set
(plus AUTOCIMKG_TEST_DB_PORT, _NAME, _USER and _PASSWORD); it writes, reads and deletes its own uniquely named data.
To test a further backend, add a factory for it to GRAPH_BACKENDS / METADATA_BACKENDS.
"""
import os
import subprocess
import sys
import uuid
from datetime import datetime

import numpy as np
import pytest

from autocimkg.graph_integration import BaseGraphIntegrator
from autocimkg.metadata_integration import BaseMetadataIntegrator
from autocimkg.models import (Document, Entity, EntityProperties, KnowledgeGraph, KnowledgeGraphVersion, Log,
                              Ontology, Relationship, RelationshipProperties)


# ---------------------------------------------------------------- backends

def db_args() -> dict:
    return dict(host=os.environ["AUTOCIMKG_TEST_DB_HOST"], port=int(os.environ.get("AUTOCIMKG_TEST_DB_PORT", "5432")),
                dbname=os.environ.get("AUTOCIMKG_TEST_DB_NAME", "postgres"),
                username=os.environ.get("AUTOCIMKG_TEST_DB_USER", "postgres"),
                password=os.environ.get("AUTOCIMKG_TEST_DB_PASSWORD", ""))


def age_graph_integrator() -> BaseGraphIntegrator:
    from autocimkg.graph_integration import GraphIntegrator
    return GraphIntegrator(**db_args())


def postgres_metadata_integrator() -> BaseMetadataIntegrator:
    from autocimkg.metadata_integration import MetadataIntegrator
    return MetadataIntegrator(**db_args())


needs_db = pytest.mark.skipif(not os.environ.get("AUTOCIMKG_TEST_DB_HOST"), reason="AUTOCIMKG_TEST_DB_HOST not set")
GRAPH_BACKENDS = [pytest.param(age_graph_integrator, id="age", marks=needs_db)]
METADATA_BACKENDS = [pytest.param(postgres_metadata_integrator, id="postgres", marks=needs_db)]


# ---------------------------------------------------------------- interfaces

def test_package_imports_without_database_drivers():
    # other backends must not need PostgreSQL/Apache AGE drivers: block them and import the package and interfaces
    code = ("import sys; sys.modules.update(age=None, psycopg2=None)\n"
            "import autocimkg\n"
            "from autocimkg.graph_integration import BaseGraphIntegrator\n"
            "from autocimkg.metadata_integration import BaseMetadataIntegrator\n"
            "try:\n"
            "    autocimkg.GraphIntegrator\n"
            "except ImportError:\n"
            "    print('ok')\n")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.stdout.strip() == "ok", result.stderr


@pytest.mark.parametrize("base", [BaseGraphIntegrator, BaseMetadataIntegrator])
def test_interfaces_are_abstract(base):
    with pytest.raises(TypeError):
        base()


def test_postgres_backends_implement_interfaces():
    from autocimkg import GraphIntegrator as TopLevelGraphIntegrator
    from autocimkg.graph_integration import GraphIntegrator
    from autocimkg.metadata_integration import MetadataIntegrator

    assert TopLevelGraphIntegrator is GraphIntegrator
    for backend, base in ((GraphIntegrator, BaseGraphIntegrator), (MetadataIntegrator, BaseMetadataIntegrator)):
        assert issubclass(backend, base)
        assert not backend.__abstractmethods__  # implements every method of the interface
        public = {name for name in vars(base) if not name.startswith("_")}
        assert public == set(base.__abstractmethods__), "interface methods must all be abstract"


# ---------------------------------------------------------------- contract

TS = datetime(2026, 9, 30, 12, 34, 56, 789012)


def entity(label: str, name: str, seed: int) -> Entity:
    properties = EntityProperties(embeddings=np.random.default_rng(seed).random(8), generated_at_time=TS,
                                  agents=["AutoCimKG"], origins=["doc.pdf"])
    return Entity(label=label, name=name, properties=properties)


SKILL = "stress testing $$ c:\\data 'q' \"über\"\nnext"  # special characters must survive writing and reading


def sample_graph() -> KnowledgeGraph:
    expert, skill = entity("Expert", "jane doe", 1), entity("Competence", SKILL, 2)
    skill.properties.invalidated_at_time = TS
    skill.properties.origins = ["O'Brien's \"paper\" $1.pdf", "doc.pdf"]
    company = Entity(label="Company", name="acme")  # w/o embeddings and timestamps
    knows = Relationship(startEntity=expert, endEntity=skill, name="knows",
                         properties=RelationshipProperties(embeddings=np.random.default_rng(3).random(8),
                                                           generated_at_time=TS, agents=["AutoCimKG"],
                                                           origins=["doc.pdf"]))
    return KnowledgeGraph(entities=[expert, skill, company], relationships=[knows])


def assert_same_properties(actual, expected):
    if expected.embeddings is None:
        assert actual.embeddings is None
    else:
        np.testing.assert_allclose(actual.embeddings, expected.embeddings)
    assert (actual.generated_at_time, actual.invalidated_at_time) == (expected.generated_at_time,
                                                                      expected.invalidated_at_time)
    assert (list(actual.agents), list(actual.origins)) == (expected.agents, expected.origins)


@pytest.mark.parametrize("make_backend", GRAPH_BACKENDS)
def test_graph_backend_contract(make_backend):
    backend, graph, expected = make_backend(), f"test_{uuid.uuid4().hex[:12]}", sample_graph()
    try:
        backend.write_graph(graph, expected)
        actual = backend.read_graph(graph)

        entities = {(e.label, e.name): e for e in actual.entities}
        assert set(entities) == {(e.label, e.name) for e in expected.entities}
        for e in expected.entities:
            assert_same_properties(entities[(e.label, e.name)].properties, e.properties)

        [relationship] = actual.relationships
        assert (relationship.startEntity.name, relationship.name, relationship.endEntity.name) == \
               ("jane doe", "knows", SKILL)
        assert_same_properties(relationship.properties, expected.relationships[0].properties)
    finally:
        backend.delete_graph(graph)
    deleted = backend.read_graph(graph)
    assert deleted is None or not deleted.entities


@pytest.mark.parametrize("make_backend", METADATA_BACKENDS)
def test_metadata_backend_contract(make_backend):
    backend, kg, source = make_backend(), f"test_{uuid.uuid4().hex[:12]}", f"test_{uuid.uuid4().hex[:12]}.pdf"
    blocks_source, blocks = f"test_{uuid.uuid4().hex[:12]}.pdf", ["title - Stress 'tests'", "abstract - Über [1]"]
    backend.init_db()
    backend.init_db()  # idempotent
    llm_config = {"model": "qwen3.5:9b", "temperature": 0, "class": "langchain_ollama.ChatOllama"}
    autocimkg_config = {"ent_threshold": 0.8, "ontology": {"strict": False}, "domains": ["finance"]}
    try:
        backend.create_kg_version(KnowledgeGraphVersion(kg_name=kg, agent="AutoCimKG", start_proc_ts=TS,
                                                        end_proc_ts=TS))
        backend.create_logs(kg, [Log(ts=TS, logger_name="autocimkg", log_level="INFO", message="Entity created")])
        backend.create_data_sources([Document(name=source, doc_type="scientific article", content="Abstract ...",
                                              authors=["Jane Doe", "John Doe"], language="eng"),
                                     Document(name=blocks_source, doc_type="scientific article", content=blocks,
                                              authors=[], language="eng")])
        backend.create_ontology(kg, Ontology(topics=[{"Finance": "Financial topics"}],
                                             relations=[{"knows": "Knowledge"}], strict=False))
        backend.create_llm_config(kg, llm_config)
        backend.create_autocimkg_config(kg, autocimkg_config)

        [version] = [v for v in backend.read_kg_versions() if v.kg_name == kg]
        assert (version.agent, version.start_proc_ts, version.end_proc_ts) == ("AutoCimKG", TS, TS)
        [log] = backend.read_logs(kg)
        assert (log.ts, log.logger_name, log.log_level, log.message) == (TS, "autocimkg", "INFO", "Entity created")
        [doc] = backend.read_data_sources_by_name(source)
        assert (doc.doc_type, doc.content, list(doc.authors), doc.language) == \
               ("scientific article", "Abstract ...", ["Jane Doe", "John Doe"], "eng")
        [blocks_doc] = backend.read_data_sources_by_name(blocks_source)
        assert (blocks_doc.content, list(blocks_doc.authors)) == (blocks, [])
        assert {source, blocks_source} <= {d.name for d in backend.read_data_sources()}
        [ontology] = backend.read_ontologies(kg)
        assert (ontology.topics, ontology.relations, ontology.strict) == \
               ([{"Finance": "Financial topics"}], [{"knows": "Knowledge"}], False)
        assert backend.read_llm_configs(kg) == [llm_config]
        assert backend.read_autocimkg_configs(kg) == [autocimkg_config]
    finally:
        backend.delete_logs(kg)
        backend.delete_ontologies(kg)
        backend.delete_llm_configs(kg)
        backend.delete_autocimkg_configs(kg)
        backend.delete_kg_version(kg)
        backend.delete_data_sources_by_name(source)
        backend.delete_data_sources_by_name(blocks_source)

    assert kg not in [v.kg_name for v in backend.read_kg_versions()]
    assert not backend.read_logs(kg) and not backend.read_ontologies(kg)
    assert not backend.read_llm_configs(kg) and not backend.read_autocimkg_configs(kg)
    assert not backend.read_data_sources_by_name(source) and not backend.read_data_sources_by_name(blocks_source)


@pytest.mark.parametrize("stored, content", [
    ("Plain text", "Plain text"),
    ('["block 1", "Über \\"2\\""]', ["block 1", 'Über "2"']),  # lists as JSON array
    ("'['block 1', \"block's 2\"]'", ["block 1", "block's 2"]),  # lists as written by earlier versions
    ("[1] Plain text w/ brackets [2]", "[1] Plain text w/ brackets [2]"),
    ("[1, 2]", "[1, 2]"),  # JSON, but not a list of text blocks
    ("", ""),
])
def test_postgres_document_content_format(stored, content):
    from autocimkg.metadata_integration.metadata_integrator import MetadataIntegrator

    assert MetadataIntegrator.transform_str_to_content(stored) == content
    if isinstance(content, list):
        assert MetadataIntegrator.transform_str_to_content(MetadataIntegrator.transform_content_to_str(content)) == content
