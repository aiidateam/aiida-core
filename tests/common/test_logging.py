###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.log` module."""

import logging

from aiida.common.log import capture_logging


def test_logging_before_dbhandler_loaded(caplog):
    """Test that logging still works even if no database is loaded.

    When a profile is loaded, the ``DbLogHandler`` logging handler is configured that redirects log messages to the
    database. This should not break the logging functionality when no database has been loaded yet.
    """
    msg = 'Testing a critical message'
    logger = logging.getLogger()
    logging.getLogger().critical(msg)
    assert caplog.record_tuples == [(logger.name, logging.CRITICAL, msg)]


def test_log_report(caplog):
    """Test that the ``logging`` module is patched such that the ``Logger`` class has the ``report`` method.

    The ``report`` method corresponds to a call to the :meth:``Logger.log`` method where the log level used is the
    :data:`aiida.common.log.LOG_LEVEL_REPORT`.
    """
    msg = 'Testing a report message'
    logger = logging.getLogger()

    with caplog.at_level(logging.REPORT):
        logger.report(msg)

    assert caplog.record_tuples == [(logger.name, logging.REPORT, msg)]


def test_capture_logging():
    """Test the :func:`aiida.common.log.capture_logging` function."""
    logger = logging.getLogger()
    message = 'Some message'
    with capture_logging(logger) as stream:
        logging.getLogger().error(message)
        assert stream.getvalue().strip() == message


def test_get_process_logger_no_process():
    """Test that :func:`aiida.common.log.get_process_logger` returns ``None`` when not in a process context."""
    from aiida.common.log import get_process_logger

    logger = get_process_logger()
    assert logger is None
