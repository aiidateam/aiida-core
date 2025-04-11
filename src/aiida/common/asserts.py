###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with asserts that can be used in the codebase."""

from typing import Optional

try:
    from typing import Never
except ImportError:
    # Fallback for Python 3.10 and older
    from typing_extensions import Never


def assert_never(arg: Never, message: Optional[str] = None) -> Never:
    """Assert a part of code that should never be reached.
    This is useful, especially when adding new variables to an enum,
    so to remind the developers to handle the new variable in all the switch cases.
    """

    raise AssertionError('This part of code should never be reached' if not message else message)
