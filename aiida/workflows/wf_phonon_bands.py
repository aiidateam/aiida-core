# -*- coding: utf-8 -*-
from __future__ import division
import os, copy
import aiida.common
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code
from aiida.orm import DataFactory
     
__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')


## ==================================================
##     General workflow to get QE phonon dispersions 
## ==================================================

'''
Example of use:
in the verdi shell type (you can use %paste or %cpaste to paste this)

from aiida.workflows.wf_phonon_bands import Workflow_Phonon_Bands
from aiida.orm.workflow import Workflow
from ase.lattice.spacegroup import crystal
from aiida.orm.data.structure import StructureData
alat=3.568 # lattice parameter in Angstrom
diamond_ase = crystal('C', [(0,0,0)], spacegroup=227,
                              cellpar=[alat, alat, alat, 90, 90, 90], primitive_cell=True)
structure_diamond = StructureData(ase=diamond_ase).store()

params = {'pw_codename': 'pw-5.1-local',
    'ph_codename': 'ph-5.1-local', 
    'q2r_codename': 'q2r-5.1-local',
    'matdyn_codename': 'matdyn-5.1-local',
    'num_machines': 1,
    'num_mpiprocs_per_machine': 8,
    'max_wallclock_seconds': 30,
    'pseudo_family': 'pz-rrkjus-pslib030',
    'structure_pk': structure_diamond.pk,
    'energy_cutoff': 40,
    'kpoints_mesh_1': 4,
    'kpoints_mesh_2': 4,
    'kpoints_mesh_3': 4,
    'qpoints_mesh_1': 4,
    'qpoints_mesh_2': 4,
    'qpoints_mesh_3': 4,
    'asr': 'crystal',
    'dual': 8,
    'smearing': 'None',
    'degauss': 0.,
    'el_conv_thr': 1e-12,
    'ph_conv_thr': 1e-16,
    'num_qpoints_in_dispersion': 2000,
    'use_images': True,
    'output_path': '/home/mounet/Documents/Phonon_results/Diamond_results/',
    'output_name': 'diamond_general_wf_images_PZ_RRKJ_pslib0.3_444_'}

wf = Workflow_Phonon_Bands(params=params)
wf.start()
'''

