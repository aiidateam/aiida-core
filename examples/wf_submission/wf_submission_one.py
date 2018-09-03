#!/usr/bin/env python
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
import sys
import os



def launch_ws():
    """
    To control the wf status use the command line
    
    verdi workflow list pk
    
    """

    import aiida.orm.workflow as wf
    from aiida.workflows import wf_demo
    from aiida.common.datastructures import wf_states

    params = {}
    params['nmachine'] = 2

    w = wf_demo.WorkflowDemo()
    w.set_params(params)
    w.store()
    w.start()

    w = wf_demo.BranchWorkflowDemo()
    w.set_params(params)
    w.start()
