# -*- coding: utf-8 -*-
from __future__ import division
import os, copy
import aiida.common
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Node
from aiida.orm import DataFactory
from aiida.workflows.wf_pw import (check_keywords,
                                   check_parameter_pk_and_extract_dict,
                                   update_and_store_params)
     
__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')


## ==================================================
##     General workflow to run QE-PHonon
##     There are actually 4 separate workflows:
##	    - WorkflowPH : run QE-PH; depending on 
##	    parameters it will run one of the three
##	    workflows below,
##	    - WorkflowPhGrid: run QE-PH with a 
##	    parallelization on the grid; it uses 
##	    WorkflowPhRestart,
##	    - WorkflowPhImages: run QE-PH with a 
##	    parallization on images; it uses 
##	    WorkflowPhRestart,
##	    - WorkflowPhRestart: lowest level of ph
##	    workflow (launch ph.x with a restart
##	    management)
## ==================================================

'''
Example of use:
in the verdi shell type (you can use %paste or %cpaste to paste this)

from aiida.workflows.wf_ph import WorkflowPH
from aiida.orm.workflow import Workflow
from aiida.orm.data.parameter import ParameterData

ph_params = ParameterData(dict={'ph_codename': 'ph-5.1-local',
                                'qpoints_mesh_1': 4,
                                'qpoints_mesh_2': 4,
                                'qpoints_mesh_3': 4,
                                'tr2_ph': 1e-16,
                                'pw_calc_pk': 3816,
                                'INPUTPH': {},
                                'num_machines': 1,
                                'num_mpiprocs_per_machine': 8,
                                'max_wallclock_seconds': 30,
                                'nimages': 1,
                                'npools': 4,
                                'use_grid': False,
                                }).store()

params = {'PH_pk': ph_params.pk,
         }

wf = WorkflowPH(params=params)
wf.start()

Note: if one defines some additional dictionaries for the keyword 'INPUTPH' in ph_params, 
then the corresponding namelist in the PH input file is updated with these values 
(adding new parameters or overriding those already defined).
'''

## ==================================================
##     PH workflow 
## ==================================================

class WorkflowPH(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowPH, self).__init__(**kwargs)
    
    ## ===============================================
    ##    Workflow steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Checking PH input parameters")
        
        # define the mandatory keywords and the corresponding description to be 
        # printed in case the keyword is missing, for the global input 
        # parameters and the PH parameters
        list_mandatory_keywords_params = [('PH_pk',"the PH parameters (pk of a "
                                           "previously stored ParameterData "
                                           "object)")]
        
        list_mandatory_keywords_ph = [('ph_codename','the PH codename'),
                                      ('qpoints_mesh_1',"the number of qpoints in the mesh for PH,"
                                                     " along 1st reciprocal lattice vector"),
                                      ('qpoints_mesh_2',"the number of qpoints in the mesh for PH,"
                                                     " along 2nd reciprocal lattice vector"),
                                      ('qpoints_mesh_3',"the number of qpoints in the mesh for PH,"
                                                     " along 3rd reciprocal lattice vector"),
                                      ('pw_calc_pk',"the parent PW calculation (pk of a "
                                                   " previously stored PwCalculation object)"),
                                      ('num_machines','the number of machines'),
                                      ('num_mpiprocs_per_machine','the number of cores per machine'),
                                      ('max_wallclock_seconds','the max. wall time in seconds'),
                                      ]
        
        # retrieve and check the initial user parameters
        params = self.get_parameters()
        check_keywords(params,list_mandatory_keywords_params)
        
        # PH parameters: retrieve and check
        ph_params = check_parameter_pk_and_extract_dict(params['PH_pk'],
                                                        'PH parameters')
        check_keywords(ph_params, list_mandatory_keywords_ph)

        # check that nimages and use_grid keywords are compatible (one
        # cannot launch a "grid" calculation with images)
        if (ph_params.get('nimages',0)>1 and ph_params.get('use_grid',False)):
            raise KeyError("Images and GRID parallelization cannot be used at "
                           "the same time. Please put EITHER nimages>1 OR "
                           "use_grid=True."
                           )
        self.next(self.run_ph)
        
    @Workflow.step
    def run_ph(self):
        
        # retrieve PH parameters (with parallelization flags)
        params = self.get_parameters()
        ph_params = ParameterData.get_subclass_from_pk(params['PH_pk']).get_dict()
        
        # extract pk of parent PW calculation
        pw_calc_pk=ph_params['pw_calc_pk']

        # update PH parameters
        update_dict = {'recover' : False,
                       'parent_calc_uuid': Calculation.get_subclass_from_pk(pw_calc_pk).uuid,
                       }
        the_params = update_and_store_params(params, 'PH_pk', update_dict,
                                             pop_list = ['pw_calc_pk'])
        
        self.append_to_report("Launching PH sub-workflow")
        if ph_params.get('nimages',0)>1:
            wf_ph = WorkflowPhImages(params=the_params)
        elif ph_params.get('use_grid',False):
            wf_ph = WorkflowPhGrid(params=the_params)
        else:
            wf_ph = WorkflowPhRestart(params=the_params)
        
        wf_ph.start()
        self.attach_workflow(wf_ph)
                
        self.next(self.final_step)
        
    @Workflow.step   
    def final_step(self):
        
        # Retrieve the PH calculation
        wf_ph = self.get_step(self.run_ph).get_sub_workflows()[0]
        ph_calc = wf_ph.get_result('ph.calc')
        
        self.add_result("ph.calc", ph_calc)
            
        self.append_to_report("PH workflow completed")
                    
        self.next(self.exit)

