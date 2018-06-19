import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.workflow import workflow_list, workflow_kill, workflow_report, workflow_logshow


class TestVerdiLegacyWorkflow(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        from aiida.workflows.test import WFTestEmpty, WFTestSimpleWithSubWF

        super(TestVerdiLegacyWorkflow, cls).setUpClass()
        cls.runner = CliRunner()

        cls.workflow = WFTestEmpty()
        cls.workflow.store()
        cls.other_workflow = WFTestEmpty()
        cls.other_workflow.store()
        cls.done_workflow = WFTestEmpty()
        cls.done_workflow.store()
        cls.done_workflow.set_state('FINISHED')
        cls.super_workflow = WFTestSimpleWithSubWF()
        cls.super_workflow.store()
        cls.super_workflow.start()

    def test_workflow_list_default(self):
        result = self.runner.invoke(workflow_list, [])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.workflow.pk), result.output)
        self.assertIn(str(self.other_workflow.pk), result.output)
        self.assertNotIn(str(self.done_workflow.pk), result.output)

    def test_workflow_list_workflows(self):
        result = self.runner.invoke(workflow_list, ['--workflows={}'.format(self.workflow.pk)])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.workflow.pk), result.output)
        self.assertNotIn(str(self.other_workflow.pk), result.output)
        self.assertNotIn(str(self.done_workflow.pk), result.output)

    def test_workflow_list_states(self):
        result = self.runner.invoke(workflow_list, ['--all-states'])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.workflow.pk), result.output)
        self.assertIn(str(self.other_workflow.pk), result.output)
        self.assertIn(str(self.done_workflow.pk), result.output)

    def test_workflow_list_depth(self):
        results = []
        results.append(self.runner.invoke(workflow_list, ['--depth=0']))
        results.append(self.runner.invoke(workflow_list, ['--depth=1']))
        results.append(self.runner.invoke(workflow_list, ['--depth=2']))

        for result in results:
            self.assertIsNone(result.exception)

        self.assertTrue(len(results[0].output) < len(results[1].output))
        self.assertTrue(len(results[1].output) < len(results[2].output))

    def test_workflow_report(self):
        result = self.runner.invoke(workflow_report, [str(self.super_workflow.uuid)])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.super_workflow.pk), result.output)

    def test_workflow_kill(self):
        from aiida.workflows.test import WFTestEmpty
        running_workflow = WFTestEmpty()
        running_workflow.store()
        result = self.runner.invoke(workflow_kill, [str(running_workflow.uuid)], input='y\n')
        self.assertIsNone(result.exception)
        self.assertNotIn('WorkflowKillError', result.output)
        self.assertNotIn('WorkflowUnkillable', result.output)
        self.assertEqual(running_workflow.get_state(), 'FINISHED')

        self.assertEqual(self.done_workflow.get_state(), 'FINISHED')
        result = self.runner.invoke(workflow_kill, [str(self.done_workflow.pk)], input='y\n')
        self.assertIsNone(result.exception)
        self.assertIn('WorkflowUnkillable', result.output)
        self.assertEqual(self.done_workflow.get_state(), 'FINISHED')

    def test_workflow_logshow(self):
        result = self.runner.invoke(workflow_logshow, [str(self.super_workflow.pk)])
        self.assertIsNone(result.exception)
        self.assertIn(str(self.super_workflow.pk), result.output)

