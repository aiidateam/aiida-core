# -*- coding: utf-8 -*-
from __future__ import division
import os, copy
import aiida.common
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Node
from aiida.orm import DataFactory
from aiida.common.exceptions import NotExistent, InputValidationError
     
__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')


## ==================================================
##     General workflow to run QE-PWscf 
## ==================================================

'''
Example of use:
in the verdi shell type (you can use %paste or %cpaste to paste this)

from aiida.workflows.wf_pw import WorkflowPW
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
                                'npools': None,
                                }).store()

params = {'PW_pk': pw_params.pk,
         }

wf = WorkflowPW(params=params)
wf.start()

Note: if one defines some additional dictionaries for the keywords 'CONTROL', 'SYSTEM'
and/or 'ELECTRONS' in pw_params, then the corresponding namelists in the PW input file
are updated with these values (adding new parameters or overriding those already defined).
'''

## ==================================================
##     functions to prepare and/or check input 
## ==================================================

def check_keywords(my_dict,list_mandatory_keywords):

    '''
    check that a dictionary contains all mandatory keywords.
    :param my_dict: dictionary to check and update
    :param list_mandatory_keywords: list of length-2 tuples of the form
    (keyword required, its description). The description is used in case the 
    keyword is missing from mydict (prints an error message including the
    description)
    '''

    # check the mandatory keyword (raise an error if not present)
    for key_word,key_description in list_mandatory_keywords:
       try:
           my_dict[key_word]
       except KeyError:
           raise KeyError("Please specify "+key_description+" for keyword "
                          +key_word)

def check_keywords_and_add_default(my_dict,list_mandatory_keywords,
                                            list_optional_keywords):
    
    '''
    check that a dictionary contains all mandatory keywords and if needed 
    assign default values to optional keywords.
    :param my_dict: dictionary to check and update
    :param list_mandatory_keywords: list of length-2 tuples of the form
    (keyword required, its description). The description is used in case the 
    keyword is missing from mydict (prints an error message including the
    description)
    :param list_optional_keywords: list of length-2 tuples of the form
    (optional keyword, its default value).
    :return the_dict: new dictionary with default keywords assigned.
    '''
    
    # check the mandatory keyword (raise an error if not present)
    for key_word,key_description in list_mandatory_keywords:
       try:
           the_dict[key_word] = my_dict[key_word]
       except KeyError:
           raise KeyError("Please specify "+key_description+" for keyword "
                          +key_word)
            
    # check the other keywords if there are in my_dict, otherwise add them
    # to the_dict with the default value
    for key_word,default_value in list_optional_keywords:
        the_dict[key_word] = my_dict.get(key_word,default_value)
    
    return the_dict

def check_parameter_pk_and_extract_dict(param_pk,name=''):
        
    '''
    check that a pk corresponds to a valid dB object, and extract its
    corresponding dictionary.
    :param param_pk: pk of a stored database object containing the parameters,
    :param name: name of the parameters (for potential error message),
    :return params_dict: dictionary extracted from the object.
    '''
    
    try:
        param_dict = Node.get_subclass_from_pk(param_pk).get_dict()
    except AttributeError, NotExistent:
        raise InputValidationError('pk of '+name+' is not valid')
    
    return param_dict
        

def update_and_store_params(params, pk_keyword, update_dict, pop_list=[]):
        
    '''
    update a ParameterData object indicated by its pk in params, store it and 
    then provides the new pk in params
    :param params: dictionary containing the pk of the ParameterData to update,
    :param pk_keyword: name of the keyword to get the pk of the ParameterData,
    :param update_dict: dictionary to update the ParameterData object stored
    with the pk extracted from params[pk_keyword],
    :param pop_list: list of keywords to take away from the dictionary,
    :return the_params: updated version of params, with the new pk associated to 
    pk_keyword.
    '''
        
    sub_params_dict =  check_parameter_pk_and_extract_dict(params[pk_keyword],
                                                           pk_keyword)
    for keyword in pop_list:
        sub_params_dict.pop(keyword, None)
    
    sub_params_dict.update(update_dict)
    sub_params = ParameterData(dict=sub_params_dict).store()
    
    the_params = params.copy()
    the_params.update({pk_keyword: sub_params.pk})
    
    return the_params

## ==================================================
##     PW workflow 
## ==================================================

