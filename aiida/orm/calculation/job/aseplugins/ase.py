# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.structure import StructureData
from aiida.common.utils import classproperty
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.orm.data.array.kpoints import KpointsData
from aiida import get_file_header

class AseCalculation(JobCalculation):
    """
    A generic plugin for calculations based on the ASE calculators.
    
    Requirement: the node should be able to import ase
    """
    
    def _init_internal_params(self):
        super(AseCalculation, self)._init_internal_params()
        
        self._INPUT_FILE_NAME = 'aiida_script.py'
        self._OUTPUT_FILE_NAME = 'results.json'
        self._input_aseatoms = "aiida_atoms.traj"
        self._output_aseatoms = "aiida_out_atoms.traj"
        self._default_parser = "ase"
        self._TXT_OUTPUT_FILE_NAME = 'aiida.out'
    
    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the namelists class.
        """
        retdict = JobCalculation._use_methods
        retdict.update({
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': ("Use a node that specifies the input parameters "
                             "for the namelists"),
               },
            "structure": {
               'valid_types': StructureData,
               'additional_parameter': None,
               'linkname': 'structure',
               'docstring': "Use a node for the structure",
               },
            "settings": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'settings',
               'docstring': ("Use a node that specifies the extra information "
                             "to be used by the calculation"),
               },
            "kpoints": {
               'valid_types': KpointsData,
               'additional_parameter': None,
               'linkname': 'kpoints',
               'docstring': ("Use a node that specifies the kpoints"),
               },
            })
        return retdict
    
    def _prepare_for_submission(self,tempfolder, inputdict):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """
        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this "
                                       "calculation")

        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this "
                                       "calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type "
                                       "ParameterData")
        
        try:
            structure = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("No structure specified for this "
                                       "calculation")
        if not isinstance(structure,StructureData):
            raise InputValidationError("structure node is not of type"
                                       "StructureData")
        
        try:
            settings = inputdict.pop(self.get_linkname('settings'),None)
        except KeyError:
            pass
        if settings is not None:
            if not isinstance(parameters, ParameterData):
                raise InputValidationError("parameters is not of type "
                                           "ParameterData")
        
        try:
            kpoints = inputdict.pop(self.get_linkname('kpoints'),None)
        except KeyError:
            pass
        if kpoints is not None:
            if not isinstance(kpoints, KpointsData):
                raise InputValidationError("kpoints is not of type KpointsData")
        
        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################
        
        # default atom getter: I will always retrieve the total energy at least
        default_atoms_getters = [ ["total_energy",""] ] 
        
        # ================================
        
        # save the structure in ase format
        atoms = structure.get_ase()
        atoms.write(tempfolder.get_abs_path(self._input_aseatoms))
        
        # ================== prepare the arguments of functions ================
        
        parameters_dict = parameters.get_dict()
        settings_dict = settings.get_dict() if settings is not None else {}
        
        # ==================== fix the args of the optimizer
        
        optimizer = parameters_dict.pop("optimizer",None)
        if optimizer is not None:
            # Validation
            if not isinstance(optimizer,dict):
                raise InputValidationError("optimizer key must contain a dictionary")
            # get the name of the optimizer
            optimizer_name = optimizer.pop("name",None)
            if optimizer_name is None:
                raise InputValidationError("Don't have access to the optimizer name")
            
            # prepare the arguments to be passed to the optimizer class
            optimizer_argsstr = "atoms, " + convert_the_args(optimizer.pop("args",[]))
            
            # prepare the arguments to be passed to optimizer.run()
            optimizer_runargsstr = convert_the_args(optimizer.pop("run_args",[]))
            
            # prepare the import string
            optimizer_import_string = get_optimizer_impstr(optimizer_name)
            
        # ================= determine the calculator name and its import ====
        
        calculator = parameters_dict.pop("calculator",{})
        calculator_import_string = get_calculator_impstr(calculator.pop("name",None))
        
        # =================== prepare the arguments for the calculator call
        
        read_calc_args = calculator.pop("args",[])
        #calc_args = calculator.pop("args",None)
        if read_calc_args is None:
            calc_argsstr = ""
        else:
            # transform a in "a" if a is a string (needed for formatting)
            calc_args = {}
            for k,v in read_calc_args.iteritems():
                if isinstance(v, basestring):
                    the_v = '"{}"'.format(v)
                else:
                    the_v = v
                calc_args[k] = the_v
            
            def return_a_function(v):
                try:
                    has_magic = "@function" in v.keys()
                except AttributeError:
                    has_magic = False
                
                if has_magic:
                    
                    args_dict = {}
                    for k2,v2 in v['args'].iteritems():
                        if isinstance(v2,basestring):
                            the_v = '"{}"'.format(v2)
                        else:
                            the_v = v2
                        args_dict[k2] = the_v
                    
                    v2 = "{}({})".format(v['@function'],
                                         ", ".join(["{}={}".format(k_,v_) 
                                            for k_,v_ in args_dict.iteritems()]))
                    return v2
                else:
                    return v
            
            tmp_list = [ "{}={}".format(k,return_a_function(v)) 
                         for k,v in calc_args.iteritems() ]
            
            calc_argsstr = ", ".join( tmp_list )

            # add kpoints if present
            if kpoints:
                #TODO: here only the mesh is supported
                # maybe kpoint lists are supported as well in ASE calculators
                try:
                    mesh = kpoints.get_kpoints_mesh()[0]
                except AttributeError:
                    raise InputValidationError("Coudn't find a mesh of kpoints"
                                               " in the KpointsData")
                calc_argsstr = ", ".join( [calc_argsstr] + ["kpts=({},{},{})".format( *mesh )] )
                        
        # =============== prepare the methods of atoms.get(), to save results
        
        atoms_getters = default_atoms_getters + convert_the_getters( parameters_dict.pop("atoms_getters",[]) )
        
        # =============== prepare the methods of calculator.get(), to save results
        
        calculator_getters = convert_the_getters( parameters_dict.pop("calculator_getters",[]) )
        
        # ===================== build the strings with the module imports
        
        all_imports = ["import ase", 'import ase.io', "import json",
                       "import numpy", calculator_import_string]
        
        if optimizer is not None:
            all_imports.append(optimizer_import_string)

        try:
            if "PW" in calc_args['mode'].values():
                all_imports.append("from gpaw import PW")
        except KeyError:
            pass
        
        extra_imports = parameters_dict.pop("extra_imports",[])
        for i in extra_imports:
            if isinstance(i,basestring):
                all_imports.append("import {}".format(i))
            elif isinstance(i,(list,tuple)):
                if not all( [isinstance(j,basestring) for j in i] ):
                    raise ValueError("extra import must contain strings")
                if len(i)==2:
                    all_imports.append("from {} import {}".format(*i))
                elif len(i)==3:
                    all_imports.append("from {} import {} as {}".format(*i))
                else:
                    raise ValueError("format for extra imports not recognized")
            else:
                raise ValueError("format for extra imports not recognized")
        
        if self.get_withmpi():
            all_imports.append( "from ase.parallel import paropen" )
        
        all_imports_string = "\n".join(all_imports) + "\n"
        
        # =================== prepare the python script ========================
        
        input_txt = ""
        input_txt += get_file_header()
        input_txt += "# calculation pk: {}\n".format(self.pk)
        input_txt += "\n"
        input_txt += all_imports_string
        input_txt += "\n"
        
        pre_lines = parameters_dict.pop("pre_lines",None)
        if pre_lines is not None:
            if not isinstance(pre_lines,(list,tuple)):
                raise ValueError("Prelines must be a list of strings")
            if not all( [isinstance(_,basestring) for _ in pre_lines] ):
                raise ValueError("Prelines must be a list of strings")
            input_txt += "\n".join(pre_lines) + "\n\n"
        
        input_txt += "atoms = ase.io.read('{}')\n".format(self._input_aseatoms)
        input_txt += "\n"
        input_txt += "calculator = custom_calculator({})\n".format(calc_argsstr)
        input_txt += "atoms.set_calculator(calculator)\n"
        input_txt += "\n"
        
        if optimizer is not None:
            # here block the trajectory file name: trajectory = 'aiida.traj'
            input_txt += "optimizer = custom_optimizer({})\n".format(optimizer_argsstr)
            input_txt += "optimizer.run({})\n".format(optimizer_runargsstr)
            input_txt += "\n"
        
        # now dump / calculate the results
        input_txt += "results = {}\n"
        for getter,getter_args in atoms_getters:
            input_txt += "results['{}'] = atoms.get_{}({})\n".format(getter,
                                                                     getter,
                                                                     getter_args)
        input_txt += "\n"
        
        for getter,getter_args in calculator_getters:
            input_txt += "results['{}'] = calculator.get_{}({})\n".format(getter,
                                                                          getter,
                                                                          getter_args) 
        input_txt += "\n"
        
        # Convert to lists
        input_txt += "for k,v in results.iteritems():\n"
        input_txt += "    if isinstance(results[k],(numpy.matrix,numpy.ndarray)):\n"
        input_txt += "        results[k] = results[k].tolist()\n"
        
        input_txt += "\n"
        
        post_lines = parameters_dict.pop("post_lines",None)
        if post_lines is not None:
            if not isinstance(post_lines,(list,tuple)):
                raise ValueError("Postlines must be a list of strings")
            if not all( [isinstance(_,basestring) for _ in post_lines] ):
                raise ValueError("Postlines must be a list of strings")
            input_txt += "\n".join(post_lines) + "\n\n"

        # Dump results to file        
        right_open = "paropen" if self.get_withmpi() else "open"
        input_txt += "with {}('{}', 'w') as f:\n".format(right_open, self._OUTPUT_FILE_NAME)
        input_txt += "    json.dump(results,f)"
        input_txt += "\n"
        
        # Dump trajectory if present
        if optimizer is not None:
            input_txt += "atoms.write('{}')\n".format(self._output_aseatoms)
            input_txt += "\n"
        
        # write all the input script to a file
        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
        with open(input_filename,'w') as infile:
            infile.write(input_txt)
            
        # ============================ calcinfo ================================
        
        # TODO: look at the qmmm infoL: it might be necessary to put
        # some singlefiles in the directory.
        # right now it has to be taken care in the pre_lines
        
        local_copy_list = []
        remote_copy_list = [] 
        additional_retrieve_list = settings_dict.pop("ADDITIONAL_RETRIEVE_LIST",[])
        
        calcinfo = CalcInfo()
        
        calcinfo.uuid = self.uuid
        # Empty command line by default
        # calcinfo.cmdline_params = settings_dict.pop('CMDLINE', [])
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = [self._INPUT_FILE_NAME]
        #calcinfo.stdin_name = self._INPUT_FILE_NAME
        codeinfo.stdout_name = self._TXT_OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]
        
        # Retrieve files
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append(self._output_aseatoms)
        calcinfo.retrieve_list += additional_retrieve_list
        
        # TODO: I should have two ways of running it: with gpaw-python in parallel
        # and executing python if in serial
        
        return calcinfo

