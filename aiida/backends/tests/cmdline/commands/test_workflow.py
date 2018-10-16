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
from click.testing import CliRunner
from traceback import format_exception

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_workflow import workflow_list, workflow_kill, workflow_report, workflow_logshow, \
    format_pk


def debug_msg(result):
    return ''.join(format_exception(*result.exc_info))


def format_pk(workflow):
    return '(pk: {})'.format(workflow.pk)


def format_wf_for_list(workflow):
    return '{} {}'.format(workflow.__class__.__name__, format_pk(workflow))


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
        self.assertIsNone(result.exception, msg=debug_msg(result))
        self.assertIn(format_wf_for_list(self.workflow), result.output)
        self.assertIn(format_wf_for_list(self.other_workflow), result.output)
        self.assertNotIn(format_wf_for_list(self.done_workflow), result.output)

    def test_workflow_list_workflows(self):
        result = self.runner.invoke(workflow_list, ['--workflows={}'.format(self.workflow.pk)])
        self.assertIsNone(result.exception, msg=debug_msg(result))
        self.assertIn(format_wf_for_list(self.workflow), result.output)
        self.assertNotIn(format_wf_for_list(self.other_workflow), result.output)
        self.assertNotIn(format_wf_for_list(self.done_workflow), result.output)

    def test_workflow_list_states(self):
        result = self.runner.invoke(workflow_list, ['--all-states'])
        self.assertIsNone(result.exception, msg=debug_msg(result))
        self.assertIn(format_wf_for_list(self.workflow), result.output)
        self.assertIn(format_wf_for_list(self.other_workflow), result.output)
        self.assertIn(format_wf_for_list(self.done_workflow), result.output)

    def test_workflow_list_depth(self):
        results = []
        results.append(self.runner.invoke(workflow_list, ['--depth=0']))
        results.append(self.runner.invoke(workflow_list, ['--depth=1']))
        results.append(self.runner.invoke(workflow_list, ['--depth=2']))

        for result in results:
            self.assertIsNone(result.exception, msg=debug_msg(result))

        self.assertTrue(len(results[0].output) < len(results[1].output))
        self.assertTrue(len(results[1].output) < len(results[2].output))

    def test_workflow_report(self):
        result = self.runner.invoke(workflow_report, [str(self.super_workflow.uuid)])
        self.assertIsNone(result.exception, msg=debug_msg(result))
        self.assertIn(format_pk(self.super_workflow), result.output)

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
        self.assertIsNone(result.exception, msg=debug_msg(result))
        self.assertIn(format_pk(self.super_workflow), result.output)