class Workflow_Phonon_Bands(Workflow):
    
    def __init__(self,**kwargs):
        
        super(Workflow_Phonon_Bands, self).__init__(**kwargs)
    
    def get_pw_parameters(self, ecutwfc, ecutrho, el_conv_thr, diagonalization,
                          mixing_mode, mixing_beta, occupations, smearing, degauss):
        
        parameters = ParameterData(dict={
                    'CONTROL': {
                        'calculation': 'scf',
                        'restart_mode': 'from_scratch',
                        'wf_collect': True,
                        },
                    'SYSTEM': {
                        'ecutwfc': ecutwfc,
                        'ecutrho': ecutrho,
                        'occupations': occupations,
                        'smearing': smearing,
                        'degauss': degauss,
                        },
                    'ELECTRONS': {
                        'diagonalization': diagonalization,
                        'mixing_mode': mixing_mode,
                        'mixing_beta': mixing_beta,
                        'conv_thr': el_conv_thr,
                        }})
                        
        return parameters
    
    def get_kpoints(self, kpoints_mesh):
        
        kpoints = KpointsData()    
        kpoints.set_kpoints_mesh(kpoints_mesh)
        
        return kpoints
    
    def get_q2r_parameters(self, asr):
        
        parameters = ParameterData(dict={
                    'INPUT': {
                        'zasr': asr,
                        },
                    })
                    
        return parameters
    
    def get_qpoints_dispersion(self,structure,num_qpoints=None):
        
        qpoints = KpointsData()
        qpoints.set_cell_from_structure(structure)
        if num_qpoints == 'None':
            num_qpoints = None
        qpoints.set_kpoints_path(tot_num_kpoints=num_qpoints)   
        
        return qpoints
    
    def get_matdyn_parameters(self, asr):
        
        parameters = ParameterData(dict={
                    'INPUT': {
                        'asr': asr,
                        },
                    })
                    
        return parameters
    
    ## ===============================================
    ##    Calculations generators
    ## ===============================================
    
    def get_pw_calculation(self, params):
        
        codename                    = params["pw_codename"]
        num_machines                = params["num_machines"]
        num_mpiprocs_per_machine    = params["num_mpiprocs_per_machine"]
        max_wallclock_seconds       = params["max_wallclock_seconds"]
        pseudo_family               = params["pseudo_family"]
        structure_pk                = params["structure_pk"]
        ecutwfc                     = params["energy_cutoff"]
        smearing                    = params["smearing"]
        kpoints_mesh_1              = params["kpoints_mesh_1"]
        kpoints_mesh_2              = params["kpoints_mesh_2"]
        kpoints_mesh_3              = params["kpoints_mesh_3"]
        ecutrho                     = params["dual"]*ecutwfc
        el_conv_thr                 = params["el_conv_thr"]
        diagonalization             = params["diagonalization"]
        mixing_mode                 = params["mixing_mode"]
        mixing_beta                 = params["mixing_beta"]
        
        if smearing == 'None':
            # default behavior, without smearing
            occupations = 'fixed'
            smearing = 'gaussian'
            degauss = 0.
        else:
            occupations = 'smearing'
            degauss = params["degauss"]

        structure = StructureData.get_subclass_from_pk(structure_pk)
        kpoints_mesh=[kpoints_mesh_1,kpoints_mesh_2,kpoints_mesh_3]
        
        pw_parameters = self.get_pw_parameters(ecutwfc, ecutrho, el_conv_thr, 
                          diagonalization, mixing_mode, mixing_beta,
                          occupations, smearing, degauss)
        pw_kpoints = self.get_kpoints(kpoints_mesh)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines,
                            "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        
        calc.use_structure(structure)
        calc.use_pseudos_from_family(pseudo_family)
        calc.use_parameters(pw_parameters)
        calc.use_kpoints(pw_kpoints)
        
        calc.store_all()
        
        return calc
                
    def get_q2r_calculation(self, params, ph_calc):
        
        codename                    = params["q2r_codename"]
        max_wallclock_seconds       = params["max_wallclock_seconds"]
        num_machines                = 1
        num_mpiprocs_per_machine    = 1
        asr                         = params["asr"]
        
        q2r_parameters = self.get_q2r_parameters(asr)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        
        calc.use_parameters(q2r_parameters)
        calc.use_parent_calculation(ph_calc)
        
        calc.store_all()
        
        return calc

    def get_matdyn_calculation(self, params, q2r_calc):
        
        codename                    = params["matdyn_codename"]
        max_wallclock_seconds       = params["max_wallclock_seconds"]
        num_machines                = 1
        num_mpiprocs_per_machine    = 1
        asr                         = params["asr"]
        structure_pk                = params["structure_pk"]
        num_qpoints_in_dispersion   = params["num_qpoints_in_dispersion"]
        
        structure = StructureData.get_subclass_from_pk(structure_pk)
        qpoints_dispersion = self.get_qpoints_dispersion(structure,
                                                         num_qpoints=num_qpoints_in_dispersion)
        matdyn_parameters = self.get_matdyn_parameters(asr)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines,
                            "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        
        calc.use_parameters(matdyn_parameters)
        calc.use_kpoints(qpoints_dispersion)
        calc.use_parent_calculation(q2r_calc)

        calc.store_all()
        
        return calc

    ## ===============================================
    ##    Workflow steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Checking input parameters")
        
        params = self.get_parameters() # user parameters
        new_params = {} # extended parameters (including optional parameters with default values)
        
        # define the mandatory keywords and the corresponding description to be 
        # printed in case the keyword is missing in params
        list_mandatory_keywords = [('pw_codename','the PW codename'),
                                   ('ph_codename','the PH codename'),
                                   ('q2r_codename','the Q2R codename'),
                                   ('matdyn_codename','the MATDYN codename'),
                                   ('structure_pk',"the structure (pk of a previously"
                                                   " stored StructureData object)"),
                                   ('energy_cutoff','the energy cutoff (Ry)'),
                                   ('kpoints_mesh_1',"the number of kpoints in the mesh,"
                                                     " along 1st reciprocal lattice vector"),
                                   ('kpoints_mesh_2',"the number of kpoints in the mesh,"
                                                     " along 2nd reciprocal lattice vector"),
                                   ('kpoints_mesh_3',"the number of kpoints in the mesh,"
                                                     " along 3rd reciprocal lattice vector"),
                                   ('qpoints_mesh_1',"the number of qpoints in the mesh for PH,"
                                                     " along 1st reciprocal lattice vector"),
                                   ('qpoints_mesh_2',"the number of qpoints in the mesh for PH,"
                                                     " along 2nd reciprocal lattice vector"),
                                   ('qpoints_mesh_3',"the number of qpoints in the mesh for PH,"
                                                     " along 3rd reciprocal lattice vector"),
                                   ('pseudo_family','the pseudopotential family'),
                                   ('num_machines','the number of machines'),
                                   ('num_mpiprocs_per_machine','the number of cores per machine'),
                                   ('max_wallclock_seconds','the max. wall time in seconds'),
                                   ('asr',"the acoustic sum rule ('no', 'simple',"
                                          " 'crystal','one-dim' or 'zero-dim')"),
                                   ('output_path',"the output folder"),
                                   ]
        
        # define the optional keywords and the corresponding default value
        # when they are missing from params
        list_optional_keywords = [('dual',8),
                                  ('smearing','None'),
                                  ('degauss',0.),
                                  ('diagonalization','david'),
                                  ('mixing_mode','plain'),
                                  ('mixing_beta',0.7),
                                  ('el_conv_thr',1e-12),
                                  ('ph_conv_thr',1e-16),
                                  ('num_qpoints_in_dispersion','None'),
                                  ('output_name','some_structure_'),
                                  ('use_images',False),
                                  ('use_grid',False),
                                  ]
        
        # check the mandatory keyword (raise an error if not present)
        for key_word,key_description in list_mandatory_keywords:
           try:
               new_params[key_word] = params[key_word]
           except KeyError:
               raise KeyError("Please specify "+key_description+" in params['"+key_word+"']")
                
        # check the other keywords if there are in params, otherwise add them
        # to params with the default value
        for key_word,default_value in list_optional_keywords:
            new_params[key_word] = params.get(key_word,default_value)
       
        # check on use_images and use_grid keywords (should not be both True)
        if (new_params['use_images'] and new_params['use_grid']):
            raise KeyError("use_images and use_grid flags cannot be both True! "
                           "Please choose either parallelization on images or "
                           "using the GRID.")
        
        self.add_attributes(new_params)
        self.next(self.run_pw)
        
    @Workflow.step
    def run_pw(self):
        
        params = self.get_attributes()
        self.append_to_report("Launching PW computation")
            
        # Prepare the PW computation
        pw_calc = self.get_pw_calculation(params)
        # Launch the PW computation    
        self.attach_calculation(pw_calc)            
            
        self.next(self.run_ph)
        
    @Workflow.step
    def run_ph(self):
        
        params = self.get_attributes()

        # Retrieve the PW calculation
        pw_calc = self.get_step_calculations(self.run_pw)[0]
        params.update({'parent_calc_uuid': pw_calc.uuid})
        
        # Launch the PH sub-workflow
        self.append_to_report("Launching PH sub-workflow")
        if params['use_images']==True:
            wf_ph = Workflow_Ph_images(params=params)
        elif params['use_grid']==True:
            wf_ph = Workflow_Ph_grid(params=params)
        else:
            params.update({'only_init'  : False,
                           'only_wfc'   : False,
                           'recover'    : False,
                           })
            wf_ph = Workflow_Ph_restart(params=params)
        
        wf_ph.start()
        self.attach_workflow(wf_ph)
        
        self.next(self.run_q2r)
    
    @Workflow.step
    def run_q2r(self):
        
        params = self.get_attributes()

        # Retrieve the PH calculation
        wf_ph = self.get_step(self.run_ph).get_sub_workflows()[0]
        ph_calc = wf_ph.get_result('ph.calc')
        
        # Launch the Q2R computation
        self.append_to_report("Launching Q2R from PH (pk={0})".format(ph_calc.pk))
        q2r_calc = self.get_q2r_calculation(params,ph_calc)
        self.attach_calculation(q2r_calc)
            
        self.next(self.run_matdyn)

    @Workflow.step
    def run_matdyn(self):
        
        params = self.get_attributes()

        # Retrieve the Q2R calculation
        q2r_calc = self.get_step_calculations(self.run_q2r)[0]
        
        # Launch the MATDYN computation
        self.append_to_report("Launching MATDYN from Q2R (pk={0})".format(q2r_calc.pk))
        
        matdyn_calc = self.get_matdyn_calculation(params,q2r_calc)
        self.attach_calculation(matdyn_calc)
        
        self.next(self.final_step)
    
    @Workflow.step   
    def final_step(self):
        
        params = self.get_attributes()
        
        # Retrieve the MATDYN calculation  
        matdyn_calc = self.get_step_calculations(self.run_matdyn)[0]
        
        # get bands
        bandsdata = matdyn_calc.out.output_phonon_bands
        bands = bandsdata.get_bands()
        # export them in xmgrace format
        output_file_name=os.path.join(params['output_path'],
                                      params['output_name']+"phonon_bands.agr")
        bandsdata.export(output_file_name, overwrite = True)
        
        self.append_to_report("Phonon dispersions done and put in {0}".format(output_file_name))
        
        self.add_result("phonon.dispersion", matdyn_calc)
            
        self.next(self.exit)


