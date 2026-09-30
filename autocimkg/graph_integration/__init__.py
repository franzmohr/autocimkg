from .base import BaseGraphIntegrator
__all__ = ["BaseGraphIntegrator", "GraphIntegrator"]


def __getattr__(name: str):
    # storage backends are imported on first use, so each one's drivers are only needed when it is used
    if name == "GraphIntegrator":  # PostgreSQL/Apache AGE
        from .graph_integrator import GraphIntegrator
        globals()[name] = GraphIntegrator
        return GraphIntegrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
