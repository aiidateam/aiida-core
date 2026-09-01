###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic tests that need the use of the DB."""

from aiida import orm


class TestBool:
    """Test AiiDA Bool class."""

    @staticmethod
    def test_bool_conversion():
        for val in [True, False]:
            assert val == bool(orm.Bool(val))

    @staticmethod
    def test_int_conversion():
        for val in [True, False]:
            assert int(val) == int(orm.Bool(val))