## ========================================================
##     General workflow to run QE ph.x code
##     with parallelization on a GRID (q-points and 
##     representations, handled manually)
##     NOT WORKING YET
## ========================================================


class Workflow_Ph_grid(Workflow):
    

    def __init__(self,**kwargs):
        
        super(Workflow_Ph_grid, self).__init__(**kwargs)
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Starting PH grid sub-workflow")
        
        self.next(self.run_ph_init_band)
        
    @Workflow.step
    def run_ph_init_band(self):
        
        # runs an initial band computation (used only for a grid computation),
        # using the PH restart wf
        params = self.get_parameters()
        
        self.append_to_report("Launching initial PH band computation")
        params.update({'only_init'  : False,
                       'only_wfc'   : True,
                       'recover'    : False,
                       'lqdir'      : True,
                       })
        wf_ph_init_band = Workflow_Ph_restart(params=params)
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
        
        # Launch the PH initial computation (using the PH restart workflow)
        self.append_to_report("Launching initial PH computation")
        params.update({'only_init'  : True,
                       'only_wfc'   : False,
                       'recover'    : True,
                       'lqdir'      : True,
                       'parent_calc_uuid': ph_calc.uuid,
                       })
        wf_ph_init = Workflow_Ph_restart(params=params)
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
        
        self.append_to_report("PH grid sub-workflow completed")
        
        self.add_result("ph.calc", ph_calc)

        self.next(self.exit)


