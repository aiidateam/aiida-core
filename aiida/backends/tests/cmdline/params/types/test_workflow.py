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
from aiida.cmdline.params.types import LegacyWorkflowParamType


class TestLegacyWorkflowParamType(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        from aiida.workflows.test import WFTestEmpty, WFTestSimpleWithSubWF

        super(TestLegacyWorkflowParamType, cls).setUpClass()

        cls.workflow = WFTestEmpty()
        cls.workflow.label = 'Unique Label'
        cls.workflow.store()
        cls.wf_type = LegacyWorkflowParamType()

    def test_get_by_id(self):
        identifier = str(self.workflow.pk)
        self.assertEqual(self.wf_type.convert(identifier, None, None).uuid, self.workflow.uuid)

    def test_get_by_uuid(self):
        identifier = str(self.workflow.uuid)
        self.assertEqual(self.wf_type.convert(identifier, None, None).uuid, self.workflow.uuid)

    def test_get_by_label(self):
        identifier = str(self.workflow.label)
        self.assertEqual(self.wf_type.convert(identifier, None, None).uuid, self.workflow.uuid)