## ========================================================
##     General workflow to run QE ph.x code
##     with parallelization on a GRID (q-points and 
##     representations, handled manually)
## ========================================================

class WorkflowPhGrid(Workflow):
    

    def __init__(self,**kwargs):
        
        super(WorkflowPhGrid, self).__init__(**kwargs)
    
    ## ===============================================
    ##    Workflow steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Starting PH grid workflow")
        
        self.next(self.run_ph_init_band)
        
    @Workflow.step
    def run_ph_init_band(self):
        
        # runs an initial band computation (used only for a grid computation),
        # using the PH restart wf
        params = self.get_parameters()
        
        # update parameters for initial band structure computation
        update_dict = {'recover'    : False,
                       'only_wfc'   : True,
                       'lqdir'      : True,
                       }
        the_params = update_and_store_params(params, 'PH_pk', update_dict)

        self.append_to_report("Launching initial PH band structure computation")
        wf_ph_init_band = WorkflowPhRestart(params=params)
        wf_ph_init_band.start()
        self.attach_workflow(wf_ph_init_band)
        
        self.next(self.run_ph_init)
        
    @Workflow.step
    def run_ph_init(self):
        
        # runs the initial ph computation
        params = self.get_parameters()
        
        # Retrieve the initial PH band calculation from the previous step
        wf_ph_init_band = self.get_step(self.run_ph_init_band).get_sub_workflows()[0]
        ph_calc = wf_ph_init_band.get_result('ph.calc')
        
        # update parameters for initial part of the dynamical matrix computation
        update_dict = {'recover'            : True,
                       'only_init'          : True,
                       'lqdir'              : True,
                       'parent_calc_uuid'   : ph_calc.uuid,
                       }
        the_params = update_and_store_params(params, 'PH_pk', update_dict)
        # Retrieve the initial PH band calculation from the previous step
        wf_ph_init_band = self.get_step(self.run_ph_init_band).get_sub_workflows()[0]
        ph_calc = wf_ph_init_band.get_result('ph.calc')
        
        # Launch the PH initial computation (using the PH restart workflow)
        self.append_to_report("Launching PH initialization")
        params.update({'only_init'  : True,
                       'only_wfc'   : False,
                       'recover'    : True,
                       'lqdir'      : True,
                       'parent_calc_uuid': ph_calc.uuid,
                       })
        wf_ph_init = WorkflowPhRestart(params=params)
        wf_ph_init.start()
        self.attach_workflow(wf_ph_init)
        
        self.next(self.run_ph_grid)
        
    @Workflow.step
    def run_ph_grid(self):
        
        # runs the parallel ph jobs for each q-point and representation 
        params = self.get_parameters()
        
        # Retrieve from the parameters the parent PH computation
        ph_calc_init = Calculation.get_subclass_from_uuid(pw_calc_uuid)
        
        # Launch the PH computation
        self.append_to_report("Launching PH computation for all q-points "
                              "and representations")
        ph_calc = self.get_ph_calculation(params,pw_calc)
        self.attach_calculation(pw_calc)
        
        self.next(self.run_ph_collect)
        
    @Workflow.step
    def run_ph_collect(self):
        
        # collect the ph results from the grid
        params = self.get_parameters()

        # Launch the PH computation
        self.append_to_report("Launching PH from PW (pk={0})".format(pw_calc.pk))
        ph_calc = self.get_ph_calculation(params,pw_calc)
        self.attach_calculation(ph_calc)
        
        self.next(self.final_step)
    
    @Workflow.step   
    def final_step(self):
        
        # Retrieve the last PH calculation (collect)
        ph_calc = self.get_step_calculations(self.run_ph_collect)[0]
        
        self.append_to_report("PH grid workflow completed")
        
        self.add_result("ph.calc", ph_calc)

        self.next(self.exit)


