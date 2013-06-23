#!/usr/bin/env python
import sys
import os

def launch_ws():

    """
    To control the wf_stauts use the procedure 
    
    wf.list_workflows() 
    
    and to force the retrival of some calculation you can use the function
    
    wf.retrieve_by_uuid(uuid_wf).finish_step_calculations(methohd_wf)
    
    """
            
    import aiida.orm.workflow as wf
    from aiida.workflows import wf_sub_demo
    from aiida.common.datastructures import wf_states
    
    params = {}
    params['nmachine']=2

    w = wf_sub_demo.WorkflowDemoSubWorkflow()
    w.start()