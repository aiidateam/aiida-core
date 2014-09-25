# -*- coding: utf-8 -*-
from __future__ import division
import os, copy
import aiida.common
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Node
from aiida.orm import DataFactory
from aiida.orm.calculation.quantumespresso.ph import PhCalculation
from aiida.orm.calculation.quantumespresso.pw import PwCalculation
from aiida.workflows.wf_pw import (WorkflowPW, check_keywords,
                                   check_parameter_pk_and_extract_dict,
                                   update_and_store_params)
from aiida.workflows.wf_ph import WorkflowPH

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')


## ==================================================
##     General workflow to get QE phonon dispersions 
## ==================================================

'''
Examples of use:
in the verdi shell type (you can use %paste or %cpaste to paste this)

from aiida.workflows.wf_phonon_bands import WorkflowPhononBands
from aiida.orm.workflow import Workflow
from ase.lattice.spacegroup import crystal
from aiida.orm.data.structure import StructureData
from aiida.orm.data.parameter import ParameterData

alat=3.568 # lattice parameter in Angstrom
diamond_ase = crystal('C', [(0,0,0)], spacegroup=227,
                              cellpar=[alat, alat, alat, 90, 90, 90], primitive_cell=True)
structure_diamond = StructureData(ase=diamond_ase).store()

pw_params = ParameterData(dict={'pw_codename': 'pw-5.1-local',
                                'pseudo_family': 'pz-rrkjus-pslib030',
                                'structure_pk': structure_diamond.pk,
                                'energy_cutoff': 40,
                                'kpoints_mesh_1': 4,
                                'kpoints_mesh_2': 4,
                                'kpoints_mesh_3': 4,
                                'dual': 8,
                                'smearing': None,
                                'degauss': 0.,
                                'conv_thr': 1e-12,
                                'CONTROL': {},
                                'SYSTEM': {},
                                'ELECTRONS': {},
                                'num_machines': 1,
                                'num_mpiprocs_per_machine': 8,
                                'max_wallclock_seconds': 30,
                                'npools': 8,
                                }).store()

ph_params = ParameterData(dict={'ph_codename': 'ph-5.1-local',
                                'qpoints_mesh_1': 4,
                                'qpoints_mesh_2': 4,
                                'qpoints_mesh_3': 4,
                                'tr2_ph': 1e-16,
                                'INPUTPH': {},
                                'num_machines': 1,
                                'num_mpiprocs_per_machine': 8,
                                'max_wallclock_seconds': 30,
                                'nimages': 4,
                                'npools': 2,
                                'use_grid': False,
                                }).store()

band_params = ParameterData(dict={'q2r_codename': 'q2r-5.1-local',
                                  'matdyn_codename': 'matdyn-5.1-local',
                                  'zasr': 'crystal',
                                  'asr': 'crystal',
                                  'num_qpoints_in_dispersion': 2000,
                                  'max_wallclock_seconds': 1000,
                                  'output_path': '/home/mounet/Documents/Phonon_results/Diamond_results/',
                                  'output_name': 'diamond_general_wf_images_PZ_RRKJ_pslib0.3_444_',
                                  }).store()


params = {'PW_pk': pw_params.pk,
          'PH_pk': ph_params.pk,
          'band_params_pk': band_params.pk,
          }

or 

params = {'PW_pk': 3816,
          'PH_pk': ph_params.pk,
          'band_params_pk': band_params.pk,
          }

or

params = {'PH_pk': 4088,
          'band_params_pk': band_params.pk,
          }

wf = WorkflowPhononBands(params=params)
wf.start()

Note: 'PW_pk' and 'PH_pk' can contain resp. a pw or ph calculation object,
instead of parameters. Then the corresponding pw or ph step is skipped and
the workflow proceeds from this calculation. If 'PH_pk' is a calculation
then both the pw and ph steps are skipped ('PW_pk' is ignored).
'''

