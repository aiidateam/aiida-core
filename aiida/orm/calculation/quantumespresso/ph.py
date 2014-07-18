# -*- coding: utf-8 -*-
"""
Plugin to create a Quantum Espresso ph.x input file.
"""
import os
from aiida.orm import Calculation, DataFactory, CalculationFactory
from aiida.common.exceptions import InputValidationError,ValidationError
from aiida.common.datastructures import CalcInfo
from aiida.orm.calculation.quantumespresso import get_input_data_text,_lowercase_dict,_uppercase_dict
from aiida.common.exceptions import UniquenessError
from aiida.common.utils import classproperty

from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.remote import RemoteData 
from aiida.orm.data.folder import FolderData 
from aiida.orm.calculation.quantumespresso.pw import PwCalculation 

# List of namelists (uppercase) that are allowed to be found in the
# input_data, in the correct order

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

    
# in restarts, will not copy but use symlinks
_default_symlink_usage = False

class PhCalculation(Calculation):
    """
    Phonon code (ph.x) of the Quantum ESPRESSO distribution.
    For more information, refer to http://www.quantum-espresso.org/
    """

    def _init_internal_params(self):
        super(PhCalculation, self)._init_internal_params()

        self.OUTPUT_SUBFOLDER = './out/'
        self.PREFIX = 'aiida'
        self.INPUT_FILE_NAME = 'aiida.in'
        self.OUTPUT_FILE_NAME = 'aiida.out'
        #OUTPUT_XML_FILE_NAME = 'data-file.xml'
        self.OUTPUT_XML_TENSOR_FILE_NAME = 'tensors.xml'
        #FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX = 'DYN_MAT'
        #OUTPUT_DYNAMICAL_MATRIX_PREFIX = os.path.join(FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX,
        #                                              'dynamical-matrix-')
    
        # Default PW output parser provided by AiiDA
        self._default_parser = 'quantumespresso.ph'

        self._compulsory_namelists = ['INPUTPH']

        # Keywords that cannot be set manually, only by the plugin
        self._blocked_keywords = [('INPUTPH', 'outdir'),
                             ('INPUTPH', 'iverbosity'),
                             ('INPUTPH', 'prefix'),
                             ('INPUTPH', 'fildyn'),
                             ]

    @classproperty
    def FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX(cls):
        return 'DYN_MAT'

    @classproperty
    def OUTPUT_DYNAMICAL_MATRIX_PREFIX(cls):
        return os.path.join(cls.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX,
                                                      'dynamical-matrix-')
    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the ph class.
        """
        retdict = Calculation._use_methods
        retdict.update({
            "settings": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'settings',
               'docstring': "Use an additional node for special settings",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': ("Use a node that specifies the input parameters "
                             "for the namelists"),
               },
            "parent_folder": {
               'valid_types': RemoteData,
               'additional_parameter': None,
               'linkname': 'parent_calc_folder',
               'docstring': ("Use a remote folder as parent folder (for "
                             "restarts and similar"),
               },
            })
        return retdict
    
    def _prepare_for_submission(self,tempfolder,inputdict):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """
