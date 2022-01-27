# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Test pytest fixtures.
"""


def test_aiida_localhost(aiida_localhost):
    """Test aiida_localhost fixture.

    Note: This indirectly also tests that the aiida_profile, temp_dir and clean_database fixtures run.
    """
    assert aiida_localhost.label == 'localhost-test'


def test_aiida_local_code(aiida_local_code_factory):
    """Test aiida_local_code_factory fixture.
    """
    code = aiida_local_code_factory(entry_point='core.templatereplacer', executable='diff')
    assert code.computer.label == 'localhost-test'
