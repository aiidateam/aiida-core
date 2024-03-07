###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.orm.users`."""
from aiida.orm.users import User


def test_user_is_default(default_user):
    """Test the :meth:`aiida.orm.users.User.is_default` property."""
    assert default_user.is_default
    user = User('other@localhost').store()
    assert not user.is_default
