# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data structures for mapping legacy `JobCalculation` data to new process attributes."""
from collections import namedtuple

StateMapping = namedtuple('StateMapping', ['state', 'process_state', 'exit_status', 'process_status'])

# Mapping of old `state` attribute values of legacy `JobCalculation` to new process related attributes.
# This is used in migration `0038_data_migration_legacy_job_calculations.py`
STATUS_TEMPLATE = 'Legacy `JobCalculation` with state `{}`'
STATE_MAPPING = {
    'NEW': StateMapping('NEW', 'killed', None, STATUS_TEMPLATE.format('NEW')),
    'TOSUBMIT': StateMapping('TOSUBMIT', 'killed', None, STATUS_TEMPLATE.format('TOSUBMIT')),
    'SUBMITTING': StateMapping('SUBMITTING', 'killed', None, STATUS_TEMPLATE.format('SUBMITTING')),
    'WITHSCHEDULER': StateMapping('WITHSCHEDULER', 'killed', None, STATUS_TEMPLATE.format('WITHSCHEDULER')),
    'COMPUTED': StateMapping('COMPUTED', 'killed', None, STATUS_TEMPLATE.format('COMPUTED')),
    'RETRIEVING': StateMapping('RETRIEVING', 'killed', None, STATUS_TEMPLATE.format('RETRIEVING')),
    'PARSING': StateMapping('PARSING', 'killed', None, STATUS_TEMPLATE.format('PARSING')),
    'SUBMISSIONFAILED': StateMapping('SUBMISSIONFAILED', 'excepted', None, STATUS_TEMPLATE.format('SUBMISSIONFAILED')),
    'RETRIEVALFAILED': StateMapping('RETRIEVALFAILED', 'excepted', None, STATUS_TEMPLATE.format('RETRIEVALFAILED')),
    'PARSINGFAILED': StateMapping('PARSINGFAILED', 'excepted', None, STATUS_TEMPLATE.format('PARSINGFAILED')),
    'FAILED': StateMapping('FAILED', 'finished', 2, None),
    'FINISHED': StateMapping('FINISHED', 'finished', 0, None),
}
