# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `CalcJobNode` node sub class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.common import LinkType
from aiida.orm import CalcJobNode, FolderData


class TestCalcJobNode(AiidaTestCase):
    """Tests for the `CalcJobNode` node sub class."""

    def test_get_scheduler_stdout(self):
        """Verify that the repository sandbox folder is cleaned after the node instance is garbage collected."""
        option_key = 'scheduler_stdout'
        option_value = '_scheduler-output.txt'
        stdout = 'some\nstandard output'

        node = CalcJobNode(computer=self.computer,)
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        retrieved = FolderData()

        # No scheduler output filename option so should return `None`
        self.assertEqual(node.get_scheduler_stdout(), None)

        # No retrieved folder so should return `None`
        node.set_option(option_key, option_value)
        self.assertEqual(node.get_scheduler_stdout(), None)

        # Now it has retrieved folder, but file does not actually exist in it, should not except but return `None
        node.store()
        retrieved.store()
        retrieved.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')
        self.assertEqual(node.get_scheduler_stdout(), None)

        # Add the file to the retrieved folder
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(stdout)
            handle.flush()
            handle.seek(0)
            retrieved.put_object_from_filelike(handle, option_value, force=True)
        self.assertEqual(node.get_scheduler_stdout(), stdout)

    def test_get_scheduler_stderr(self):
        """Verify that the repository sandbox folder is cleaned after the node instance is garbage collected."""
        option_key = 'scheduler_stderr'
        option_value = '_scheduler-error.txt'
        stderr = 'some\nstandard error'

        node = CalcJobNode(computer=self.computer,)
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        retrieved = FolderData()

        # No scheduler error filename option so should return `None`
        self.assertEqual(node.get_scheduler_stderr(), None)

        # No retrieved folder so should return `None`
        node.set_option(option_key, option_value)
        self.assertEqual(node.get_scheduler_stderr(), None)

        # Now it has retrieved folder, but file does not actually exist in it, should not except but return `None
        node.store()
        retrieved.store()
        retrieved.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')
        self.assertEqual(node.get_scheduler_stderr(), None)

        # Add the file to the retrieved folder
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(stderr)
            handle.flush()
            handle.seek(0)
            retrieved.put_object_from_filelike(handle, option_value, force=True)
        self.assertEqual(node.get_scheduler_stderr(), stderr)
