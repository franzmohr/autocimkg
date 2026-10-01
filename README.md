# AutoCimKG: Automatic Construction and Incremental Maintenance of Knowledge Graphs

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15834992.svg)](https://doi.org/10.5281/zenodo.15834992)

AutoCimKG is a reusable, prototypical Python module that automatically builds and incrementally updates knowledge graphs (KGs) about experts and competencies. 
It applies unified, semantic text processing by prompting off-the-shelf large language models (LLMs), such as OpenAI's [GPT-4o](https://openai.com/de-DE/index/hello-gpt-4o/).
For this purpose, the approach utilises the LLM abstraction framework [LangChain](https://www.langchain.com/).
The training-free AutoCimKG consumes unstructured texts and tries to elicit knowledge and skills (as well as their relations) applied in the processed documents and attributable to their authors.
Additionally, it processes relational master data to resolve valid experts and determine associated facts like department affiliation or employment status. 
Consequently, the extensible prototype yields an overall KG that encodes distinct experts, competencies, documents and organisational units across inputs.
This is supported by ongoing entity and relationship resolution (building on text embeddings calculated by LLMs, such as OpenAI's [text-embedding-3-large](https://openai.com/index/new-embedding-models-and-api-updates/)). 
Moreover, an existing KG can be extended incrementally with new documents, if available. No batch-like rebuild is needed for this purpose.
<br/>
<br/>
The developed software system offers even more functionality. AutoCimKG also allows to store and retrieve snapshots of KGs to and from a connected [PostgreSQL/Apache AGE database](https://age.apache.org/), which enables query-based utilisation and makes the KG available for downstream tasks.
Moreover, the system also offers to process a user-defined lightweight ontology (respectively semantic schema). 
Here, specialist subject areas and specific relationship types are definable that align the LLM-based extraction of competencies and their relations from text. 
More specifically, subject areas are semantically linked to subordinate competencies and integrated into the KG (adding a more coarse-grained level for utilisation).
Moreover, the ontology lets the user define a strictness level, which indicates to either filter out incompatible competencies or suggest new subject areas for ontology evolution.
Contrarily, relationship types are used to filter and standardise extracted competency relationships.
Last but not least, AutoCimKG manages comprehensive metadata and realises a relational metadata repository in the connected PostgreSQL/Apache AGE database. 
Thus, it allows to store and retrieve data sources, KG version information, system logs, LLM as well as system configurations and applied ontologies. 
In addition, the assembled property graph encodes embedded (i.e. fact-level) provenance about editors, sources and generation as well as invalidation moments.
<br/>
<br/>
The artefact AutoCimKG was developed in the course of a master's thesis. Further information about the project is provided there.
- **Title**: 'Automatic Construction and Incremental Maintenance of Knowledge Graphs: Encoding Employee Competencies in the Case of the Austrian Financial Market Authority'
- **Author:** Gerhard Lerch
- **Year:** 2025
- **University:** Johannes Kepler Universit&auml;t Linz
## About this Fork
This repository continues the development of AutoCimKG. The [original repository](https://github.com/gary4512/autocimkg) by Gerhard Lerch is preserved as the final state of the master's thesis above and is no longer maintained.
Credit for the design and implementation of AutoCimKG goes to its original author. If you use AutoCimKG in your work, please cite the original software ([DOI 10.5281/zenodo.15834992](https://doi.org/10.5281/zenodo.15834992), see 'CITATION.cff') and the thesis.
<br/>
<br/>
Changes compared to the original version (2026-09):
- Support for further LLM providers besides OpenAI, including local models (see [LLM Providers](#llm-providers)); modified files: 'autocimkg/\_\_init\_\_.py', 'autocimkg/autocimkg_core.py', 'autocimkg/utils/\_\_init\_\_.py', 'autocimkg/utils/llm_integrator.py', 'tutorial/tutorial.ipynb'; new files: 'autocimkg/utils/llm_factory.py', 'requirements-optional.txt'.
- A read-only MCP server that makes stored KGs available to AI agents (new folder 'mcp_server/').
- Support for newer Python versions (v3.10 to v3.13) by replacing exact package versions with version ranges; modified files: 'requirements.txt', 'requirements-optional.txt'.
- Installable package that also runs on Databricks clusters, w/ LangChain v0.3 or v1 (see [Databricks](#databricks)); the logging module is no longer reloaded and the tutorial reads PDFs w/ pypdf directly; modified files: 'README.md', 'requirements.txt', 'autocimkg/autocimkg_core.py', 'autocimkg/utils/llm_integrator.py', 'autocimkg/graph_integration/graph_integrator.py', 'autocimkg/metadata_integration/metadata_integrator.py', 'autocimkg/models/knowledge_graph.py', 'tutorial/tutorial.ipynb'; new files: 'pyproject.toml', 'autocimkg/utils/logger.py'; removed files: 'requirements-optional.txt' (replaced by extras).
- Interchangeable storage backends: interfaces for graph and metadata storage, implemented by the existing PostgreSQL/Apache AGE connectors, whose drivers are imported on first use (see [Storage Backends](#storage-backends)); modified files: 'README.md', 'autocimkg/\_\_init\_\_.py', 'autocimkg/graph_integration/\_\_init\_\_.py', 'autocimkg/graph_integration/graph_integrator.py', 'autocimkg/metadata_integration/\_\_init\_\_.py', 'autocimkg/metadata_integration/metadata_integrator.py'; new files: 'autocimkg/graph_integration/base.py', 'autocimkg/metadata_integration/base.py', 'tests/test_storage.py'.
- Fixes in the PostgreSQL/Apache AGE connectors: graphs w/ entities or relationships w/o embeddings can be read again, a document's content stored as list of text blocks is read back as list, and author names may contain commas (earlier stored lists and authors included); modified files: 'autocimkg/graph_integration/graph_integrator.py', 'autocimkg/metadata_integration/metadata_integrator.py'.
- Further fixes: ```build_graph()``` no longer fails at the end when a log message spans several lines (e.g. the traceback of a retried LLM call), and names and properties w/ special characters (e.g. backslashes, quotes or '$$') are written to and read from Apache AGE unchanged instead of making the whole write fail; modified files: 'autocimkg/autocimkg_core.py', 'autocimkg/graph_integration/graph_integrator.py'; new files: 'tests/test_logging.py'.
- The storage connectors raise a ```StorageError``` when an operation fails, instead of only logging it (and returning None when reading); reading or deleting a graph no longer creates it, if missing; modified files: 'README.md', 'autocimkg/\_\_init\_\_.py', 'autocimkg/utils/\_\_init\_\_.py', 'autocimkg/graph_integration/base.py', 'autocimkg/graph_integration/graph_integrator.py', 'autocimkg/metadata_integration/base.py', 'autocimkg/metadata_integration/metadata_integrator.py', 'tests/test_storage.py'; new files: 'autocimkg/utils/errors.py'.
## License Notice
This software is based on and includes modified components of the [iText2KG library (v0.0.7)](https://github.com/AuvaLab/itext2kg), which is licensed under the GNU Lesser General Public Library (v2.1).
The extensive changes and enhancements made are reflected in all files of the reused codebase and correspond to the overview given above. 
This software is therefore also licensed under LGPL-2.1 and a copy of the license is provided in the 'LICENSE.txt' file.
<br/>
<br/>
Y. Lairgi, L. Moncla, R. Cazabet, K. Benabdeslem, and P. Cléau, ‘iText2KG: Incremental Knowledge Graphs Construction Using Large Language Models’, in Web Information Systems Engineering – WISE 2024, vol. 15439, M. Barhamgi, H. Wang, and X. Wang, Eds., in Lecture Notes in Computer Science, vol. 15439. , Singapore: Springer, 2025, pp. 214–229. doi: 10.1007/978-981-96-0573-6_16.
## Installation
AutoCimKG is a Python package and can be installed directly from GitHub, optionally with the extras of further LLM providers (see [LLM Providers](#llm-providers)):
```bash
pip install "autocimkg[ollama] @ git+https://github.com/franzmohr/autocimkg"
```
To work on AutoCimKG itself or run the tutorial, clone the repository and install it with ```pip install -r requirements.txt```. 
This installs the package in editable mode, together with the tutorial's packages and the test tools.
The tutorial can take the form of a [PyCharm](https://www.jetbrains.com/pycharm/) Python project centered around a [Jupyter Notebook](https://jupyter.org/).
The library needs a chat as well as an embedding model, either hosted (e.g. via OpenAI's [developer platform](https://platform.openai.com/)) or running locally (e.g. via [Ollama](https://ollama.com/)).
Moreover, AutoCimKG connects to a [PostgreSQL/Apache AGE database](https://age.apache.org/age-manual/master/intro/setup.html), if desired. 
Another recommendation is to set up the terminal-based [psql](https://www.postgresql.org/docs/current/app-psql.html) 
and [pgAdmin](https://www.pgadmin.org/) to inspect assembled property graphs as well as associated metadata and to query the competency KG (using SQL and Cypher).
<br/>
<br/>
In general, AutoCimKG was developed with Python v3.9 and runs on Python v3.9 to v3.13 (tested with v3.12 and v3.13), with LangChain v0.3 as well as v1. 
The dependencies are defined in 'pyproject.toml' as version ranges, so pip picks versions that suit the Python version and the packages already installed. 
The exact versions used in the master's thesis are those of the [original repository](https://github.com/gary4512/autocimkg/blob/main/requirements.txt).
### Databricks
On Databricks clusters (Databricks Runtime 14.3 LTS or later), install AutoCimKG as a notebook-scoped library and restart Python afterwards:
```python
%pip install "autocimkg @ git+https://github.com/franzmohr/autocimkg"
dbutils.library.restartPython()
```
Alternatively, build a wheel (```python -m build```), upload it to a Unity Catalog volume and install it from there, e.g. as a cluster library.
AutoCimKG works w/ the numpy, pandas, scikit-learn and psycopg2 versions preinstalled in the runtime, so no PostgreSQL build tools are needed on the cluster.
On runtimes w/ pydantic v1 (14.3 LTS and 15.4 LTS), pip upgrades pydantic to v2 for the notebook. 
Otherwise, pip installs the newest LangChain packages AutoCimKG supports and upgrades what they need, e.g. openai from v2 to v3 on 18 LTS.
To keep all preinstalled versions instead (16.4 LTS or later), install AutoCimKG w/ the runtime's packages as constraints, so pip picks matching LangChain versions:
```python
from importlib.metadata import distributions
runtime = {d.metadata["Name"].lower(): d.version for d in reversed(list(distributions())) if d.metadata["Name"]}
with open("/Workspace/Users/<user>/runtime-constraints.txt", "w") as f:  # a path all nodes of the cluster can read
    f.writelines(f"{name}=={version}\n" for name, version in runtime.items())
```
```python
%pip install "autocimkg @ git+https://github.com/franzmohr/autocimkg" -c /Workspace/Users/<user>/runtime-constraints.txt
dbutils.library.restartPython()
```
<br/>
<br/>
Some further hints for Databricks:
- The PostgreSQL/Apache AGE database must be reachable from the cluster's network. Keep its password in a secret scope, e.g. ```dbutils.secrets.get("<scope>", "<key>")```.
- Documents in Unity Catalog volumes can be read via their path, e.g. ```PdfReader("/Volumes/<catalog>/<schema>/<volume>/paper.pdf")```.
- AutoCimKG logs to the notebook's output and leaves the runtime's logging configuration untouched.
## LLM Providers
AutoCimKG accepts any [LangChain](https://www.langchain.com/) chat and embeddings model. 
For common providers, ```create_chat_model()``` and ```create_embeddings_model()``` construct suitable models (incl. JSON output mode where supported):
```python
from autocimkg import create_chat_model, create_embeddings_model

# hosted
llm_model = create_chat_model("openai", "gpt-4o")                       # OPENAI_API_KEY
embeddings_model = create_embeddings_model("openai", "text-embedding-3-large")

# local via Ollama
llm_model = create_chat_model("ollama", "qwen3.5:9b", num_ctx=16384)
embeddings_model = create_embeddings_model("ollama", "nomic-embed-text")

# local via LM Studio, vLLM, llama.cpp, LocalAI, ... (OpenAI-compatible API)
llm_model = create_chat_model("openai_compatible", "<model>", base_url="http://localhost:1234/v1")
```
| Provider            | Chat | Embeddings | Package                  | Extra         |
|---------------------|------|------------|--------------------------|---------------|
| `openai`            | yes  | yes        | `langchain-openai`       | (included)    |
| `azure_openai`      | yes  | yes        | `langchain-openai`       | (included)    |
| `openai_compatible` | yes  | yes        | `langchain-openai`       | (included)    |
| `ollama`            | yes  | yes        | `langchain-ollama`       | `ollama`      |
| `anthropic`         | yes  | -          | `langchain-anthropic`    | `anthropic`   |
| `google_genai`      | yes  | yes        | `langchain-google-genai` | `google`      |
| `mistralai`         | yes  | yes        | `langchain-mistralai`    | `mistralai`   |
| `huggingface`       | -    | yes        | `langchain-huggingface`  | `huggingface` |

Packages beyond ```langchain-openai``` are installed via the extra, e.g. ```pip install "autocimkg[anthropic] @ git+https://github.com/franzmohr/autocimkg"```. Further arguments are handed to the respective LangChain class. 
```get_model_config()``` describes a model without API keys, e.g. for storing it via ```MetadataIntegrator.create_llm_config()```.
Note that an existing KG can only be maintained with the embeddings model it was built with, as entity and relationship resolution compares embeddings.
Moreover, smaller local models tend to produce invalid JSON more often, which AutoCimKG answers with retries (see ```max_tries``` parameters).
## Usage
An exemplary utilisation of AutoCimKG is provided in the ```tutorial```.
## Storage Backends
The KG construction itself works on ```KnowledgeGraph``` objects and doesn't depend on a database. 
Storing graphs and metadata is the task of two interchangeable connectors, defined as interfaces: ```BaseGraphIntegrator``` (graphs) and ```BaseMetadataIntegrator``` (metadata repository). 
```GraphIntegrator``` and ```MetadataIntegrator``` implement them for PostgreSQL/Apache AGE. Their database drivers are only imported when these classes are used.
A failed operation (e.g. an unreachable database, reading a graph that doesn't exist or creating a KG version twice) raises a ```StorageError``` for every backend, w/ the driver's original error as its cause:
```python
from autocimkg import StorageError

try:
    kg = graph_integrator.read_graph("kg_v1")
except StorageError as e:
    print(e)  # e.g. "Reading graph 'kg_v1' failed: LookupError: graph doesn't exist"
```
<br/>
<br/>
A further backend (e.g. Delta tables on Databricks) subclasses both interfaces; their docstrings describe what a backend has to preserve. 
The contract tests in 'tests/test_storage.py' check this for every backend listed there. 
They run against PostgreSQL/Apache AGE if ```AUTOCIMKG_TEST_DB_HOST``` (plus ```_PORT```, ```_NAME```, ```_USER``` and ```_PASSWORD```) is set, e.g.:
```bash
AUTOCIMKG_TEST_DB_HOST=localhost AUTOCIMKG_TEST_DB_NAME=<database> AUTOCIMKG_TEST_DB_USER=<user> AUTOCIMKG_TEST_DB_PASSWORD=<password> pytest tests
```
The MCP server (see below) reads PostgreSQL/Apache AGE directly and would need a backend of its own.
## Use in AI Agents (e.g. Microsoft Copilot Studio)
The folder ```mcp_server``` contains a standalone MCP server that exposes stored competency KGs as read-only tools (e.g. finding experts for a topic), which agents in Microsoft Copilot Studio and Microsoft 365 Copilot can call (authenticated via Entra ID or an API key). See its README for setup.
