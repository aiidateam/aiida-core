# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import range

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.utils import get_workflow_list
from aiida.common.datastructures import wf_states
from aiida.daemon.runner import legacy_workflow_stepper
from aiida.orm.implementation import get_all_running_steps
from aiida.workflows.test import WFTestSimpleWithSubWF


class TestDaemonBasic(AiidaTestCase):

    def test_workflow_fast_kill(self):
        from aiida.cmdline.commands.workflow import Workflow as WfCmd
        from aiida.orm.backends import construct_backend

        backend = construct_backend()

        params = dict()
        params['nmachine'] = 2

        # Create a workflow with 2 subworkflows and start it
        head_wf = WFTestSimpleWithSubWF()
        head_wf.start()

        # Get the user
        user = backend.users.find(email=self.user_email)[0]
        wfl = get_workflow_list(user=user)
        running_no = 0
        for w in get_workflow_list(user=user, all_states=True):
            if w.get_aiida_class().get_state() == wf_states.RUNNING:
                running_no += 1
        self.assertEquals(running_no, 3)

        # Killing the head workflow
        wf_cmd = WfCmd()
        wf_cmd.workflow_kill(*[str(head_wf.pk), '-f', '-q'])

        # At this point no running workflow should be found
        running_no = 0
        for w in get_workflow_list(user=user, all_states=True):
            if w.get_aiida_class().get_state() == wf_states.RUNNING:
                running_no += 1
        self.assertEquals(running_no, 0,
                          "No running workflows should be found")

        self.assertNotEquals(get_all_running_steps(), 0,
                             "At this point there will be running steps.")

        # Making the daemon to advance. This will automatically set
        # to FINISHED all the running steps that are (directly) under
        # a finished workflow
        legacy_workflow_stepper()

        self.assertEquals(len(list(get_all_running_steps())), 0,
                          "At this point there should be no running steps.")
        running_no = 0
        for w in get_workflow_list(user=user, all_states=True):
            if w.get_aiida_class().get_state() == wf_states.RUNNING:
                running_no += 1
        self.assertEquals(running_no, 0,
                          "At this point there should be "
                          "no running workflows.")

        # Make the daemon to advance a bit more and make sure that no
        # workflows resurrect.
        for _ in range(5):
            legacy_workflow_stepper()

        self.assertEquals(len(list(get_all_running_steps())), 0,
                          "At this point there should be no running steps.")
        running_no = 0
        for w in get_workflow_list(user=user, all_states=True):
            if w.get_aiida_class().get_state() == wf_states.RUNNING:
                running_no += 1
        self.assertEquals(running_no, 0,
                          "At this point there should be "
                          "no running workflows.")
