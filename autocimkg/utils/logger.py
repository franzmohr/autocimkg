import logging
import sys

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_logger(name: str = "autocimkg") -> logging.Logger:
    """
    Returns the stdout logger shared by AutoCimKG's components.
    A stdout handler added before (e.g. when a notebook cell is re-run) is replaced, so each message is printed once.
    NOTE: the logging module itself is left untouched, as reloading it would reset the logging configuration of
    the whole process (e.g. the one of a Databricks or Jupyter notebook)!

    :param name: Logger name
    :returns: Logger w/ exactly one stdout handler
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # don't repeat messages via handlers of the root logger (e.g. in Databricks)

    for handler in [handler for handler in logger.handlers if getattr(handler, "autocimkg_stdout", False)]:
        logger.removeHandler(handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    console_handler.setLevel(logging.DEBUG)
    console_handler.autocimkg_stdout = True
    logger.addHandler(console_handler)

    return logger
