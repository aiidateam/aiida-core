# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `SinglefileData` class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import SinglefileData, load_node


class TestSinglefileData(AiidaTestCase):
    """Tests for the `SinglefileData` class."""

    def test_reload_singlefile_data(self):
        """Test writing and reloading a `SinglefileData` instance."""
        content_original = 'some text ABCDE'

        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            filepath = handle.name
            basename = os.path.basename(filepath)
            handle.write(content_original)
            handle.flush()
            node = SinglefileData(file=filepath)

        uuid = node.uuid

        with node.open() as handle:
            content_written = handle.read()

        self.assertEqual(node.list_object_names(), [basename])
        self.assertEqual(content_written, content_original)

        node.store()

        with node.open() as handle:
            content_stored = handle.read()

        self.assertEqual(content_stored, content_original)
        self.assertEqual(node.list_object_names(), [basename])

        node_loaded = load_node(uuid)
        self.assertTrue(isinstance(node_loaded, SinglefileData))

        with node.open() as handle:
            content_loaded = handle.read()

        self.assertEqual(content_loaded, content_original)
        self.assertEqual(node_loaded.list_object_names(), [basename])

        with node_loaded.open() as handle:
            self.assertEqual(handle.read(), content_original)

    def test_construct_from_filelike(self):
        """Test constructing an instance from filelike instead of filepath."""
        content_original = 'some testing text\nwith a newline'

        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            basename = os.path.basename(handle.name)
            handle.write(content_original)
            handle.flush()
            handle.seek(0)
            node = SinglefileData(file=handle)

        with node.open() as handle:
            content_stored = handle.read()

        self.assertEqual(content_stored, content_original)
        self.assertEqual(node.list_object_names(), [basename])

        node.store()

        with node.open() as handle:
            content_stored = handle.read()

        self.assertEqual(content_stored, content_original)
        self.assertEqual(node.list_object_names(), [basename])
