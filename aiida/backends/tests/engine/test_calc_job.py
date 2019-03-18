# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `CalcJob` process sub class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.engine import launch, CalcJob, Process


class TestCalcJob(AiidaTestCase):
    """Test for the `CalcJob` process sub class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestCalcJob, cls).setUpClass(*args, **kwargs)
        cls.code = orm.Code(remote_computer_exec=(cls.computer, '/bin/true')).store()

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
            launch.run_get_pk(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.submit(CalcJob)

    def test_define_not_calling_super(self):
        """A `CalcJob` that does not call super in `define` classmethod should raise."""

        class IncompleteDefineCalcJob(CalcJob):
            """Test class with incomplete define method"""

            @classmethod
            def define(cls, spec):
                pass

            def prepare_for_submission(self, folder):
                pass

        with self.assertRaises(AssertionError):
            launch.run(IncompleteDefineCalcJob)

    def test_invalid_options_type(self):
        """Verify that passing an invalid type to `metadata.options` raises a `TypeError`."""

        class SimpleCalcJob(CalcJob):
            """Simple `CalcJob` implementation"""

            @classmethod
            def define(cls, spec):
                super(SimpleCalcJob, cls).define(spec)

            def prepare_for_submission(self, folder):
                pass

        # The `metadata.options` input expects a plain dict and not a node `Dict`
        with self.assertRaises(TypeError):
            launch.run(SimpleCalcJob, code=self.code, metadata={'options': orm.Dict(dict={'a': 1})})
