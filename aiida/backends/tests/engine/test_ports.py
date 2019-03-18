# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for process spec ports."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.engine.processes.ports import InputPort, PortNamespace


class TestInputPort(AiidaTestCase):
    """Tests for the `InputPort` class."""

    def test_with_non_db(self):
        """Test the functionality of the `non_db` attribute upon construction and setting."""

        # When not specifying, it should get the default value and `non_db_explicitly_set` should be `False`
        port = InputPort('port')
        self.assertEqual(port.non_db, False)
        self.assertEqual(port.non_db_explicitly_set, False)

        # Using the setter to change the value should toggle both properties
        port.non_db = True
        self.assertEqual(port.non_db, True)
        self.assertEqual(port.non_db_explicitly_set, True)

        # Explicitly setting to `False` upon construction
        port = InputPort('port', non_db=False)
        self.assertEqual(port.non_db, False)
        self.assertEqual(port.non_db_explicitly_set, True)

        # Explicitly setting to `True` upon construction
        port = InputPort('port', non_db=True)
        self.assertEqual(port.non_db, True)
        self.assertEqual(port.non_db_explicitly_set, True)


class TestPortNamespace(AiidaTestCase):
    """Tests for the `PortNamespace` class."""

    def test_with_non_db(self):
        """Ports inserted to a `PortNamespace` should inherit the `non_db` attribute if not explicitly set."""
        namespace_non_db = True
        port_namespace = PortNamespace('namespace', non_db=namespace_non_db)

        # When explicitly set upon port construction, value should not be inherited even when different
        port = InputPort('storable', non_db=False)
        port_namespace['storable'] = port
        self.assertEqual(port.non_db, False)

        port = InputPort('not_storable', non_db=True)
        port_namespace['not_storable'] = port
        self.assertEqual(port.non_db, True)

        # If not explicitly defined, it should inherit from parent namespace
        port = InputPort('not_storable')
        port_namespace['not_storable'] = port
        self.assertEqual(port.non_db, namespace_non_db)
