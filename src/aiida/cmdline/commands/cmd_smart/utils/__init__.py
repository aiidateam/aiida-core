###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The utils for `verdi smart` command line interface."""

from pathlib import Path

VERDI_CLI_MAP = Path(__file__).resolve().parent / 'verdi_cli.json'

__all__ = ['VERDI_CLI_MAP']
