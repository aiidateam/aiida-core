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
        """
        Simple test that checks the state of the workflows. We create two
        workflows since the test order in the SQLA was influencing the value
        of aiida.backends.sqlalchemy.models.workflow.DbWorkflow.state which
        should be a Choice object, according to the SQLA doc. Sometimes it
        was automatically converted to unicode.

        Since we are interested to get a unicode from
        aiida.orm.implementation.general.workflow.AbstractWorkflow#get_state
        we enforce this conversion at
        aiida.orm.implementation.sqlalchemy.workflow.Workflow#get_state

        For more info, check issue #951
        """
        # Creating two simple workflows & storing them
        wf1 = WFTestEmpty()
        wf1.store()

        wf2 = WFTestEmpty()
        wf2.store()

        # Checking that the get_state doesn't throw exceptions and that
        # it is a valid state
        self.assertIn(wf1.get_state(), wf_states)
        self.assertIn(wf2.get_state(), wf_states)

    def test_wf_ctime(self):
        import datetime
        import pytz

        # Get the current datetime (before the creation of the workflow)
        dt_before = datetime.datetime.now(pytz.utc)

        # Creating a simple workflow & storing it
        wf = WFTestEmpty()
        wf.store()

        # Get the current datetime (after the creation of the workflow)
        dt_after = datetime.datetime.now(pytz.utc)

        self.assertLessEqual(dt_before, wf.ctime, "The workflow doesn't have"
                                                  "a valid creation time")

        self.assertGreaterEqual(dt_after, wf.ctime, "The workflow doesn't "
                                                    "have a valid creation "
                                                    "time")

    def test_failing_calc_in_wf(self):
        """
        This test checks that a workflow (but also a workflow with
        sub-workflows) that has an exception at one of its steps stops
        properly and it is not left as RUNNING.
        """
        from aiida.daemon.workflowmanager import execute_steps
        from aiida.workflows.test import (FailingWFTestSimple,
                                          FailingWFTestSimpleWithSubWF)

        try:
            # Testing the error propagation of a simple workflow
            wf = FailingWFTestSimple()
            wf.store()
            step_no = 0
            wf.start()
            while wf.is_running():
                execute_steps()
                step_no += 1
                self.assertLess(step_no, 5, "This workflow should have stopped "
                                            "since it is failing")

            # Testing the error propagation of a workflow with subworkflows
            wf = FailingWFTestSimpleWithSubWF()
            wf.store()

            step_no = 0
            wf.start()
            while wf.is_running():
                execute_steps()
                step_no += 1
                self.assertLess(step_no, 5, "This workflow should have stopped "
                                            "since it is failing")
        finally:
            pass

    def test_result_parameter_name_colision(self):
        """
        This test checks that the the workflow parameters and results do not
        collide. This was a problem in SQLA (Issue #960) but a test for both
        backends is added (for completeness).
        """
        # Creating a simple workflow & storing it
        wf = WFTestEmpty()
        wf.store()

        # Set some parameters
        params = {'band_calculation_set': 2,
                  'codename': 'pw-5.2.0',
                  'pseudo_family': 'SSSP_v0.7_eff_PBE'}
        wf.set_params(params)

        # Add some results that their names collide with the parameter names
        wf.add_result('structure', 'test_string_1')
        wf.add_result('codename', 'test_string_2')

        # Check that we have the correct results
        self.assertDictEqual(
            {'structure': 'test_string_1', 'codename': 'test_string_2'},
            wf.get_results(), "The workflow results are not the expected "
                              "ones.")

        # Check that we have the correct parameters
        self.assertDictEqual(params, wf.get_parameters(),
                             "The workflow parameters are not the expected "
                             "ones.")

    def tearDown(self):
        """
        Cleaning the database after each test. Since I don't
        want the workflows of one test to interfere with the
        workflows of the other tests.
        """
        self._class_was_setup = True
        self.clean_db()
        self.insert_data()