#        from aiida.common.utils import get_unique_filename, get_suggestion

        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []
        
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")
        
        # Settings can be undefined, and defaults to an empty dictionary.
        # They will be used for any input that doen't fit elsewhere.
        settings = inputdict.pop(self.get_linkname('settings'),None)
        if settings is None:
            settings_dict = {}
        else:
            if not isinstance(settings,  ParameterData):
                raise InputValidationError("settings, if specified, must be of "
                                           "type ParameterData")
            # Settings converted to uppercase
            settings_dict = _uppercase_dict(settings.get_dict(),
                                            dict_name='settings')

        parent_calc_folder = inputdict.pop(self.get_linkname('parent_folder'),None)
        if parent_calc_folder is None:
            raise InputValidationError("No parent calculation found, needed to compute phonons")
        # TODO: to be a PwCalculation is not sufficient: it could also be a nscf calculation that is invalid for phonons
        
        if not isinstance(parent_calc_folder, RemoteData):
            raise InputValidationError("parent_calc_folder, if specified,"
                    "must be of type RemoteData")

        restart_flag = False
        parent_calcs = parent_calc_folder.get_inputs(type=PwCalculation)
        if not parent_calcs:
            parent_calcs = parent_calc_folder.get_inputs(type=PhCalculation)
            restart_flag = True
        if len(parent_calcs) != 1:
            raise UniquenessError("Input RemoteData is child of many Calcs, or "
                                  "does not have a parent at all")
        parent_calc = parent_calcs[0]


        # Also, the parent calculation must be on the same computer
        new_comp = self.get_computer()
        old_comp = parent_calc.get_computer()
        if ( not new_comp.uuid == old_comp.uuid ):
            raise InputValidationError("PhCalculation must be launched on the same computer"
                          " of the parent: {}".format(old_comp.get_name()))

        # put by default, default_parent_output_folder = ./out
        default_parent_output_folder = parent_calc.OUTPUT_SUBFOLDER
        #os.path.join(
        #                   parent_calc.OUTPUT_SUBFOLDER, 
        #                  '{}.save'.format(parent_calc.PREFIX))
        parent_calc_out_subfolder = settings_dict.pop('parent_calc_out_subfolder',
                                                      default_parent_output_folder)      

        # Here, there should be no other inputs
        if inputdict:
            raise InputValidationError("The following input data nodes are "
                "unrecognized: {}".format(inputdict.keys()))

        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################

        # I put the first-level keys as uppercase (i.e., namelist and card names)
        # and the second-level keys as lowercase
        # (deeper levels are unchanged)
        input_params = _uppercase_dict(parameters.get_dict(),
                                       dict_name='parameters')
        input_params = {k: _lowercase_dict(v, dict_name=k) 
                        for k, v in input_params.iteritems()}
        
        # I remove unwanted elements (for the moment, instead, I stop; to change when
        # we setup a reasonable logging)
        for nl, flag in self._blocked_keywords:
            if nl in input_params:
                if flag in input_params[nl]:
                    raise InputValidationError(
                        "You cannot specify explicitly the '{}' flag in the '{}' "
                        "namelist or card.".format(flag, nl))
        
        # Set some variables (look out at the case! NAMELISTS should be uppercase,
        # internal flag names must be lowercase)
        if 'INPUTPH' not in input_params:
            raise InputValidationError("No namelist INPUTPH found in input") # I cannot decide what to do in the calculation
        input_params['INPUTPH']['outdir'] = self.OUTPUT_SUBFOLDER
        input_params['INPUTPH']['iverbosity'] = 1 # in human language 1=high
        input_params['INPUTPH']['prefix'] = self.PREFIX
        input_params['INPUTPH']['fildyn'] = self.OUTPUT_DYNAMICAL_MATRIX_PREFIX

        # =================== NAMELISTS ========================
        
        # customized namelists, otherwise not present in the distributed ph code
        try:
            namelists_toprint = settings_dict.pop('NAMELISTS')
            if not isinstance(namelists_toprint, list):
                raise InputValidationError(
                    "The 'NAMELISTS' value, if specified in the settings input "
                    "node, must be a list of strings")
        except KeyError: # list of namelists not specified in the settings; do automatic detection
            namelists_toprint = self._compulsory_namelists
        
        input_filename = tempfolder.get_abs_path(self.INPUT_FILE_NAME)

        # create a folder for the dynamical matrices
        if not restart_flag: # if it is a restart, it will be copied over
            tempfolder.get_subfolder(self.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX,
                                 create=True)
        
        with open(input_filename,'w') as infile:
            infile.write('AiiDA calculation\n')
            for namelist_name in namelists_toprint:
                infile.write("&{0}\n".format(namelist_name))
                # namelist content; set to {} if not present, so that we leave an 
                # empty namelist
                namelist = input_params.pop(namelist_name,{})
                for k, v in sorted(namelist.iteritems()):
                    infile.write(get_input_data_text(k,v))
                infile.write("/\n")

            #TODO: write manual q points
            #TODO: write nat_todo

        if input_params:
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))
        
        # copy the parent scratch
        symlink = settings_dict.pop('PARENT_FOLDER_SYMLINK',_default_symlink_usage) # a boolean
        if symlink:
            # I create a symlink to the whole parent ./out
            # TODO: it would be better to do a symlink of ./out/* -> ./out/
            # tempfolder.get_subfolder(self.OUTPUT_SUBFOLDER, create=True)
            remote_symlink_list.append(
                        (parent_calc_folder.get_computer().uuid,
                         os.path.join(parent_calc_folder.get_remote_path(),
                                     parent_calc_out_subfolder),
                         self.OUTPUT_SUBFOLDER))
#             remote_symlink_list.append(
#                 (parent_calc_folder.get_computer().uuid,
#                  os.path.join(parent_calc_folder.get_remote_path(),
#                               parent_calc_out_subfolder),
#                  #os.path.join(self.OUTPUT_SUBFOLDER,'{}.save'.format(self.PREFIX))
#                  self.OUTPUT_SUBFOLDER
#                  ))
            pass
        else:
            # here I copy the whole folder ./out
            remote_copy_list.append(
                (parent_calc_folder.get_computer().uuid,
                 os.path.join(parent_calc_folder.get_remote_path(),
                              parent_calc_out_subfolder),
                 self.OUTPUT_SUBFOLDER))
        
        if restart_flag: # in this case, copy in addition also the dynamical matrices
            if symlink:
                remote_symlink_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                              self.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX),
                     self.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX))
