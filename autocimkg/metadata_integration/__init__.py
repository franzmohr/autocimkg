from .base import BaseMetadataIntegrator
__all__ = ["BaseMetadataIntegrator", "MetadataIntegrator"]


def __getattr__(name: str):
    # storage backends are imported on first use, so each one's drivers are only needed when it is used
    if name == "MetadataIntegrator":  # PostgreSQL
        from .metadata_integrator import MetadataIntegrator
        globals()[name] = MetadataIntegrator
        return MetadataIntegrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
