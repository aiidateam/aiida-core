#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

def launch_ws():

    """
    To control the wf_stauts use the procedure 
    
    wf.list_workflows() 
    
    and to force the retrival of some calculation you can use the function
    
    wf.retrieve_by_uuid(uuid_wf).kill_step_calculations(methohd_wf)
    
    """
        
    import aiida.orm.workflow as wf
    from aiida.workflows import wf_demo
    from aiida.common.datastructures import wf_states
    
    params = {}
    params['nmachine']=2

    w = wf_demo.WorkflowDemo()
    w.set_params(params)
    w.start()
    
    w = wf_demo.WorkflowDemoBranch()
    w.set_params(params)
    w.start()