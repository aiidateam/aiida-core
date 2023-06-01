# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.cmdline.utils.log` module."""
import logging

from aiida.cmdline.utils import log


def test_cli_formatter():
    """Test the ``CliFormatter.format`` method for a plain message.

    Note that if it contains percentage signs but no arguments, it should not try to convert it.
    """
    message = 'message'
    record = logging.LogRecord('name', logging.INFO, 'pathname', 0, message, (), None)
    assert log.CliFormatter().format(record) == message


def test_cli_formatter_no_args():
    """Test the ``CliFormatter.format`` method for a message with percentage signs but no args."""
    message = 'PID    MEM %    CPU %  started'
    record = logging.LogRecord('name', logging.INFO, 'pathname', 0, message, (), None)
    assert log.CliFormatter().format(record) == message


def test_cli_formatter_named_parameters():
    """Test the ``CliFormatter.format`` method for a message with named parameters but no args.

    This can occur for example when logging prepared SQL queries. These contain named parameters, but are not actually
    intended to be filled with arguments passed to the logging call but are supposed to be kept as is. When no arguments
    are passed in the log record, this should not except.
    """
    message = 'SELECT t.pk FROM t WHERE t.pk = %(pk_1)s'
    record = logging.LogRecord('name', logging.INFO, 'pathname', 0, message, (), None)
    assert log.CliFormatter().format(record) == message


def test_cli_formatter_args():
    """Test the ``CliFormatter.format`` method for a message with a single argument."""
    record = logging.LogRecord('name', logging.INFO, 'pathname', 0, 'Some %s', ('value',), None)
    assert log.CliFormatter().format(record) == 'Some value'


def test_cli_formatter_prefix():
    """Test the ``CliFormatter.format`` method for a message with a single argument."""
    record = logging.LogRecord('name', logging.INFO, 'pathname', 0, 'Some %s', ('value',), None)
    record.prefix = True
    assert log.CliFormatter().format(record) == '\x1b[34m\x1b[1mInfo\x1b[0m: Some value'
