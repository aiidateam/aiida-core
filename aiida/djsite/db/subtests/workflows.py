# -*- coding: utf-8 -*-
"""
Tests for workflows
"""
from django.utils import unittest

from aiida.orm import Workflow
from aiida.djsite.db.testbase import AiidaTestCase
from aiida.workflows.test import WorkflowTestEmpty
 
__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Nicolas Mounet"


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

        self.assertEquals(a.pk,load_workflow(wf_id=a.pk).pk)
        self.assertEquals(a.pk,load_workflow(wf_id=a.uuid).pk)
        self.assertEquals(a.pk,load_workflow(pk=a.pk).pk)
        self.assertEquals(a.pk,load_workflow(uuid=a.uuid).pk)

        with self.assertRaises(ValueError):
            load_workflow(wf_id=a.pk,pk=a.pk)
        with self.assertRaises(ValueError):
            load_workflow(pk=a.pk,uuid=a.uuid)
        with self.assertRaises(ValueError):
            load_workflow(pk=a.uuid)
        with self.assertRaises(NotExistent):
            load_workflow(uuid=a.pk)
        with self.assertRaises(ValueError):
            load_workflow()


