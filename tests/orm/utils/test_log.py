###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.utils.log` module."""

import logging

from aiida.orm.utils import log as log_module


def test_db_log_handler_emit_when_finalizing(monkeypatch):
    """Test ``DBLogHandler.emit`` does not import the ORM during Python finalization."""
    handler = log_module.DBLogHandler()
    record = logging.LogRecord('name', logging.INFO, 'pathname', 0, 'message', (), None)
    monkeypatch.setattr('sys.is_finalizing', lambda: True)
    monkeypatch.setattr(log_module, 'sys', None)

    handler.emit(record)
