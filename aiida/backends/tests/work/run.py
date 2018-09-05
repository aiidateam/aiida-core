# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase

import aiida.orm
from aiida.orm.data.int import Int
from aiida.orm.data.str import Str
from aiida.work.launch import run, run_get_node
from aiida.work.test_utils import DummyProcess


class TestRun(AiidaTestCase):
    def setUp(self):
        super(TestRun, self).setUp()

    def tearDown(self):
        super(TestRun, self).tearDown()

    def test_run(self):
        inputs = {'a': Int(2), 'b': Str('test')}
        result = run(DummyProcess, **inputs)

    def test_run_get_node(self):
        inputs = {'a': Int(2), 'b': Str('test')}
        result, node = run_get_node(DummyProcess, **inputs)
        self.assertIsInstance(node, aiida.orm.Calculation)
