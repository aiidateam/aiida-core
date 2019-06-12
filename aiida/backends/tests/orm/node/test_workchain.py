# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `WorkChainNode` node sub class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.orm import WorkChainNode


class TestWorkChainNode(AiidaTestCase):
    """Tests for the `WorkChainNode` node sub class."""

    def test_errors_handled(self):
        """Test the property `errors_handled` and the attribute `add_error_handler`."""
        errors = ['handle_unconverged', 'handle_out_of_walltime']
        node = WorkChainNode().store()

        # If the attribute does not exist, the property should
        self.assertEqual(node.errors_handled, None)

        node.add_error_handled(errors[0])
        self.assertEqual(node.errors_handled, [errors[0]])

        node.add_error_handled(errors[1])
        self.assertEqual(node.errors_handled, errors)

        # After sealing, retrieving should still work, but `add_error_handler` should raise
        node.seal()
        self.assertEqual(node.errors_handled, errors)

        with self.assertRaises(exceptions.ModificationNotAllowed):
            node.add_error_handled(errors[1])
