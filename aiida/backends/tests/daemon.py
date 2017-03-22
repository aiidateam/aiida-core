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
from aiida.orm import User
from aiida.orm.workflow import Workflow
from aiida.workflows.test import WFTestSimpleWithSubWF
from aiida.orm import get_workflow_info
from aiida.daemon.tasks import manual_tick_all


class TestDaemonBasic(AiidaTestCase):
    def test_workflow_fast_kill(self):
        from aiida.workflows import wf_demo

        params = dict()
        params['nmachine'] = 2

        w = WFTestSimpleWithSubWF()
        w.start()
        print "======> ", w.pk

        # Get the user
        dbuser = User.search_for_users(email=self.user_email)[0]
        wfqs = get_workflow_list(pk_list=[str(w.pk)], user=dbuser)
        print "WWWWWW", wfqs
        for w in wfqs:
            for line in get_workflow_info(w):
                print line

        print "Killing the workflow"

        from aiida.cmdline.commands.workflow import Workflow as WfCmd
        wf_cmd = WfCmd()
        wf_cmd.workflow_kill(*[str(w.pk), "-f"])

        wfqs = get_workflow_list(pk_list=[str(w.pk)], user=dbuser)
        print "WWWWWW", wfqs
        for w in wfqs:
            for line in get_workflow_info(w):
                print line

        print "Ticking the daemon"
        manual_tick_all()

        wfqs = get_workflow_list(pk_list=[str(w.pk)], user=dbuser)
        print "WWWWWW", wfqs
        for w in wfqs:
            for line in get_workflow_info(w):
                print line

