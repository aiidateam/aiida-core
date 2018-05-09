# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Bug regression tests for ``verdi help``"""
import unittest

from aiida.cmdline.verdilib import Help, Import
from aiida.utils.capturing import Capturing


class VerdiHelpTest(unittest.TestCase):
    """Make sure fixed bugs stay fixed"""

    def setUp(self):
        super(VerdiHelpTest, self).setUp()
        self.help_cmd = Help()

    def test_verdi_help_full_string(self):
        """
        Prevent regression of bug #700

        ``verdi help`` was printing only the first letter of the docstring of non-click commands
        """
        self.assertFalse(hasattr(Import, '_ctx'), 'This test must use a non-click verdi subcommand')
        fail_msg = 'Has the docstring for ``verdi import`` changed? If not, this is a regression of #700'

        with Capturing() as output:
            try:
                self.help_cmd.run()
            except SystemExit:
                pass

        self.assertIn('  * import        Import nodes and group of nodes', output, fail_msg)
