# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Methods to validate the database integrity and fix violations."""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

WARNING_BORDER = '*' * 120


def write_database_integrity_violation(results, headers, reason_message, action_message=None):
    """Emit a integrity violation warning and write the violating records to a log file in the current directory

    :param results: a list of tuples representing the violating records
    :param headers: a tuple of strings that will be used as a header for the log file. Should have the same length
        as each tuple in the results list.
    :param reason_message: a human readable message detailing the reason of the integrity violation
    :param action_message: an optional human readable message detailing a performed action, if any
    """
    # pylint: disable=duplicate-string-formatting-argument
    from datetime import datetime
    from tabulate import tabulate
    from tempfile import NamedTemporaryFile

    from aiida import settings
    from aiida.cmdline.utils import echo

    if settings.TESTING_MODE:
        return

    if action_message is None:
        action_message = 'nothing'

    with NamedTemporaryFile(prefix='migration-', suffix='.log', dir='.', delete=False, mode='w+') as handle:
        echo.echo('')
        echo.echo_warning(
            '\n{}\nFound one or multiple records that violate the integrity of the database\nViolation reason: {}\n'
            'Performed action: {}\nViolators written to: {}\n{}\n'.format(WARNING_BORDER, reason_message,
                                                                          action_message, handle.name, WARNING_BORDER))

        handle.write('# {}\n'.format(datetime.utcnow().isoformat()))
        handle.write('# Violation reason: {}\n'.format(reason_message))
        handle.write('# Performed action: {}\n'.format(action_message))
        handle.write('\n')
        handle.write(tabulate(results, headers))
