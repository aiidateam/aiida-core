###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.tools.archive` module."""

import logging

import pytest

from aiida.tools.archive import EXPORT_LOGGER, IMPORT_LOGGER


@pytest.fixture(scope='function', autouse=True)
def archive_log_critical_only():
    """Fixture to set the log level to CRITICAL for the archive loggers."""
    export_level = EXPORT_LOGGER.level
    import_level = IMPORT_LOGGER.level
    EXPORT_LOGGER.setLevel(logging.CRITICAL)
    IMPORT_LOGGER.setLevel(logging.CRITICAL)
    yield
    EXPORT_LOGGER.setLevel(export_level)
    IMPORT_LOGGER.setLevel(import_level)


@pytest.fixture(scope='function')
def aiida_localhost_factory(tmp_path):
    """Get or create an AiiDA computer for localhost."""
    from aiida.common.exceptions import NotExistent
    from aiida.orm import Computer

    def _func(label='localhost-test'):
        try:
            computer = Computer.collection.get(label=label)
        except NotExistent:
            computer = Computer(
                label=label,
                description='localhost computer set up by test manager',
                hostname=label,
                workdir=str(tmp_path),
                transport_type='core.local',
                scheduler_type='core.direct',
            )
            computer.store()
            computer.set_minimum_job_poll_interval(0.0)
            computer.configure()

        return computer

    return _func
