"""
Tests of the construction log that build_graph() records (AutoCimKGCore.log).
"""
import logging

from autocimkg import AutoCimKGCore


def test_multi_line_messages_are_kept_in_one_entry():
    # a retried LLM call logs a traceback and a failed parse logs the document text: both span several lines
    core = AutoCimKGCore(llm_model=None, embeddings_model=None)
    buffer, handler = core._AutoCimKGCore__init_logger()
    try:
        core.logger.info("Entity (x:Y) created")
        try:
            raise ValueError("Invalid json output")
        except ValueError:
            core.logger.exception("Error occurred. Retrying (%s/%s) ...", 1, 5)
        core.logger.warning("Error in parsing the instance: %s", "page 1\n\npage 2 autocimkg: ...")
        logs = core._AutoCimKGCore__read_logging_buffer(buffer)
    finally:
        core._AutoCimKGCore__destroy_logger(buffer, handler)

    assert [(log.log_level, log.message.split("\n")[0]) for log in logs] == [
        ("INFO", "Entity (x:Y) created"),
        ("ERROR", "Error occurred. Retrying (1/5) ..."),
        ("WARNING", "Error in parsing the instance: page 1"),
    ]
    assert logs[1].message.endswith("ValueError: Invalid json output")
    assert logs[2].message == "Error in parsing the instance: page 1\n\npage 2 autocimkg: ..."
    assert all(log.logger_name == "autocimkg" and log.ts is not None for log in logs)


def test_buffered_handler_is_removed():
    core = AutoCimKGCore(llm_model=None, embeddings_model=None)
    buffer, handler = core._AutoCimKGCore__init_logger()
    core._AutoCimKGCore__destroy_logger(buffer, handler)
    assert handler not in logging.getLogger("autocimkg").handlers