## ========================================================
##     General workflow to run QE ph.x code
##     with parallelization on images (q-points and
##     representations, handled by QE itself)
##     NOT WORKING YET
## ========================================================


class Workflow_Ph_images(Workflow):
    

    def __init__(self,**kwargs):
        
        super(Workflow_Ph_images, self).__init__(**kwargs)
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Starting PH images sub-workflow")
        
        self.next(self.run_ph)
        
    @Workflow.step
    def run_ph(self):
        
        # Launch the initial PH computation on images (using the PH restart wf)
        params = self.get_parameters()
        
        self.append_to_report("Launching initial PH computation on images")
        params.update({'only_init'  : False,
                       'only_wfc'   : False,
                       'recover'    : False,
                       })
        wf_ph_init = Workflow_Ph_restart(params=params)
        wf_ph_init.start()
        self.attach_workflow(wf_ph_init)
                    
        self.next(self.run_ph_collect)
        
    @Workflow.step
    def run_ph_collect(self):
        
        # collect the PH results (from images)
        params = self.get_parameters()

        # Retrieve the initial PH calculation from the previous step
        wf_ph_init = self.get_step(self.run_ph).get_sub_workflows()[0]
        ph_calc = wf_ph_init.get_result('ph.calc')
        
        # Launch the PH "collect" computation
        self.append_to_report("Collecting PH results from images")
        params.update({'only_init'  : False,
                       'only_wfc'   : False,
                       'use_images' : False,
                       'recover'    : True,
                       'parent_calc_uuid': ph_calc.uuid,
                       'num_mpiprocs_per_machine': 1,
                       })
        wf_ph_collect = Workflow_Ph_restart(params=params)
        wf_ph_collect.start()
        self.attach_workflow(wf_ph_collect)
        
        self.next(self.final_step)
    
    @Workflow.step   
    def final_step(self):
        
        # Retrieve the last PH calculation (collect)
        wf_ph_collect = self.get_step(self.run_ph_collect).get_sub_workflows()[0]
        ph_calc = wf_ph_collect.get_result('ph.calc')
        
        self.append_to_report("PH images sub-workflow completed")
        
        self.add_result("ph.calc", ph_calc)

        self.next(self.exit)