## ========================================================
##     General workflow to run QE ph.x code
##     with parallelization on images (q-points and
##     representations, handled by QE itself)
## ========================================================


class WorkflowPhImages(Workflow):
    

    def __init__(self,**kwargs):
        
        super(WorkflowPhImages, self).__init__(**kwargs)
    
    ## ===============================================
    ##    Workflow steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Starting PH images workflow")
        
        self.next(self.run_ph)
        
    @Workflow.step
    def run_ph(self):
        
        # Launch the initial PH computation on images (using the PH restart wf)

        # retrieve PH parameters
        params = self.get_parameters()

        self.append_to_report("Launching initial PH computation on images")
        wf_ph_init = WorkflowPhRestart(params=params)
        wf_ph_init.start()
        self.attach_workflow(wf_ph_init)
                    
        self.next(self.run_ph_collect)
        
    @Workflow.step
    def run_ph_collect(self):
        
        # collect the PH results (from images)
        params = self.get_parameters()
        ph_params = ParameterData.get_subclass_from_pk(params['PH_pk']).get_dict()

        # Retrieve the initial PH calculation from the previous step
        wf_ph_init = self.get_step(self.run_ph).get_sub_workflows()[0]
        ph_calc = wf_ph_init.get_result('ph.calc')
        
        # update PH parameters, taking out parallelization on images but keeping
        # any other kind of parallelization
        num_machines = ph_params['num_machines']
        num_mpiprocs_per_machine = ph_params['num_mpiprocs_per_machine']
        nimages = ph_params['nimages']
        
        num_machines_phcollect = int(num_machines/nimages)
        num_mpiprocs_per_machine_phcollect = num_mpiprocs_per_machine
        if num_machines_phcollect == 0:
            from numpy import mod
            num_machines_phcollect = 1
            num_mpiprocs_per_machine_phcollect = int(num_mpiprocs_per_machine/nimages)
            
        self.append_to_report("nimages={0}, num_machines={1}, "
                              "num_mpiprocs_per_machine={2}".format(nimages,
                                        num_machines_phcollect,
                                        num_mpiprocs_per_machine_phcollect))
        
        update_dict = {'recover'                    : True,
                       'nimages'                    : None,
                       'num_machines'               : num_machines_phcollect,
                       'num_mpiprocs_per_machine'   : num_mpiprocs_per_machine_phcollect,
                       'parent_calc_uuid'           : ph_calc.uuid,
                       }
        the_params = update_and_store_params(params, 'PH_pk', update_dict)

        # Launch the PH "collect" computation
        self.append_to_report("Collecting PH computations on images")
        wf_ph_collect = WorkflowPhRestart(params=the_params)
        wf_ph_collect.start()
        self.attach_workflow(wf_ph_collect)
        
        self.next(self.final_step)
    
    @Workflow.step   
    def final_step(self):
        
        # Retrieve the last PH calculation (collect)
        wf_ph_collect = self.get_step(self.run_ph_collect).get_sub_workflows()[0]
        ph_calc = wf_ph_collect.get_result('ph.calc')
        
        self.append_to_report("PH images workflow completed")
        
        self.add_result("ph.calc", ph_calc)

        self.next(self.exit)


## ==================================================
##     Workflow to handle a single QE ph.x run
##     with a restart management in case the wall
##     time is exceeded
## ==================================================