#                 # and here I copy ./out/_ph0 # copied already by ./out
#                 remote_symlink_list.append(
#                         (parent_calc_folder.get_computer().uuid,
#                          os.path.join(parent_calc_folder.get_remote_path(),
#                                       self.OUTPUT_SUBFOLDER,'_ph0'),
#                          os.path.join(self.OUTPUT_SUBFOLDER,'_ph0')
#                          ))

            else:
                # copy the dynamical matrices
                remote_copy_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                              self.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX),
                     '.'))
                # no need to copy the _ph0, since I copied already the whole ./out folder
        
        calcinfo = CalcInfo()
        
        calcinfo.uuid = self.uuid
        # Empty command line by default
        cmdline_params = settings_dict.pop('CMDLINE', [])
        calcinfo.cmdline_params = (list(cmdline_params)
                                   + ["-in", self.INPUT_FILE_NAME])
        
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list
        #calcinfo.stdin_name = self.INPUT_FILE_NAME
        calcinfo.stdout_name = self.OUTPUT_FILE_NAME
        
        # Retrieve by default the output file and the xml file
        calcinfo.retrieve_list = []        
        calcinfo.retrieve_list.append(self.OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append(self.FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX)
        calcinfo.retrieve_list.append(  
                os.path.join(self.OUTPUT_SUBFOLDER,
                             '_ph0',
                             '{}.phsave'.format(self.PREFIX),
                             self.OUTPUT_XML_TENSOR_FILE_NAME))
        
        if settings_dict:
            raise InputValidationError("The following keys have been found in "
                "the settings input node, but were not understood: {}".format(
                ",".join(settings_dict.keys())))
        
        return calcinfo
        
    def set_parent_calc(self,calc):
        """
        Set the parent calculation of Ph, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData to PhCalculation 
        """
        from aiida.common.exceptions import NotExistent
        
        if not isinstance(calc,PwCalculation):
            raise ValueError("Parent calculation must be a PwCalculation")
        
        remotedatas = calc.get_outputs(type=RemoteData)
        if not remotedatas:
            raise NotExistent("No output remotedata found in "
                                  "the parent")
        if len(remotedatas) != 1:
            raise UniquenessError("More than one output remotedata found in "
                                  "the parent")
        remotedata = remotedatas[0]
        
        self._set_parent_remotedata(remotedata)

    def _set_parent_remotedata(self,remotedata):
        """
        Used to set a parent remotefolder in the restart of ph.
        """
        if not isinstance(remotedata,RemoteData):
            raise ValueError('remotedata must be a RemoteData')
        
        # complain if another remotedata is already found
        input_remote = self.get_inputs(type=RemoteData)
        if input_remote:
            raise ValidationError("Cannot set several parent calculation to a "
                                  "ph calculation")

        self.use_parent_folder(remotedata)
        
    def get_parent_calc(self):
        """
        Return the parent calculation of Ph, 
        from which it will inherit the outputsubfolder.
        Raise NotExistent if no parent_calculation was set.
        """       
        from aiida.common.exceptions import NotExistent
        
        try:
            parentremotedata = self.get_inputs_dict()[
                self._use_methods['parent_folder']['linkname']]
        except KeyError:
            raise NotExistent("No parent was set.")
        
        parentcalcs = parentremotedata.get_inputs(type=PwCalculation)
        if not parentcalcs: # case of restart
            parentcalcs = parentremotedata.get_inputs(type=PhCalculation)

        if len(parentcalcs) > 1:
            raise UniquenessError("More than one input calculation found")
        if parentcalcs:
            return parentcalcs[0]
        else:
            raise NotExistent("No valid parent calculation was found")
            
    def create_restart(self,restart_if_failed=False,
                       parent_folder_symlink=_default_symlink_usage):
        """
        Function to restart a calculation that was not completed before 
        (like max walltime reached...) i.e. not to restart a FAILED calculation.
        Returns a calculation c2, with all links prepared but not stored in DB.
        To submit it simply:
        c2.store_all()
        c2.submit()
        
        :param bool restart_if_failed: restart if parent is failed. default False
        """
        from aiida.common.datastructures import calc_states
        if self.get_state() != calc_states.FINISHED:
            if restart_if_failed:
                pass
            else:
                raise InputValidationError("Calculation to be restarted must be "
                            "in the {} state".format(calc_states.FINISHED) )
        
        inp = self.get_inputs_dict()
        code = inp['code']
        
        old_inp_dict = inp['parameters'].get_dict()
        # add the restart flag
        old_inp_dict['INPUTPH']['recover'] = True
        inp_dict = ParameterData(dict=old_inp_dict) 
        
        remote_folders = self.get_outputs(type=RemoteData)
        if len(remote_folders)!=1:
            raise InputValidationError("More than one output RemoteData found "
                                       "in calculation {}".format(self.pk))
        remote_folder = remote_folders[0]
        
        c2 = self.copy()
        
        labelstring = c2.label + " Restart of ph.x."
        c2.label = labelstring.lstrip()
        
        # set the 
        c2.use_parameters(inp_dict)
        c2.use_code(code)
        
        # settings will use the logic for the usage of symlinks
        try:
            old_settings_dict = inp['settings'].get_dict()
        except KeyError:
            old_settings_dict = {}
        if parent_folder_symlink:
            old_settings_dict['PARENT_FOLDER_SYMLINK'] = True
            
        if old_settings_dict: # if not empty dictionary
            settings = ParameterData(dict=old_settings_dict)
            c2.use_settings(settings)
        
        c2._set_parent_remotedata( remote_folder )
        return c2
    