## ==================================================
##     Workflow to handle a single QE ph.x run
##     with a restart management in case the wall
##     time is exceeded
## ==================================================


class Workflow_Ph_restart(Workflow):
    

    def __init__(self,**kwargs):
        
        super(Workflow_Ph_restart, self).__init__(**kwargs)
    
    def get_ph_parameters(self, qpoints_mesh, ph_conv_thr, only_init=False,
                            only_wfc=False, recover=False, max_seconds=1e7):
        
        parameters = ParameterData(dict={
            'INPUTPH': {
                'tr2_ph' : ph_conv_thr,
                'epsil' : True,
                'ldisp' : True,
                'nq1' : qpoints_mesh[0],
                'nq2' : qpoints_mesh[1],
                'nq3' : qpoints_mesh[2],
                'only_init' : only_init,
                'only_wfc' : only_wfc,
                'recover' : recover,
                'max_seconds' : max_seconds,
                }})
                
        return parameters
    
    def get_ph_calculation(self, params, parent_calc):
        
        '''
        if params["use_images"]==True, uses parallelization on images (q points
        and irreducible representations), with 
        num_mpiprocs_per_machine*num_machines images
        '''
        
        codename                    = params["ph_codename"]
        num_machines                = params["num_machines"]
        num_mpiprocs_per_machine    = params["num_mpiprocs_per_machine"]
        max_wallclock_seconds       = params["max_wallclock_seconds"]
        qpoints_mesh_1              = params["qpoints_mesh_1"]
        qpoints_mesh_2              = params["qpoints_mesh_2"]
        qpoints_mesh_3              = params["qpoints_mesh_3"]
        ph_conv_thr                 = params["ph_conv_thr"]
        use_images                  = params["use_images"]
        only_init                   = params["only_init"]
        only_wfc                    = params["only_wfc"]
        recover                     = params["recover"]
        
        qpoints_mesh=[qpoints_mesh_1,qpoints_mesh_2,qpoints_mesh_3]
        ph_parameters = self.get_ph_parameters(qpoints_mesh, ph_conv_thr,
                                               only_init, only_wfc, recover,
                                               max_wallclock_seconds)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines,
                            "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        calc.use_parameters(ph_parameters)
        calc.use_parent_calculation(parent_calc)

        if use_images:
            settings = ParameterData(dict={'cmdline': ['-ni',
                                str(num_mpiprocs_per_machine*num_machines)]})
            calc.use_settings(settings)
        
        calc.store_all()
        
        return calc
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Starting PH restart sub-workflow")
        
        self.next(self.run_ph_restart)
        
    @Workflow.step
    def run_ph_restart(self):
        
        # launch Phonon code, or restart it if maximum wall time was exceeded.
        # go to final_step when computation succeeded in previous step.
        params = self.get_parameters()
        max_wallclock_seconds = params["max_wallclock_seconds"]
        
        # Retrieve the list of PH calculations already done in this step
        ph_calc_list = self.get_step_calculations(self.run_ph_restart).order_by('ctime')
        n_ph_calc = len(ph_calc_list)
            
        if n_ph_calc==0:
            # Initial computation (parent must be a pw calculation)
            
            # Retrieve from the parameters the parent PW computation
            parent_calc_uuid = params['parent_calc_uuid']
            parent_calc = Calculation.get_subclass_from_uuid(parent_calc_uuid)
            
            # Launch the phonon code (first trial)
            self.append_to_report("Launching ph.x from parent calculation (pk={0})"
                                  .format(parent_calc.pk))
            ph_calc = self.get_ph_calculation(params,parent_calc)
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
                    max_wallclock_seconds = params["max_wallclock_seconds"]
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
        
        self.append_to_report("PH restart sub-workflow completed")
        
        self.add_result("ph.calc", ph_calc)

        self.next(self.exit)
