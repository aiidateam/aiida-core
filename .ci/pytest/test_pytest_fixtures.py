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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


def test_aiida_localhost(aiida_localhost):
    """Test aiida_localhost fixture.

    Note: This indirectly also tests that the aiida_profile, tempdir and clean_database fixtures run.
    """
    assert aiida_localhost.label == 'localhost'
