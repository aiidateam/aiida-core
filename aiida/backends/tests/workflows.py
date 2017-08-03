# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.utils import get_workflow_list
from aiida.common.datastructures import wf_states
from aiida.orm import User
from aiida.workflows.test import WFTestEmpty
from aiida.orm.implementation import get_workflow_info
from aiida.workflows.test import WFTestSimpleWithSubWF


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

        a = WFTestEmpty()
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
        with self.assertRaises(ValueError):
            load_workflow(uuid=a.pk)
        with self.assertRaises(ValueError):
            load_workflow()

    def test_listing_workflows(self):
        """
        Test ensuring that the workflow listing works as expected.
        (Listing initialized & running workflows and not listing finished
        workflows or workflows with errors).
        """
        # Assuming there is only one user
        dbuser = User.search_for_users(email=self.user_email)[0]
        # Creating a workflow & storing it
        a = WFTestEmpty()
        a.store()

        # Setting manually the state to RUNNING.
        a.set_state(wf_states.RUNNING)

        # Getting all the available workflows of the current user
        # and checking if we got the right one.
        wfqs = get_workflow_list(all_states=True, user=dbuser)
        self.assertTrue(len(wfqs) == 1, "We expect one workflow")
        a_prime = wfqs[0].get_aiida_class()
        self.assertEqual(a.uuid, a_prime.uuid, "The uuid is not the expected "
                                               "one")

        # We ask all the running workflows. We should get one workflow.
        wfqs = get_workflow_list(all_states=True, user=dbuser)
        self.assertTrue(len(wfqs) == 1, "We expect one workflow")
        a_prime = wfqs[0].get_aiida_class()
        self.assertEqual(a.uuid, a_prime.uuid, "The uuid is not the expected "
                                               "one")

        # We change the state of the workflow to FINISHED.
        a.set_state(wf_states.FINISHED)

        # Getting all the available workflows of the current user
        # and checking if we got the right one.
        wfqs = get_workflow_list(all_states=True, user=dbuser)
        self.assertTrue(len(wfqs) == 1, "We expect one workflow")
        a_prime = wfqs[0].get_aiida_class()
        self.assertEqual(a.uuid, a_prime.uuid, "The uuid is not the expected "
                                               "one")

        # We ask all the running workflows. We should get zero results.
        wfqs = get_workflow_list(all_states=False, user=dbuser)
        self.assertTrue(len(wfqs) == 0, "We expect zero workflows")

        # We change the state of the workflow to INITIALIZED.
        a.set_state(wf_states.INITIALIZED)

        # We ask all the running workflows. We should get one workflow.
        wfqs = get_workflow_list(all_states=True, user=dbuser)
        self.assertTrue(len(wfqs) == 1, "We expect one workflow")
        a_prime = wfqs[0].get_aiida_class()
        self.assertEqual(a.uuid, a_prime.uuid, "The uuid is not the expected "
                                               "one")

        # We change the state of the workflow to ERROR.
        a.set_state(wf_states.ERROR)

        # We ask all the running workflows. We should get zero results.
        wfqs = get_workflow_list(all_states=False, user=dbuser)
        self.assertTrue(len(wfqs) == 0, "We expect zero workflows")

    def test_workflow_info(self):
        """
        This test checks that the workflow info is generate without any
        exceptions
        :return:
        """
        # Assuming there is only one user
        dbuser = User.search_for_users(email=self.user_email)[0]

        # Creating a simple workflow & storing it
        a = WFTestEmpty()
        a.store()

        # Emulate the workflow list
        for w in get_workflow_list(all_states=True, user=dbuser):
            if not w.is_subworkflow():
                get_workflow_info(w)

        # Create a workflow with sub-workflows and store it
        b = WFTestSimpleWithSubWF()
        b.store()

        # Emulate the workflow list
        for w in get_workflow_list(all_states=True, user=dbuser):
            if not w.is_subworkflow():
                get_workflow_info(w)

        # Start the first workflow and perform a workflow list
        b.start()
        for w in get_workflow_list(all_states=True, user=dbuser):
            if not w.is_subworkflow():
                get_workflow_info(w)

    def test_wf_get_state(self):
        # Creating a simple workflow & storing it
        wf = WFTestEmpty()
        wf.store()

        # Checking that the get_state doesn't throw exceptions and that
        # it is a valid state
        self.assertIn(wf.get_state(), wf_states)


    def tearDown(self):
        """
        Cleaning the database after each test. Since I don't
        want the workflows of one test to interfere with the
        workflows of the other tests.
        """
        self._class_was_setup = True
        self.clean_db()
        self.insert_data()
