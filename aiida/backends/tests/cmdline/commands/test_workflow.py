import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.workflow import workflow_list, workflow_kill, workflow_report, workflow_logshow


class TestVerdiLegacyWorkflow(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        from aiida.workflows.test import WFTestEmpty

        super(TestVerdiLegacyWorkflow, cls).setUpClass()
        cls.runner = CliRunner()

        cls.workflow = WFTestEmpty()
        cls.workflow.store()
        cls.other_workflow = WFTestEmpty()
        cls.other_workflow.store()

    def test_workflow_list_default(self):
        result = self.runner.invoke(workflow_list, [])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.workflow.pk), result.output)
        self.assertIn(str(self.other_workflow.pk), result.output)

    def test_workflow_list_workflows(self):
        result = self.runner.invoke(workflow_list, ['--workflows={}'.format(self.workflow.pk)])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.workflow.pk), result.output)
        self.assertNotIn(str(self.other_workflow.pk), result.output)
