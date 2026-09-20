###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from Plumpy.                         #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The Plumpy license is reproduced in open_source_licenses.txt.         #
###########################################################################

__all__: tuple[str, ...] = ()


class KilledError(Exception):
    """The process was killed."""


class InvalidStateError(Exception):
    """
    Raised when an operation is attempted that requires the process to be in a state
    that is different from the current state
    """


class UnsuccessfulResult:
    """The result of the process was unsuccessful"""

    def __init__(self, result: int | None = None):
        """Initialise.

        :param result: the exit code of the process

        """
        self.result = result


class PersistenceError(Exception):
    """Raised when there is a problem persisting the process"""


class ClosedError(Exception):
    """Raised when an mutable operation is attempted on a closed process"""
