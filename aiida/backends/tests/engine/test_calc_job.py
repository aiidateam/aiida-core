# -*- coding: utf-8 -*-
"""Test for the `CalcJob` process sub class."""
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.engine import launch, CalcJob, Process


class TestCalcJob(AiidaTestCase):
    """Test for the `CalcJob` process sub class."""

    def setUp(self):
        super(TestCalcJob, self).setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestCalcJob, self).tearDown()
        self.assertIsNone(Process.current())

    def test_run_base_class(self):
        """Verify that it is impossible to run, submit or instantiate a base `CalcJob` class."""
        with self.assertRaises(exceptions.InvalidOperation):
            CalcJob()

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run_get_node(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run_get_pid(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.submit(CalcJob)
