# -*- coding: utf-8 -*-
"""
Tests for workflows
"""

from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.workflows.test import WorkflowTestEmpty

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


class TestWorkflowBasic(AiidaTestCase):
    """
    These tests check the basic features of workflows.
    Now only the load_workflow function is tested.
    """

    def test_load_workflows(self):
        """
        Test for load_node() function.
        """
        from aiida.orm import load_workflow
        from aiida.common.exceptions import NotExistent

        a = WorkflowTestEmpty()
        a.store()

        self.assertEquals(a.pk, load_workflow(wf_id=a.pk).pk)
        self.assertEquals(a.pk, load_workflow(wf_id=a.uuid).pk)
        self.assertEquals(a.pk, load_workflow(pk=a.pk).pk)
        self.assertEquals(a.pk, load_workflow(uuid=a.uuid).pk)

        with self.assertRaises(ValueError):
            load_workflow(wf_id=a.pk, pk=a.pk)
        with self.assertRaises(ValueError):
            load_workflow(pk=a.pk, uuid=a.uuid)
        with self.assertRaises(ValueError):
            load_workflow(pk=a.uuid)
        with self.assertRaises(NotExistent):
            load_workflow(uuid=a.pk)
        with self.assertRaises(ValueError):
            load_workflow()


