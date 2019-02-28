# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `CalcJob` utils."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm import Dict, CalcJobNode
from aiida.orm.utils.calcjob import CalcJobResultManager
from aiida.plugins import CalculationFactory
from aiida.plugins.entry_point import get_entry_point_string_from_class


class TestCalcJobResultManager(AiidaTestCase):
    """Tests for the `CalcJobResultManager` utility class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Define a useful CalcJobNode to test the CalcJobResultManager.

        We emulate a node for the `TemplateReplacer` calculation job class. To do this we have to make sure the
        process type is set correctly and an output parameter node is created.
        """
        super(TestCalcJobResultManager, cls).setUpClass(*args, **kwargs)
        cls.process_class = CalculationFactory('templatereplacer')
        cls.process_type = get_entry_point_string_from_class(cls.process_class.__module__, cls.process_class.__name__)
        cls.node = CalcJobNode(computer=cls.computer, process_type=cls.process_type)
        cls.node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        cls.node.store()

        cls.key_one = 'key_one'
        cls.key_two = 'key_two'
        cls.val_one = 'val_one'
        cls.val_two = 'val_two'
        cls.keys = [cls.key_one, cls.key_two]

        cls.result_node = Dict(dict={
            cls.key_one: cls.val_one,
            cls.key_two: cls.val_two,
        }).store()

        cls.result_node.add_incoming(cls.node, LinkType.CREATE, cls.process_class.spec().default_output_node)

    def test_no_process_type(self):
        """`get_results` should raise `ValueError` if `CalcJobNode` has no `process_type`"""
        node = CalcJobNode(computer=self.computer)
        manager = CalcJobResultManager(node)

        with self.assertRaises(ValueError):
            manager.get_results()

    def test_invalid_process_type(self):
        """`get_results` should raise `ValueError` if `CalcJobNode` has invalid `process_type`"""
        node = CalcJobNode(computer=self.computer, process_type='aiida.calculations:not_existent')
        manager = CalcJobResultManager(node)

        with self.assertRaises(ValueError):
            manager.get_results()

    def test_process_class_no_default_node(self):
        """`get_results` should raise `ValueError` if process class does not define default output node."""
        # This is a valid process class however ArithmeticAddCalculation does define a default output node
        process_class = CalculationFactory('arithmetic.add')
        process_type = get_entry_point_string_from_class(process_class.__module__, process_class.__name__)
        node = CalcJobNode(computer=self.computer, process_type=process_type)

        manager = CalcJobResultManager(node)

        with self.assertRaises(ValueError):
            manager.get_results()

    def test_iterator(self):
        """Test that the manager can be iterated over."""
        manager = CalcJobResultManager(self.node)
        for key in manager:
            self.assertIn(key, self.keys)

    def test_getitem(self):
        """Test that the manager support getitem operator."""
        manager = CalcJobResultManager(self.node)
        self.assertEqual(manager[self.key_one], self.val_one)

    def test_getattr(self):
        """Test that the manager support getattr operator."""
        manager = CalcJobResultManager(self.node)
        self.assertEqual(getattr(manager, self.key_one), self.val_one)