def get_calculator_impstr(calculator_name):
    """
    Returns the import string for the calculator
    """
    if calculator_name.lower() == "gpaw" or calculator_name is None:
        return "from gpaw import GPAW as custom_calculator"
    else:
        possibilities = {"abinit":"abinit.Abinit",
                         "aims":"aims.Aims",
                         "ase_qmmm_manyqm":"AseQmmmManyqm",
                         "castep":"Castep",
                         "dacapo":"Dacapo",
                         "dftb":"Dftb",
                         "eam":"EAM",
                         "elk":"ELK",
                         "emt":"EMT",
                         "exciting":"Exciting",
                         "fleur":"FLEUR",
                         "gaussian":"Gaussian",
                         "gromacs":"Gromacs",
                         "mopac":"Mopac",
                         "morse":"MorsePotential",
                         "nwchem":"NWChem",
                         'siesta':"Siesta",
                         "tip3p":"TIP3P",
                         "turbomole":"Turbomole",
                         "vasp":"Vasp",
                         }
        
        current_val = possibilities.get(calculator_name.lower())
        
        package, class_name = (calculator_name,current_val) if current_val else calculator_name.rsplit('.',1)
        
        return "from ase.calculators.{} import {} as custom_calculator".format(package, class_name)

def get_optimizer_impstr(optimizer_name):
    """
    Returns the import string for the optimizer
    """
    possibilities = {"bfgs":"BFGS",
                     "bfgslinesearch":"BFGSLineSearch",
                     "fire":"FIRE",
                     "goodoldquasinewton":"GoodOldQuasiNewton",
                     "hesslbfgs":"HessLBFGS",
                     "lbfgs":"LBFGS",
                     "lbfgslinesearch":"LBFGSLineSearch",
                     "linelbfgs":"LineLBFGS",
                     "mdmin":"MDMin",
                     "ndpoly":"NDPoly",
                     "quasinewton":"QuasiNewton",
                     "scipyfmin":"SciPyFmin",
                     "scipyfminbfgs":"SciPyFminBFGS",
                     "scipyfmincg":"SciPyFminCG",
                     "scipyfminpowell":"SciPyFminPowell",
                     "scipygradientlessoptimizer":"SciPyGradientlessOptimizer",
                     }
    
    current_val = possibilities.get(optimizer_name.lower())
    
    if current_val:
        return "from ase.optimize import {} as custom_optimizer".format(current_val)
    else:
        package,current_val = optimizer_name.rsplit('.',1)
        return "from ase.optimize.{} import {} as custom_optimizer".format(package,current_val)
        
def convert_the_getters(getters):
    """
    A function used to prepare the arguments of calculator and atoms getter methods
    """
    return_list = []
    for getter in getters:
        
        if isinstance(getter,basestring):
            out_args = ""
            method_name = getter
            
        else:
            method_name, a = getter
            
            out_args = convert_the_args(a)
            
        return_list.append( (method_name, out_args) )
    return return_list

def convert_the_args(raw_args):
    """
    Function used to convert the arguments of methods
    """
    if not raw_args:
        return ""
    if isinstance(raw_args,dict):
        out_args = ", ".join([ "{}={}".format(k,v) for k,v in raw_args.iteritems() ])
        
    elif isinstance(raw_args,(list,tuple)):
        new_list = []
        for x in raw_args:
            if isinstance(x,basestring):
                new_list.append(x)
            elif isinstance(x,dict):
                new_list.append( ", ".join([ "{}={}".format(k,v) for k,v in x.iteritems() ]) )
            else:
                raise ValueError("Error preparing the getters")
        out_args = ", ".join(new_list)
    else:
        raise ValueError("Couldn't recognize list of getters")
    return out_args
