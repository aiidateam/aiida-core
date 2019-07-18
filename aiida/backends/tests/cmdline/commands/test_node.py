# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for verdi node"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_node


class TestVerdiNode(AiidaTestCase):
    """Tests for `verdi node`"""

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_node_tree(self):
        """Test `verdi node tree`"""
        node = orm.Data().store()
        options = [str(node.pk)]
        result = self.cli_runner.invoke(cmd_node.tree, options)
        self.assertClickResultNoException(result)