class WorkflowPhRestart(Workflow):
    

    def __init__(self,**kwargs):
        
        super(WorkflowPhRestart, self).__init__(**kwargs)
    
    def get_ph_parameters(self, qpoints_mesh, tr2_ph, recover=False, max_seconds=1e7,
                        additional_inputph_dict={}):
        
        inputph_dict = {
                'tr2_ph' : tr2_ph,
                'epsil' : True,
                'ldisp' : True,
                'nq1' : qpoints_mesh[0],
                'nq2' : qpoints_mesh[1],
                'nq3' : qpoints_mesh[2],
                'recover' : recover,
                'max_seconds' : max_seconds,
                }
        
        inputph_dict.update(additional_inputph_dict)

        parameters = ParameterData(dict={'INPUTPH': inputph_dict})
                
        return parameters
    
    ## ============================
    ##    PH calculation generator
    ## ============================
    
    def get_ph_calculation(self, ph_params, parent_calc):
        
        # mandatory parameters (existence should have been checked before)
        codename                    = ph_params["ph_codename"]
        qpoints_mesh_1              = ph_params["qpoints_mesh_1"]
        qpoints_mesh_2              = ph_params["qpoints_mesh_2"]
        qpoints_mesh_3              = ph_params["qpoints_mesh_3"]
        num_machines                = ph_params["num_machines"]
        num_mpiprocs_per_machine    = ph_params["num_mpiprocs_per_machine"]
        max_wallclock_seconds       = ph_params["max_wallclock_seconds"]
        
        # optional parameters (if not provided, default values assigned)
        tr2_ph                      = ph_params.get("tr2_ph",1e-16)
        recover                     = ph_params.get("recover",False)
        additional_inputph_dict     = ph_params.get("INPUTPH",{})
        nimages                     = ph_params.get("nimages",None)
        npools                      = ph_params.get("npools",None)

        qpoints_mesh=[qpoints_mesh_1,qpoints_mesh_2,qpoints_mesh_3]
        ph_parameters = self.get_ph_parameters(qpoints_mesh, tr2_ph,
                                               recover, max_wallclock_seconds,
                                               additional_inputph_dict)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines,
                            "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        calc.use_parameters(ph_parameters)
        calc.use_parent_calculation(parent_calc)
        
        # add command-line parameters for parallelization, if needed
        cmdline_list=[]
        if (nimages is not None) and (nimages > 1):
            cmdline_list = cmdline_list + ['-ni', str(nimages)]
        if (npools is not None) and (npools > 1):
            cmdline_list = cmdline_list + ['-nk',str(npools)]     
        
        settings = ParameterData(dict={'cmdline': cmdline_list})
        calc.use_settings(settings)
        
        calc.store_all()
        
        return calc
    
    ## ===============================================
    ##    Workflow steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Starting PH restart workflow")
        
        self.next(self.run_ph_restart)
        
    @Workflow.step
    def run_ph_restart(self):
        
        # launch Phonon code, or restart it if maximum wall time was exceeded.
        # go to final_step when computation succeeded in previous step.
        
        # retrieve PH parameters
        params = self.get_parameters()
        ph_params = Node.get_subclass_from_pk(params['PH_pk']).get_dict()
        
        max_wallclock_seconds = ph_params["max_wallclock_seconds"]
        
        # Retrieve the list of PH calculations already done in this step
        ph_calc_list = self.get_step_calculations(self.run_ph_restart).order_by('ctime')
        n_ph_calc = len(ph_calc_list)
            
        if n_ph_calc==0:
            # Initial computation (parent must be a pw calculation)
            
            # Retrieve from the parameters the parent PW computation
            parent_calc_uuid = ph_params['parent_calc_uuid']
            parent_calc = Calculation.get_subclass_from_uuid(parent_calc_uuid)
            
            # Launch the phonon code (first trial)
            self.append_to_report("Launching ph.x from parent calculation (pk={0})"
                                  .format(parent_calc.pk))
            ph_calc = self.get_ph_calculation(ph_params,parent_calc)
            self.attach_calculation(ph_calc)
            
            # loop step on itself
            self.next(self.run_ph_restart)
        
        else:
            # Restarted computation
            
            # Retrieve the last PH calculation done inside this subworkflow
            ph_calc = ph_calc_list[len(ph_calc_list)-1]
            
            # test if it needs to be restarted
            if ph_calc.get_state()=='FINISHED':
                # computation succeeded -> go to final step   
                self.next(self.final_step)
                
            elif ph_calc.get_state()=='FAILED':
                if 'Maximum CPU time exceeded' in ph_calc.res.warnings:
                    # restart when maximum CPU time was exceeded
                    max_wallclock_seconds = ph_params["max_wallclock_seconds"]
                    self.append_to_report("WARNING: ph.x calculation (pk={0}) "
                                          "stopped because max CPU time ({1} s) was "
                                          "reached; restarting computation where it "
                                          "stopped".format(ph_calc.pk,max_wallclock_seconds))
                    # prepare restarted calculation
                    ph_new_calc = ph_calc.create_restart(restart_if_failed=True)
                    ph_new_calc.store_all()
                    # Launch calculation
                    self.attach_calculation(ph_new_calc)
                    # this restart step loops on itself
                    self.next(self.run_ph_restart)
                
                else:
                    # case of a real failure -> cannot restart
                    self.append_to_report("ERROR: ph.x (pk={}) failed unexpectedly, "
                                          "stopping".format(ph_calc.pk))
                    self.next(self.exit)
                
            else:   
                # any other case leads to stop
                self.append_to_report("ERROR: unexpected status ({0}) of ph.x (pk={1})"
                                      "calculation, stopping".format(ph_calc.get_state(),ph_calc.pk))
                self.next(self.exit)
        
    @Workflow.step   
    def final_step(self):
        
        # Retrieve the last PH calculation
        ph_calc_list = self.get_step_calculations(self.run_ph_restart).order_by('ctime')
        ph_calc = ph_calc_list[len(ph_calc_list)-1]
        
        self.append_to_report("PH restart workflow completed")
        
        self.add_result("ph.calc", ph_calc)

        self.next(self.exit)

