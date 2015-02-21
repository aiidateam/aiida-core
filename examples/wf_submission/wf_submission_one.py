#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

def launch_ws():

    """
    To control the wf status use the command line
    
    verdi workflow list pk
    
    """
        
    import aiida.orm.workflow as wf
    from aiida.workflows import wf_demo
    from aiida.common.datastructures import wf_states
    
    params = {}
    params['nmachine']=2

    w = wf_demo.WorkflowDemo()
    w.set_params(params)
    w.store()
    w.start()
    
    w = wf_demo.BranchWorkflowDemo()
    w.set_params(params)
    w.start()
