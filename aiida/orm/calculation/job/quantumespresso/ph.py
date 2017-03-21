# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin to create a Quantum Espresso ph.x input file.
"""
import os
from aiida.orm.calculation.job import JobCalculation
from aiida.common.exceptions import InputValidationError,ValidationError
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.orm.calculation.job.quantumespresso import get_input_data_text,_lowercase_dict,_uppercase_dict
from aiida.common.exceptions import UniquenessError
from aiida.common.utils import classproperty
from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.remote import RemoteData 
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation 
from aiida.orm.calculation.job.quantumespresso import BasePwCpInputGenerator
from aiida.orm.data.array.kpoints import KpointsData
import numpy

# List of namelists (uppercase) that are allowed to be found in the
# input_data, in the correct order
    
# in restarts, will not copy but use symlinks
_default_symlink_usage = False

class PhCalculation(JobCalculation):
    """
    Phonon code (ph.x) of the Quantum ESPRESSO distribution.
    For more information, refer to http://www.quantum-espresso.org/
    """

    def _init_internal_params(self):
        super(PhCalculation, self)._init_internal_params()

        self._PREFIX = 'aiida'
        self._INPUT_FILE_NAME = 'aiida.in'
        self._OUTPUT_FILE_NAME = 'aiida.out'
        self._OUTPUT_XML_TENSOR_FILE_NAME = 'tensors.xml'
    
        # Default PH output parser provided by AiiDA
        self._default_parser = 'quantumespresso.ph'

        self._compulsory_namelists = ['INPUTPH']

        # Keywords that cannot be set manually, only by the plugin
        self._blocked_keywords = [('INPUTPH', 'outdir'),
                             ('INPUTPH', 'iverbosity'),
                             ('INPUTPH', 'prefix'),
                             ('INPUTPH', 'fildyn'),
                             ('INPUTPH', 'ldisp'),
                             ('INPUTPH', 'nq1'),
                             ('INPUTPH', 'nq2'),
                             ('INPUTPH', 'nq3'),
                             ('INPUTPH', 'qplot'),
                             ]
        
        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'

    @classproperty
    def _OUTPUT_SUBFOLDER(cls):
        return './out/'

    @classproperty
    def _FOLDER_DRHO(cls):
        return 'FILDRHO'

    @classproperty
    def _DRHO_PREFIX(cls):
        return 'drho'

    @classproperty
    def _DRHO_STAR_EXT(cls):
        return 'drho_rot'

    @classproperty
    def _FOLDER_DYNAMICAL_MATRIX(cls):
        return 'DYN_MAT'

    @classproperty
    def _OUTPUT_DYNAMICAL_MATRIX_PREFIX(cls):
        return os.path.join(cls._FOLDER_DYNAMICAL_MATRIX,
                                                      'dynamical-matrix-')
    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the ph class.
        """
        retdict = JobCalculation._use_methods
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
            "qpoints": {
               'valid_types': KpointsData,
               'additional_parameter': None,
               'linkname': 'qpoints',
               'docstring': ("Specify the Qpoints on which to compute phonons"),
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
        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this calculation")

        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []
        
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")
        
        try:
            qpoints = inputdict.pop(self.get_linkname('qpoints'))
        except KeyError:
            raise InputValidationError("No qpoints specified for this calculation")
        if not isinstance(qpoints, KpointsData):
            raise InputValidationError("qpoints is not of type KpointsData")

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
            raise InputValidationError("No parent calculation found, needed to "
                                       "compute phonons")
        # TODO: to be a PwCalculation is not sufficient: it could also be a nscf
        # calculation that is invalid for phonons
        
        if not isinstance(parent_calc_folder, RemoteData):
            raise InputValidationError("parent_calc_folder, if specified,"
                                       "must be of type RemoteData")

        restart_flag = False
        # extract parent calculation
        parent_calcs = parent_calc_folder.get_inputs(node_type=JobCalculation)
        n_parents = len(parent_calcs)
        if n_parents != 1:
            raise UniquenessError("Input RemoteData is child of {} "
                                  "calculation{}, while it should have "
                                  "a single parent".format(n_parents,
                                                "" if n_parents==0 else "s"))
        parent_calc = parent_calcs[0]
        # check that it is a valid parent
        self._check_valid_parent(parent_calc)
        
        if not isinstance(parent_calc, PwCalculation):
            restart_flag = True

        # Also, the parent calculation must be on the same computer
        new_comp = self.get_computer()
        old_comp = parent_calc.get_computer()
        if ( not new_comp.uuid == old_comp.uuid ):
            raise InputValidationError("PhCalculation must be launched on the same computer"
                          " of the parent: {}".format(old_comp.get_name()))

        # put by default, default_parent_output_folder = ./out
        try:
            default_parent_output_folder = parent_calc._OUTPUT_SUBFOLDER
        except AttributeError:
            try:
                default_parent_output_folder = parent_calc._get_output_folder()
            except AttributeError:
                raise InputValidationError("Parent of PhCalculation  does not "
                                           "have a default output subfolder")
        #os.path.join(
        #                   parent_calc.OUTPUT_SUBFOLDER, 
        #                  '{}.save'.format(parent_calc.PREFIX))
        parent_calc_out_subfolder = settings_dict.pop('PARENT_CALC_OUT_SUBFOLDER',
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

        prepare_for_d3 = settings_dict.pop('PREPARE_FOR_D3',False)
        if prepare_for_d3:
            self._blocked_keywords += [('INPUTPH', 'fildrho'),
                                       ('INPUTPH', 'drho_star%open'),
                                       ('INPUTPH', 'drho_star%ext'),
                                       ('INPUTPH', 'drho_star%dir')]
        
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
        input_params['INPUTPH']['outdir'] = self._OUTPUT_SUBFOLDER
        input_params['INPUTPH']['iverbosity'] = 1 # in human language 1=high
        input_params['INPUTPH']['prefix'] = self._PREFIX
        input_params['INPUTPH']['fildyn'] = self._OUTPUT_DYNAMICAL_MATRIX_PREFIX
        if prepare_for_d3:
            input_params['INPUTPH']['fildrho'] = self._DRHO_PREFIX
            input_params['INPUTPH']['drho_star%open'] = True
            input_params['INPUTPH']['drho_star%ext'] = self._DRHO_STAR_EXT
            input_params['INPUTPH']['drho_star%dir'] = self._FOLDER_DRHO
        
        # qpoints part
        try:
            mesh,offset = qpoints.get_kpoints_mesh()
            
            if any([i!=0. for i in offset]):
                raise NotImplementedError("Computation of phonons on a mesh with"
                    " non zero offset is not implemented, at the level of ph.x")
            
            input_params["INPUTPH"]["ldisp"] = True
            input_params["INPUTPH"]["nq1"] = mesh[0]
            input_params["INPUTPH"]["nq2"] = mesh[1]
            input_params["INPUTPH"]["nq3"] = mesh[2]
            
            postpend_text = None
            
        except AttributeError:
            # this is the case where no mesh was set. Maybe it's a list
            try:
                list_of_points = qpoints.get_kpoints(cartesian=True)
            except AttributeError as e:
                # In this case, there are no info on the qpoints at all
                raise InputValidationError("Neither a qpoints mesh or a valid "
                                           "list of qpoints was found in input",
                                           e.message)
            # change to 2pi/a coordinates
            lattice_parameter = numpy.linalg.norm(qpoints.cell[0])
            list_of_points *= lattice_parameter / (2.*numpy.pi)
            # add here the list of point coordinates            
            if len(list_of_points)>1:
                input_params["INPUTPH"]["qplot"] = True
                input_params["INPUTPH"]["ldisp"] = True
                postpend_text = "{}\n".format(len(list_of_points))
                for points in list_of_points:
                    postpend_text += "{}  {}  {}  1\n".format(*points)
                # Note: the weight is fixed to 1, because ph.x calls these 
                # things weights but they are not such. If they are going to 
                # exist with the meaning of weights, they will be supported
            else:
                input_params["INPUTPH"]["ldisp"] = False
                postpend_text = ""
                for points in list_of_points:
                    postpend_text += "{}  {}  {}\n".format(*points)
            
        
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
        
        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)

        # create a folder for the dynamical matrices
        if not restart_flag: # if it is a restart, it will be copied over
            tempfolder.get_subfolder(self._FOLDER_DYNAMICAL_MATRIX,
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
            
            # add list of qpoints if required
            if postpend_text is not None:
                infile.write(postpend_text)
            
            #TODO: write nat_todo
            
        if input_params:
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))
        
        # copy the parent scratch
        symlink = settings_dict.pop('PARENT_FOLDER_SYMLINK',
                                    _default_symlink_usage) # a boolean
        if symlink:
            # I create a symlink to each file/folder in the parent ./out
            tempfolder.get_subfolder(self._OUTPUT_SUBFOLDER, create=True)
            
            remote_symlink_list.append( (parent_calc_folder.get_computer().uuid,
                                         os.path.join(parent_calc_folder.get_remote_path(),
                                                      parent_calc_out_subfolder,
                                                      "*"),
                                         self._OUTPUT_SUBFOLDER
                                         ) )
            
            # I also create a symlink for the ./pseudo folder
            # TODO: suppress this when the recover option of QE will be fixed 
            # (bug when trying to find pseudo file) 
            remote_symlink_list.append((parent_calc_folder.get_computer().uuid,
                                        os.path.join(parent_calc_folder.get_remote_path(),
                                                     self._get_pseudo_folder()),
                                        self._get_pseudo_folder()
                                        ))
            #pass
        else:
            # here I copy the whole folder ./out
            remote_copy_list.append(
                (parent_calc_folder.get_computer().uuid,
                 os.path.join(parent_calc_folder.get_remote_path(),
                              parent_calc_out_subfolder),
                 self._OUTPUT_SUBFOLDER))
            # I also copy the ./pseudo folder
            # TODO: suppress this when the recover option of QE will be fixed 
            # (bug when trying to find pseudo file) 
            remote_copy_list.append(
                (parent_calc_folder.get_computer().uuid,
                 os.path.join(parent_calc_folder.get_remote_path(),
                              self._get_pseudo_folder()),
                        self._get_pseudo_folder()))
            
        
        if restart_flag: # in this case, copy in addition also the dynamical matrices
            if symlink:
                remote_symlink_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                              self._FOLDER_DYNAMICAL_MATRIX),
                     self._FOLDER_DYNAMICAL_MATRIX))

            else:
                # copy the dynamical matrices
                remote_copy_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                              self._FOLDER_DYNAMICAL_MATRIX),
                     '.'))
                # no need to copy the _ph0, since I copied already the whole ./out folder
        
        # here we may create an aiida.EXIT file
        create_exit_file = settings_dict.pop('ONLY_INITIALIZATION',False)
        if create_exit_file:
            exit_filename = tempfolder.get_abs_path(
                             '{}.EXIT'.format(self._PREFIX))
            with open(exit_filename,'w') as f:
                f.write('\n')

        calcinfo = CalcInfo()
        
        calcinfo.uuid = self.uuid
        # Empty command line by default
        cmdline_params = settings_dict.pop('CMDLINE', [])
        
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list
        
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = (list(cmdline_params)
                                   + ["-in", self._INPUT_FILE_NAME])
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]
        
        # Retrieve by default the output file and the xml file
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append(self._FOLDER_DYNAMICAL_MATRIX)
        calcinfo.retrieve_list.append(  
                os.path.join(self._OUTPUT_SUBFOLDER,
                             '_ph0',
                             '{}.phsave'.format(self._PREFIX),
                             self._OUTPUT_XML_TENSOR_FILE_NAME))
        
        extra_retrieved = settings_dict.pop('ADDITIONAL_RETRIEVE_LIST', [])
        for extra in extra_retrieved:
            calcinfo.retrieve_list.append( extra )
        
        if settings_dict:
            raise InputValidationError("The following keys have been found in "
                "the settings input node, but were not understood: {}".format(
                ",".join(settings_dict.keys())))
        
        return calcinfo
        
    def _check_valid_parent(self,calc):
        """
        Check that calc is a valid parent for a PhCalculation.
        It can be a PwCalculation, PhCalculation, or (if the class exists) a 
        CopyonlyCalculation
        :todo: maybe assume that CopyonlyCalculation class always exists?
        """

        try:
            from aiida.orm.calculation.job.simpleplugins.copyonly import CopyonlyCalculation
            if ( ( (not isinstance(calc,PwCalculation)) 
                            and (not isinstance(calc,PhCalculation)) )
                            and (not isinstance(calc,CopyonlyCalculation)) ):
                raise ValueError("Parent calculation must be a PwCalculation, a "
                                 "PhCalculation or a CopyonlyCalculation")
        except ImportError:
            if ( (not isinstance(calc,PwCalculation)) 
                            and (not isinstance(calc,PhCalculation)) ):
                raise ValueError("Parent calculation must be a PwCalculation or "
                                 "a PhCalculation")
    
    def use_parent_calculation(self,calc):
        """
        Set the parent calculation of Ph, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData to PhCalculation 
        """
        from aiida.common.exceptions import NotExistent
        
        self._check_valid_parent(calc)
        
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
        input_remote = self.get_inputs(node_type=RemoteData)
        if input_remote:
            raise ValidationError("Cannot set several parent calculation to a "
                                  "ph calculation")

        self.use_parent_folder(remotedata)
            
    def _get_pseudo_folder(self):
        """
        Get the calculation-specific pseudo folder (relative path).
        Default given by BasePwCpInputGenerator._PSEUDO_SUBFOLDER
        """
        return self.get_attr("pseudo_folder",
                             BasePwCpInputGenerator._PSEUDO_SUBFOLDER)

    def _set_pseudo_folder(self,pseudo_folder):
        """
        Get the calculation-specific pseudo folder.
        
        :param pseudo_folder: a string with the relative path (in the remote 
        directory) to the pseudo folder
        """
        self.set_attr("pseudo_folder", unicode(pseudo_folder))
    
    def create_restart(self,force_restart=False,
                       parent_folder_symlink=_default_symlink_usage):
        """
        Function to restart a calculation that was not completed before 
        (like max walltime reached...) i.e. not to restart a FAILED calculation.
        Returns a calculation c2, with all links prepared but not stored in DB.
        To submit it simply:
        c2.store_all()
        c2.submit()
        
        :param bool force_restart: restart also if parent is not in FINISHED 
        state (e.g. FAILED, IMPORTED, etc.). Default=False.
        """
        from aiida.common.datastructures import calc_states
        if self.get_state() != calc_states.FINISHED:
            if force_restart:
                pass
            else:
                raise InputValidationError("Calculation to be restarted must be "
                            "in the {} state. Otherwise, use the force_restart "
                            "flag".format(calc_states.FINISHED) )
        
        inp = self.get_inputs_dict()
        code = inp['code']
        qpoints = inp['qpoints']
        
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
        
        #if 'Restart' in c2.label:
        #    # increment by 1 the number of restart already done
        #    l = c2.label.split('Restart')
        #    try:
        #        num_restart = int(l[1].split('of')[0])
        #    except ValueError:
        #        num_restart = 1
        #    labelstring = "{0} Restart {1} of ph.x".format(l[0],num_restart+1)
        #else:
        #    labelstring = c2.label + " Restart of ph.x"
        if not 'Restart' in c2.label:
            labelstring = c2.label + " Restart of {} {}.".format(
                                        self.__class__.__name__,self.pk)
        else:
            labelstring = " Restart of {} {}.".format(self.__class__.__name__,self.pk)
        c2.label = labelstring.lstrip()
        
        # set the parameters, code and q-points
        c2.use_parameters(inp_dict)
        c2.use_code(code)
        c2.use_qpoints(qpoints)
        
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
    
