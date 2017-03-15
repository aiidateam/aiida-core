#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
