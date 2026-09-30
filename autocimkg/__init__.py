from .documents_distiller import DocumentsDistiller
from .autocimkg_core import AutoCimKGCore
from .utils import create_chat_model, create_embeddings_model, get_model_config
__all__ = ['DocumentsDistiller', 'GraphIntegrator', 'AutoCimKGCore',
           'create_chat_model', 'create_embeddings_model', 'get_model_config']


def __getattr__(name: str):
    # the PostgreSQL/Apache AGE backend is imported on first use (see graph_integration)
    if name == "GraphIntegrator":
        from .graph_integration import GraphIntegrator
        globals()[name] = GraphIntegrator
        return GraphIntegrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