class WorkflowPhononBands(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowPhononBands, self).__init__(**kwargs)
    
    def get_q2r_parameters(self, zasr):
        
        parameters = ParameterData(dict={
                    'INPUT': {
                        'zasr': zasr,
                        },
                    })
                    
        return parameters
    
    def get_qpoints_dispersion(self,cell,pbc,num_qpoints=None):
        
        qpoints = KpointsData()
        qpoints.set_cell(cell, pbc)
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
                    
    def get_q2r_calculation(self, band_params, ph_calc):
        
        codename                    = band_params["q2r_codename"]
        max_wallclock_seconds       = band_params["max_wallclock_seconds"]
        zasr                        = band_params["zasr"]
        num_machines                = 1
        num_mpiprocs_per_machine    = 1
        
        q2r_parameters = self.get_q2r_parameters(zasr)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines, 
                            "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        
        calc.use_parameters(q2r_parameters)
        calc.use_parent_calculation(ph_calc)
        
        calc.store_all()
        
        return calc

    def get_matdyn_calculation(self, band_params, q2r_calc):
        
        codename                    = band_params["matdyn_codename"]
        max_wallclock_seconds       = band_params["max_wallclock_seconds"]
        asr                         = band_params["asr"]
        num_machines                = 1
        num_mpiprocs_per_machine    = 1
        num_qpoints_in_dispersion   = band_params.get("num_qpoints_in_dispersion",None)
        
        # extract cell and periodic boundary conditions from q2r force constants
        force_constants = q2r_calc.out.force_constants
        cell = force_constants.cell
        # test qpoints mesh extracted from force constants, to find the periodic 
        # boundary conditions: if one of the qpoints_mesh item is 1 or less, 
        # the corresponding direction is assumed to be not periodic
        pbc = tuple(q>1 for q in force_constants.qpoints_mesh)
        qpoints_dispersion = self.get_qpoints_dispersion(cell, pbc,
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
        
        # define the mandatory keywords and the corresponding description to be 
        # printed in case the keyword is missing, for the global input 
        # parameters and the PH parameters
        list_mandatory_keywords_params = [('PH_pk',"the PH parameters (pk of a "
                                           "previously stored ParameterData or "
                                           "PhCalculation object)"),
                                          ('band_params_pk',"the phonon band "
                                           "parameters (pk of a previously stored "
                                           "ParameterData object)"),
                                          ]
        
        # define the mandatory keywords and the corresponding description to be 
        # printed in case the keyword is missing in params
        list_mandatory_keywords_bands = [('q2r_codename','the Q2R codename'),
                                         ('matdyn_codename','the MATDYN codename'),
                                         ('asr',"the acoustic sum rule for the "
                                         " force constants ('no', 'simple',"
                                          " 'crystal','one-dim' or 'zero-dim')"),
                                         ('zasr',"the acoustic sum rule for the "
                                         " effective charges ('no', 'simple',"
                                          " 'crystal','one-dim' or 'zero-dim')"),
                                         ('output_path',"the output folder"),
                                         ]
                
        # retrieve and check the initial user parameters
        params = self.get_parameters()
        check_keywords(params,list_mandatory_keywords_params)
        
        # phonon band parameters: retrieve and check
        band_params = check_parameter_pk_and_extract_dict(params['band_params_pk'],
                                                        'Phonon band parameters')
        check_keywords(band_params, list_mandatory_keywords_bands)
 
        ph = Node.get_subclass_from_pk(params['PH_pk'])
        if isinstance(ph,PhCalculation):
            # if in 'PH_pk' there is a calculation, launch directly from the
            # Q2R step
            self.next(self.run_q2r)
        else:
            try:
                pw = Node.get_subclass_from_pk(params['PW_pk'])
                if isinstance(pw,PwCalculation):
                    # if in 'PW_pk' there is a calculation, launch directly 
                    # from the PH step
                    self.next(self.run_ph)
                else:
                    # in other cases, begins from scratch with PW
                    self.next(self.run_pw)
            
            except KeyError:
                raise KeyError("Object with pk {0} is not a PhCalculation, "
                               "so you need to specify pk of a ParameterData or "
                               "PwCalculation object in keyword "
                               "'PW_pk'.".format(params['PH_pk']))
                self.next(self.exit())
                
    @Workflow.step
    def run_pw(self):
        
        params = self.get_parameters()
        # take out parameters that are useless for the PW computation
        params.pop('PH_pk')
        params.pop('band_params_pk')
        
        self.append_to_report("Launching PW sub-workflow")
        wf_pw = WorkflowPW(params=params)        
        wf_pw.start()
        self.attach_workflow(wf_pw)
                    
        self.next(self.run_ph)
        
    @Workflow.step
    def run_ph(self):
        
        params = self.get_parameters()
        # take out parameters that are useless for the PH computation
        params.pop('band_params_pk')
        pw_pk = params.pop('PW_pk')
        
        # Retrieve the PW calculation
        if not isinstance(Node.get_subclass_from_pk(pw_pk), PwCalculation):
            wf_pw = self.get_step(self.run_pw).get_sub_workflows()[0]
            pw_pk = wf_pw.get_result('pw.calc').pk
        
        # update the ph parameters, adding the pk of the pw calculation
        ph_update_dict={'pw_calc_pk': pw_pk}
        the_params = update_and_store_params(params, 'PH_pk', ph_update_dict)
        
        # Launch the PH sub-workflow
        self.append_to_report("Launching PH sub-workflow")
        wf_ph = WorkflowPH(params=the_params)
        wf_ph.start()
        self.attach_workflow(wf_ph)
        
        self.next(self.run_q2r)
    
    @Workflow.step
    def run_q2r(self):
        
        params = self.get_parameters()
        band_params = Node.get_subclass_from_pk(params['band_params_pk']).get_dict()
        
        # Retrieve the PH calculation
        ph = Node.get_subclass_from_pk(params['PH_pk'])
        if isinstance(ph,PhCalculation): 
            ph_calc = ph
        else:
            wf_ph = self.get_step(self.run_ph).get_sub_workflows()[0]
            ph_calc = wf_ph.get_result('ph.calc')
        
        # Launch the Q2R computation
        self.append_to_report("Launching Q2R from PH (pk={0})".format(ph_calc.pk))
        q2r_calc = self.get_q2r_calculation(band_params,ph_calc)
        self.attach_calculation(q2r_calc)
            
        self.next(self.run_matdyn)

    @Workflow.step
    def run_matdyn(self):
        
        params = self.get_parameters()
        band_params = Node.get_subclass_from_pk(params['band_params_pk']).get_dict()
        
        # Retrieve the Q2R calculation
        q2r_calc = self.get_step_calculations(self.run_q2r)[0]
        
        # Launch the MATDYN computation
        self.append_to_report("Launching MATDYN from Q2R (pk={0})".format(q2r_calc.pk))
        
        matdyn_calc = self.get_matdyn_calculation(band_params,q2r_calc)
        self.attach_calculation(matdyn_calc)
        
        self.next(self.final_step)
    
    @Workflow.step   
    def final_step(self):
        
        params = self.get_parameters()
        band_params = Node.get_subclass_from_pk(params['band_params_pk']).get_dict()
        
        # Retrieve the MATDYN calculation  
        matdyn_calc = self.get_step_calculations(self.run_matdyn)[0]
        
        # get bands
        bandsdata = matdyn_calc.out.output_phonon_bands
        bands = bandsdata.get_bands()
        # export them in xmgrace format
        output_file_name=os.path.join(band_params['output_path'],
                                      band_params.get('output_name','some_structure_')
                                      +"phonon_bands.agr")
        bandsdata.export(output_file_name, overwrite = True)
        
        self.append_to_report("Phonon dispersions done and put in {0}".format(output_file_name))
        
        self.add_result("phonon.dispersion", matdyn_calc)
            
        self.next(self.exit)