class WorkflowPW(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowPW, self).__init__(**kwargs)
    
    def get_pw_parameters(self, ecutwfc, ecutrho, conv_thr, diagonalization,
                          mixing_mode, mixing_beta, occupations, smearing, degauss,
                          additional_control_dict={}, additional_system_dict={},
                          additional_electrons_dict={}):
        
        control_dict= {
                        'calculation': 'scf',
                        'restart_mode': 'from_scratch',
                        'wf_collect': True,
                        }
        control_dict.update(additional_control_dict)

        system_dict= {
                        'ecutwfc': ecutwfc,
                        'ecutrho': ecutrho,
                        'occupations': occupations,
                        'smearing': smearing,
                        'degauss': degauss,
                        }
        system_dict.update(additional_system_dict)

        electrons_dict= {
                        'diagonalization': diagonalization,
                        'mixing_mode': mixing_mode,
                        'mixing_beta': mixing_beta,
                        'conv_thr': conv_thr,
                        }
        electrons_dict.update(additional_electrons_dict)

        parameters = ParameterData(dict={
                        'CONTROL': control_dict,
                        'SYSTEM': system_dict,
                        'ELECTRONS': electrons_dict,
                        })
                        
        return parameters
    
    def get_kpoints(self, kpoints_mesh):
        
        kpoints = KpointsData()    
        kpoints.set_kpoints_mesh(kpoints_mesh)
        
        return kpoints
    
    ## ============================
    ##    PW calculation generator
    ## ============================
    
    def get_pw_calculation(self, pw_params):
        
        # mandatory parameters (existence should have been checked before)
        codename                    = pw_params["pw_codename"]
        pseudo_family               = pw_params["pseudo_family"]
        structure_pk                = pw_params["structure_pk"]
        ecutwfc                     = pw_params["energy_cutoff"]
        kpoints_mesh_1              = pw_params["kpoints_mesh_1"]
        kpoints_mesh_2              = pw_params["kpoints_mesh_2"]
        kpoints_mesh_3              = pw_params["kpoints_mesh_3"]
        num_machines                = pw_params["num_machines"]
        num_mpiprocs_per_machine    = pw_params["num_mpiprocs_per_machine"]
        max_wallclock_seconds       = pw_params["max_wallclock_seconds"]

        # optional parameters (if not provided, default values assigned)
        ecutrho                     = pw_params.get("dual",8)*ecutwfc
        conv_thr                    = pw_params.get("conv_thr",1e-12)
        smearing                    = pw_params.get("smearing",None)
        diagonalization             = pw_params.get("diagonalization","david")
        mixing_mode                 = pw_params.get("mixing_mode","plain")
        mixing_beta                 = pw_params.get("mixing_beta",0.7)
        additional_control_dict     = pw_params.get("CONTROL", {})
        additional_system_dict      = pw_params.get("SYSTEM", {})
        additional_electrons_dict   = pw_params.get("ELECTRONS", {})
        npools                      = pw_params.get("npools", None)
 
        if smearing is None:
            # default behavior, without smearing
            occupations = 'fixed'
            smearing = 'gaussian'
            degauss = 0.
        else:
            # otherwise smearing indicates the kind of smearing applied
            occupations = 'smearing'
            degauss = pw_params.get("degauss",0.)

        structure = StructureData.get_subclass_from_pk(structure_pk)
        kpoints_mesh=[kpoints_mesh_1,kpoints_mesh_2,kpoints_mesh_3]
        
        pw_parameters = self.get_pw_parameters(ecutwfc, ecutrho, conv_thr, 
                          diagonalization, mixing_mode, mixing_beta,
                          occupations, smearing, degauss, additional_control_dict,
                          additional_system_dict, additional_electrons_dict)
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
        
        if (npools is not None) and (npools > 1):
            settings = ParameterData(dict={'cmdline': ['-nk', str(npools)]})
            calc.use_settings(settings)
        
        calc.store_all()
        
        return calc
                
    ## ===============================================
    ##    Workflow steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        self.append_to_report("Checking PW input parameters")
        
        # define the mandatory keywords and the corresponding description to be 
        # printed in case the keyword is missing, for the global input 
        # parameters and the PW parameters
        list_mandatory_keywords_params = [('PW_pk',"the PW parameters (pk of a "
                                           "previously stored ParameterData "
                                           "object)"),
                                          ]
        
        list_mandatory_keywords_pw = [('pw_codename','the PW codename'),
                                      ('structure_pk',"the structure (pk of a previously"
                                                   " stored StructureData object)"),
                                      ('energy_cutoff','the energy cutoff (Ry)'),
                                      ('kpoints_mesh_1',"the number of kpoints in the mesh,"
                                                     " along 1st reciprocal lattice vector"),
                                      ('kpoints_mesh_2',"the number of kpoints in the mesh,"
                                                     " along 2nd reciprocal lattice vector"),
                                      ('kpoints_mesh_3',"the number of kpoints in the mesh,"
                                                     " along 3rd reciprocal lattice vector"),
                                      ('pseudo_family','the pseudopotential family'),
                                      ('num_machines','the number of machines'),
                                      ('num_mpiprocs_per_machine','the number of cores per machine'),
                                      ('max_wallclock_seconds','the max. wall time in seconds'),
                                      ]
        
        # retrieve and check the initial user parameters
        params = self.get_parameters()
        check_keywords(params,list_mandatory_keywords_params)
        
        # PW parameters: retrieve and check
        pw_params = check_parameter_pk_and_extract_dict(params['PW_pk'],
                                                        'PW parameters')
        check_keywords(pw_params, list_mandatory_keywords_pw)

        self.next(self.run_pw)
        
    @Workflow.step
    def run_pw(self):
        
        # retrieve PW parameters
        params = self.get_parameters()
        pw_params = Node.get_subclass_from_pk(params['PW_pk']).get_dict()

        self.append_to_report("Launching PW computation")
            
        # Prepare the PW computation
        pw_calc = self.get_pw_calculation(pw_params)
        # Launch the PW computation
        self.attach_calculation(pw_calc)
        
        self.next(self.final_step)
        
    @Workflow.step   
    def final_step(self):
        
        # Retrieve the PW calculation  
        pw_calc = self.get_step_calculations(self.run_pw)[0]
        
        self.add_result("pw.calc", pw_calc)

        self.append_to_report("PW workflow completed")
                    
        self.next(self.exit)

