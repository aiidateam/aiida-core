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
