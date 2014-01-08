#!/usr/bin/env python
import sys
import os

def launch_ws():

    """
    To control the wf_stauts use the procedure 
    
    wf.list_workflows() 
    
    and to force the retrival of some calculation you can use the function
    
    wf.retrieve_by_uuid(uuid_wf).kill_step_calculations(methohd_wf)
    
    """
    
    from aiida.common.utils import load_django
    
    load_django()
            
    import aiida.orm.workflow as wf
    from aiida.workflows.wfgiovanni import WorkflowCustomEOS
    import numpy
    
    params = {
#              'pw_codename': 'pw-svn-rosa',
              'pw_codename': 'pw-svn-bellatrix',
              'num_machines': 1,
              'num_cpus_per_machine': 32, ### CORRECT IF YOU WANT TO SEND ON BELLATRIX!
              'max_wallclock_seconds': 30*60,
              'pseudo_family': 'pbe-rrkjus-pslib030',
              'cell_dofree': 'x',
              'functionalized': True,
              'change_coord': 1, # independent variable is y
              'value_range': numpy.linspace(2.8,3.8,20).tolist(), # Change cell y value in this range
              'atom1': 'Si',
              'atom2': 'C',
              'ecutwfc': 60.,
              'ecutrho': 350.,
              'kpoints': [6, 12, 1, 1, 1, 0],
              'startz': 20.,
              ## BNHH
              #'startx': 4.49,
              #'starty': 2.59,
              ## BN
              #'startx': 4.35,
              #'starty': 2.51,
              ## SiC
              'startx': 5.35,
              'starty': 3.09,
              }

    w = WorkflowCustomEOS(params=params)
    w.start()

    return w
    
if __name__ == "__main__":
    if sys.argv[1:] == ["--run"]:
        wf = launch_ws()
        print "Workflow launched, pk={}".format(wf.pk)
    else:
        print >> sys.stderr, "Pass --run to run the wf."
