# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :class:`aiida.storage.sqlite_temp.backend.SqliteTempBackend` while running processes."""
from aiida.engine import calcfunction
from aiida.manage import get_profile, load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend


@calcfunction
def add(x, y):
    """Sum two integers."""
    return x + y


def test_calcfunction(aiida_instance, aiida_profile):
    """Test running a calcfunction."""
    try:
        profile = SqliteTempBackend.create_profile(debug=False)
        aiida_instance.add_profile(profile)
        aiida_instance.store()
        load_profile(profile, allow_switch=True)

        assert get_profile() == profile

        result, node = add.run_get_node(1, 2)
        assert node.is_finished_ok
        assert result == 3

    finally:
        try:
            aiida_instance.remove_profile(profile)
            aiida_instance.store()
        except Exception:  # pylint: disable=broad-except
            pass
        load_profile(aiida_profile, allow_switch=True)
