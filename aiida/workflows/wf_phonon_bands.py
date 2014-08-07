# -*- coding: utf-8 -*-
from __future__ import division
import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer
from aiida.orm import CalculationFactory, DataFactory
        
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

from aiida.workflows.user.wf_phonon_bands import Workflow_Phonon_Bands
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
    'max_wallclock_seconds': 60*60,
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
    'el_conv_thr': 1e-12,
    'ph_conv_thr': 1e-16,
    'num_qpoints_in_dispersion': 2000,
    'output_path': '/home/mounet/Documents/Phonon_results/Diamond_results/',
    'output_name': 'diamond_general_wf_'}

wf = Workflow_Phonon_Bands(params=params)
wf.start()
'''

class Workflow_Phonon_Bands(Workflow):
    
    def __init__(self,**kwargs):
        
        super(Workflow_Phonon_Bands, self).__init__(**kwargs)
    
    def get_pw_parameters(self, ecutwfc, ecutrho, el_conv_thr, diagonalization,
                          mixing_mode, mixing_beta):
        
        parameters = ParameterData(dict={
                    'CONTROL': {
                        'calculation': 'scf',
                        'restart_mode': 'from_scratch',
                        'wf_collect': True,
                        },
                    'SYSTEM': {
                        'ecutwfc': ecutwfc,
                        'ecutrho': ecutrho,
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
    
    def get_ph_parameters(self, qpoints_mesh, ph_conv_thr):
        
        parameters = ParameterData(dict={
            'INPUTPH': {
                'tr2_ph' : ph_conv_thr,
                'epsil' : True,
                'ldisp' : True,
                'nq1' : qpoints_mesh[0],
                'nq2' : qpoints_mesh[1],
                'nq3' : qpoints_mesh[2],
                }})
                
        return parameters
    
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
        kpoints_mesh_1              = params["kpoints_mesh_1"]
        kpoints_mesh_2              = params["kpoints_mesh_2"]
        kpoints_mesh_3              = params["kpoints_mesh_3"]
        ecutrho                     = params["dual"]*ecutwfc
        el_conv_thr                 = params["el_conv_thr"]
        diagonalization             = params["diagonalization"]
        mixing_mode                 = params["mixing_mode"]
        mixing_beta                 = params["mixing_beta"]
        
        structure = StructureData.get_subclass_from_pk(structure_pk)
        kpoints_mesh=[kpoints_mesh_1,kpoints_mesh_2,kpoints_mesh_3]
        
        pw_parameters = self.get_pw_parameters(ecutwfc, ecutrho, el_conv_thr, 
                          diagonalization, mixing_mode, mixing_beta)
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
                
    def get_ph_calculation(self, params, pw_calc):
        
        codename                    = params["ph_codename"]
        num_machines                = params["num_machines"]
        num_mpiprocs_per_machine    = params["num_mpiprocs_per_machine"]
        max_wallclock_seconds       = params["max_wallclock_seconds"]
        qpoints_mesh_1              = params["qpoints_mesh_1"]
        qpoints_mesh_2              = params["qpoints_mesh_2"]
        qpoints_mesh_3              = params["qpoints_mesh_3"]
        ph_conv_thr                 = params["ph_conv_thr"]
        
        qpoints_mesh=[qpoints_mesh_1,qpoints_mesh_2,qpoints_mesh_3]
        ph_parameters = self.get_ph_parameters(qpoints_mesh, ph_conv_thr)
        
        code = Code.get(codename)
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines,
                            "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        
        calc.use_parameters(ph_parameters)
        calc.set_parent_calc(pw_calc)
        
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
        calc.set_parent_calc(ph_calc)
        
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
        calc.set_parent_calc(q2r_calc)

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
                                   ('output_path',"the output folder")]
        
        # define the optional keywords and the corresponding default value
        # when they are missing from params
        list_optional_keywords = [('dual',8),
                                  ('diagonalization','david'),
                                  ('mixing_mode','plain'),
                                  ('mixing_beta',0.7),
                                  ('el_conv_thr',1e-12),
                                  ('ph_conv_thr',1e-16),
                                  ('num_qpoints_in_dispersion','None'),
                                  ('output_name','some_structure_')]
        
        # check the mandatory keyword (raise an error if not present)
        for key_word,key_description in list_mandatory_keywords:
           try:
               new_params[key_word] = params[key_word]
           except KeyError:
               raise KeyError("Please indicate "+key_description+" in params['"+key_word+"']")
                
        # check the other keywords if there are in params, otherwise add them
        # to params with the default value
        for key_word,default_value in list_optional_keywords:
          try:
              new_params[key_word] = params[key_word]
          except KeyError:
              new_params[key_word] = default_value
       
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
        
        # Launch the PH computation
        self.append_to_report("Launching PH from PW (pk={0})".format(pw_calc.pk))
        ph_calc = self.get_ph_calculation(params,pw_calc)
        self.attach_calculation(ph_calc)
            
        self.next(self.run_q2r)
    
    @Workflow.step
    def run_q2r(self):
        
        params = self.get_attributes()

        # Retrieve the PH calculation
        ph_calc = self.get_step_calculations(self.run_ph)[0]
        
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
        output_file_name=params['output_path']+params['output_name']+"phonon_bands.agr"
        bandsdata.export(output_file_name, overwrite = False)
        
        self.append_to_report("Phonon dispersions done and put in {0}".format(output_file_name))
        
        self.add_result("phonon.dispersion", matdyn_calc)
            
        self.next(self.exit)



