import logging


class StorageError(Exception):
    """
    Raised by storage backends (see BaseGraphIntegrator and BaseMetadataIntegrator) when an operation fails,
    e.g. because the database is unreachable or rejects a query. The backend's original error is its __cause__.
    """


def storage_error(logger: logging.Logger, operation: str, error: Exception) -> StorageError:
    """
    Logs a failed storage operation and returns the StorageError to raise.

    :param logger: Logger of the storage backend
    :param operation: Description of the failed operation (e.g. "Reading graph 'kg_v1'")
    :param error: Error raised by the database driver (a StorageError is passed on unchanged)
    :returns: StorageError w/ the original error as cause
    """

    if isinstance(error, StorageError):
        return error
    message = f"{operation} failed: {type(error).__name__}: {str(error).strip()}"
    logger.error(message)
    storage_error_ = StorageError(message)
    storage_error_.__cause__ = error
    return storage_error_
