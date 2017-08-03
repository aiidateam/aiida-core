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
Plugin to create a Quantum Espresso neb.x input file.
"""
import os
from aiida.orm.calculation.job import JobCalculation
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.orm.calculation.job.quantumespresso import get_input_data_text,_lowercase_dict,_uppercase_dict
from aiida.common.utils import classproperty
from aiida.orm.data.structure import StructureData
from aiida.orm.data.array.kpoints import KpointsData
from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.singlefile import SinglefileData
from aiida.orm.data.upf import UpfData
from aiida.orm.data.remote import RemoteData 
from aiida.orm.calculation.job.quantumespresso import BasePwCpInputGenerator
import copy


class NebCalculation(BasePwCpInputGenerator,JobCalculation):
    """
    Nudged Elastic Band code (neb.x) of Quantum ESPRESSO distribution
    For more information, refer to http://www.quantum-espresso.org/
    """ 

    # in restarts, will not copy but use symlinks
    _default_symlink_usage = False
    
    def _init_internal_params(self):
        super(NebCalculation, self)._init_internal_params()

        self._PREFIX = 'aiida'
        self._INPUT_FILE_NAME = 'neb.dat'
        self._OUTPUT_FILE_NAME = 'aiida.out'

        # Default NEB output parser provided by AiiDA
        self._default_parser = 'quantumespresso.neb'
                
        self._DEFAULT_INPUT_FILE = 'neb.dat'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'

        self._automatic_namelists = {
            'scf': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
        }

        # Keywords that cannot be set
        self._blocked_keywords = [('CONTROL', 'pseudo_dir'),  # set later
                                  ('CONTROL', 'outdir'),  # set later
                                  ('CONTROL', 'prefix'),  # set later
                                  ('SYSTEM', 'ibrav'),  # set later
                                  ('SYSTEM', 'celldm'),
                                  ('SYSTEM', 'nat'),  # set later
                                  ('SYSTEM', 'ntyp'),  # set later
                                  ('SYSTEM', 'a'), ('SYSTEM', 'b'), ('SYSTEM', 'c'),
                                  ('SYSTEM', 'cosab'), ('SYSTEM', 'cosac'), ('SYSTEM', 'cosbc'),
                                  ]

        _neb_ext_list = ['path','dat','int']

        # I retrieve them all, even if I don't parse all of them
        self._internal_retrieve_list = [ '{}.{}'.format(self._PREFIX, ext) for ext in _neb_ext_list]

        self._use_kpoints = True

    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        """
        retdict = JobCalculation._use_methods

        retdict.update({                
                "settings": {
                    'valid_types': ParameterData,
                    'additional_parameter': None,
                    'linkname': 'settings',
                    'docstring': "Use an additional node for special settings",
                    },
                "first_structure": {
                    'valid_types': StructureData,
                    'additional_parameter': None,
                    'linkname': 'first_structure',
                    'docstring': "Choose the first structure to use",
                    },
                "last_structure": {
                    'valid_types': StructureData,
                    'additional_parameter': None,
                    'linkname': 'last_structure',
                    'docstring': "Choose the last structure to use",
                    },
                "kpoints": {
                    'valid_types': KpointsData,
                    'additional_parameter': None,
                    'linkname': 'kpoints',
                    'docstring': "Use the node defining the kpoint sampling to use",
                    },
                "pw_parameters": {
                    'valid_types': ParameterData,
                    'additional_parameter': None,
                    'linkname': 'pw_parameters',
                    'docstring': ("Use a node that specifies the input parameters "
                                  "for the PW namelists"),
                    },
                "neb_parameters" : {
                    'valid_types': ParameterData,
                    'additional_parameter': None,
                    'linkname': 'neb_parameters',
                    'docstring':("Use a node that specifies the input parameters "
                                 "for the NEB PATH namelist")
                    },      
                "parent_folder": {
                    'valid_types': RemoteData,
                    'additional_parameter': None,
                    'linkname': 'parent_calc_folder',
                    'docstring': ("Use a remote folder as parent folder (for "
                                  "restarts and similar"),
                    },
                "pseudo": {
                    'valid_types': UpfData,
                    'additional_parameter': "kind",
                    'linkname': cls._get_linkname_pseudo,
                    'docstring': ("Use a node for the UPF pseudopotential of one of "
                                  "the elements in the structure. You have to pass "
                                  "an additional parameter ('kind') specifying the "
                                  "name of the structure kind (i.e., the name of "
                                  "the species) for which you want to use this "
                                  "pseudo. You can pass either a string, or a "
                                  "list of strings if more than one kind uses the "
                                  "same pseudo"),
                    },
                "vdw_table": {
                    'valid_types': SinglefileData,
                    'additional_parameter': None,
                    'linkname': 'vdw_table',
                    'docstring': ("Use a Van der Waals kernel table. It should be "
                              "a SinglefileData, with the table provided "
                              "(note that the filename is not checked but it "
                              "should be the name expected by QE."),
                    },
                })
        return retdict

    def _generate_NEBinputdata(self,neb_parameters,settings_dict):
        """ 
        This methods generate the input data for the NEB part of the calculation
        """
        # I put the first-level keys as uppercase (i.e., namelist and card names)
        # and the second-level keys as lowercase
        # (deeper levels are unchanged)
        input_params = _uppercase_dict(neb_parameters.get_dict(),
                                       dict_name='parameters')
        input_params = {k: _lowercase_dict(v, dict_name=k)
                        for k, v in input_params.iteritems()}
        
        # For the neb input there is no blocked keyword
        
        # Create an empty dictionary for the compulsory namelist 'PATH'
        # if not present
        if 'PATH' not in input_params:
            input_params['PATH'] = {}

        # In case of climbing image, we need the corresponding card
        climbing_image = False
        if input_params['PATH'].get('ci_scheme','no-ci').lower()  in ['manual']:
            climbing_image = True
            try: 
                climbing_image_list = settings_dict.pop("CLIMBING_IMAGES")
            except KeyError:
                raise InputValidationError("No climbing image specified for this calculation")
            if not isinstance(climbing_image_list, list):
                raise InputValidationError("Climbing images should be provided as a list")
            if [ i  for i in climbing_image_list if i<2 or i >= input_params['PATH'].get('num_of_images',2)]:
                raise InputValidationError("The climbing images should be in the range between the first "
                                           "and the last image")

            climbing_image_card = "CLIMBING_IMAGES\n"
            climbing_image_card += ", ".join([str(_) for _ in climbing_image_list]) + "\n"
 

        inputfile = ""    
        inputfile += "&PATH\n"
        # namelist content; set to {} if not present, so that we leave an 
        # empty namelist
        namelist = input_params.pop('PATH', {})
        for k, v in sorted(namelist.iteritems()):
            inputfile += get_input_data_text(k, v)
        inputfile += "/\n"

        # Write cards now
        if climbing_image:
            inputfile += climbing_image_card

        if input_params:
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))

        return inputfile

    def _prepare_for_submission(self,tempfolder,inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """
        import numpy as np

        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this calculation")
        
        try:
            pw_parameters = inputdict.pop(self.get_linkname('pw_parameters'))
        except KeyError:
            raise InputValidationError("No PW parameters specified for this calculation")
        if not isinstance(pw_parameters, ParameterData):
            raise InputValidationError("PW parameters is not of type ParameterData")

        try:
            neb_parameters = inputdict.pop(self.get_linkname('neb_parameters'))
        except KeyError:
            raise InputValidationError("No NEB parameters specified for this calculation")
        if not isinstance(neb_parameters, ParameterData):
            raise InputValidationError("NEB parameters is not of type ParameterData")

        try:
            first_structure = inputdict.pop(self.get_linkname('first_structure'))
        except KeyError:
            raise InputValidationError("No initial structure specified for this calculation")
        if not isinstance(first_structure, StructureData):
            raise InputValidationError("Initial structure is not of type StructureData")

        try:
            last_structure = inputdict.pop(self.get_linkname('last_structure'))
        except KeyError:
            raise InputValidationError("No final structure specified for this calculation")
        if not isinstance(last_structure, StructureData):
            raise InputValidationError("Final structure is not of type StructureData")

        try:
            kpoints = inputdict.pop(self.get_linkname('kpoints'))
        except KeyError:
            raise InputValidationError("No kpoints specified for this calculation")
        if not isinstance(kpoints, KpointsData):
            raise InputValidationError("kpoints is not of type KpointsData")
        
        # Settings can be undefined, and defaults to an empty dictionary
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

        pseudos = {}
        # I create here a dictionary that associates each kind name to a pseudo
        for link in inputdict.keys():
            if link.startswith(self._get_linkname_pseudo_prefix()):
                kindstring = link[len(self._get_linkname_pseudo_prefix()):]
                kinds = kindstring.split('_')
                the_pseudo = inputdict.pop(link)
                if not isinstance(the_pseudo, UpfData):
                    raise InputValidationError("Pseudo for kind(s) {} is not of "
                                               "type UpfData".format(",".join(kinds)))
                for kind in kinds:
                    if kind in pseudos:
                        raise InputValidationError("Pseudo for kind {} passed "
                                                   "more than one time".format(kind))
                    pseudos[kind] = the_pseudo

        parent_calc_folder = inputdict.pop(self.get_linkname('parent_folder'), None)
        if parent_calc_folder is not None:
            if not isinstance(parent_calc_folder, RemoteData):
                raise InputValidationError("parent_calc_folder, if specified, "
                                           "must be of type RemoteData")

        vdw_table = inputdict.pop(self.get_linkname('vdw_table'), None)
        if vdw_table is not None:
            if not isinstance(vdw_table, SinglefileData):
                raise InputValidationError("vdw_table, if specified, "
                                           "must be of type SinglefileData")            

        # Here, there should be no more parameters...
        if inputdict:
            raise InputValidationError("The following input data nodes are "
                                       "unrecognized: {}".format(inputdict.keys()))

        # Check that the first and last image have the same cell
        if abs(np.array(first_structure.cell)-
               np.array(last_structure.cell)).max() > 1.e-4:
            raise InputValidationError("Different cell in the fist and last image")

        # Check that the first and last image have the same number of sites
        if len(first_structure.sites) != len(last_structure.sites):
            raise InputValidationError("Different number of sites in the fist and last image")

        # Check that sites in the initial and final structure have the same kinds
        if not first_structure.get_site_kindnames() == last_structure.get_site_kindnames():
            raise InputValidationError("Mismatch between the kind names and/or oder between "
                                       "the first and final image")

        # Check structure, get species, check peudos
        kindnames = [k.name for k in first_structure.kinds]
        if set(kindnames) != set(pseudos.keys()):
            err_msg = ("Mismatch between the defined pseudos and the list of "
                       "kinds of the structure. Pseudos: {}; kinds: {}".format(
                ",".join(pseudos.keys()), ",".join(list(kindnames))))
            raise InputValidationError(err_msg)

        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################
        # I create the subfolder that will contain the pseudopotentials
        tempfolder.get_subfolder(self._PSEUDO_SUBFOLDER, create=True)
        # I create the subfolder with the output data (sometimes Quantum
        # Espresso codes crash if an empty folder is not already there
        tempfolder.get_subfolder(self._OUTPUT_SUBFOLDER, create=True)

        # We first prepare the NEB-specific input file 
        input_filecontent = self._generate_NEBinputdata(neb_parameters,settings_dict)

        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
        with open(input_filename, 'w') as infile:
            infile.write(input_filecontent)
            
        # We now generate the PW input files for each input structure
        local_copy_pseudo_list = []
        for i, structure in enumerate([first_structure, last_structure]): 
            # We need to a pass a copy of the settings_dict for each structure 
            this_settings_dict = copy.deepcopy(settings_dict)
            input_filecontent, this_local_copy_pseudo_list = self._generate_PWCPinputdata(pw_parameters,this_settings_dict,
                                                                                     pseudos,structure,kpoints)
            local_copy_pseudo_list += this_local_copy_pseudo_list

            input_filename = tempfolder.get_abs_path('pw_{}.in'.format(i+1))
            with open(input_filename, 'w') as infile:
                infile.write(input_filecontent)

        # We need to pop the settings that were used in the PW calculations
        for key in settings_dict.keys():
            if key not in this_settings_dict.keys():
                settings_dict.pop(key)

        # We avoid to copy twice the same pseudopotential to the same filename
        local_copy_pseudo_list = set(local_copy_pseudo_list)
        # We check that two different pseudopotentials are not copied 
        # with the same name (otherwise the first is overwritten)
        if len(set([ pseudoname for local_path, pseudoname in local_copy_pseudo_list])) < len(local_copy_pseudo_list):
            raise InputValidationError("Same filename for two different pseudopotentials")

        local_copy_list += local_copy_pseudo_list 

        # If present, add also the Van der Waals table to the pseudo dir
        # Note that the name of the table is not checked but should be the 
        # one expected by QE.
        if vdw_table:
            local_copy_list.append(
                (
                vdw_table.get_file_abs_path(),
                os.path.join(self._PSEUDO_SUBFOLDER,
                    os.path.split(vdw_table.get_file_abs_path())[1])
                )
                )

        # operations for restart
        symlink = settings_dict.pop('PARENT_FOLDER_SYMLINK', self._default_symlink_usage)  # a boolean
        if symlink:
            if parent_calc_folder is not None:
                # I put the symlink to the old parent ./out folder
                remote_symlink_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                                  self._OUTPUT_SUBFOLDER,'*'),
                     self._OUTPUT_SUBFOLDER
                    ))
                # and to the old parent prefix.path
                remote_symlink_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                                  '{}.path'.format(self._PREFIX)),
                     '{}.path'.format(self._PREFIX)
                    )) 
        else:
            # copy remote output dir and .path file, if specified
            if parent_calc_folder is not None:
                remote_copy_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                                  self._OUTPUT_SUBFOLDER,'*'),
                     self._OUTPUT_SUBFOLDER
                    ))
                # and to the old parent prefix.path
                remote_copy_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                                  '{}.path'.format(self._PREFIX)),
                     '{}.path'.format(self._PREFIX)
                    ))     

        # here we may create an aiida.EXIT file
        create_exit_file = settings_dict.pop('ONLY_INITIALIZATION',False)
        if create_exit_file:
            exit_filename = tempfolder.get_abs_path(
                             '{}.EXIT'.format(self._PREFIX))
            with open(exit_filename,'w') as f:
                f.write('\n')
                
        calcinfo = CalcInfo()
        codeinfo=CodeInfo()

        calcinfo.uuid = self.uuid
        # Empty command line by default
        cmdline_params = settings_dict.pop('CMDLINE', [])
        # For the time-being we only have the initial and final image
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list
        # In neb calculations there is no input read from standard input!! 
        
        codeinfo.cmdline_params = (["-input_images", "2"]
                                   + list(cmdline_params))
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]
        
        # Retrieve by default the output file and ...
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append([os.path.join(self._OUTPUT_SUBFOLDER,
                                                    self._PREFIX + '_*[0-9]', 'PW.out'),
                                       '.',
                                       2])
        calcinfo.retrieve_list.append([os.path.join(self._OUTPUT_SUBFOLDER,
                                                    self._PREFIX + '_*[0-9]',self._PREFIX + '.save', 
                                                    self._DATAFILE_XML_BASENAME),
                                       '.',
                                       3])
        settings_retrieve_list = settings_dict.pop('ADDITIONAL_RETRIEVE_LIST', [])
        calcinfo.retrieve_list += settings_retrieve_list
        calcinfo.retrieve_list += self._internal_retrieve_list

        if settings_dict:
            try:
                Parserclass = self.get_parserclass()
                parser = Parserclass(self)
                parser_opts = parser.get_parser_settings_key()
                settings_dict.pop(parser_opts)
            except (KeyError, AttributeError):  # the key parser_opts isn't inside the dictionary
                raise InputValidationError("The following keys have been found in "
                                           "the settings input node, but were not understood: {}".format(
                    ",".join(settings_dict.keys())))

        return calcinfo

    def _get_reference_structure(self):
        """
        Used to get the reference structure to obtain which 
        pseudopotentials to use from a given family using 
        use_pseudos_from_family. 
        This is a redefinition of the method in the BaseClass
        The first structure is used to choose the pseudopotentials
        """
        return self.get_inputs_dict()[self.get_linkname('first_structure')]
    
    def create_restart(self, force_restart=False, parent_folder_symlink=None):
        """
        Function to restart a calculation that was not completed before 
        (like max walltime reached...) i.e. not to restart a really FAILED calculation.
        Returns a calculation c2, with all links prepared but not stored in DB.
        To submit it simply:
        c2.store_all()
        c2.submit()
        
        :param bool force_restart: restart also if parent is not in FINISHED 
        state (e.g. FAILED, IMPORTED, etc.). Default=False.
        :param bool parent_folder_symlink: if True, symlinks are used
        instead of hard copies of the files. Default given by 
        self._default_symlink_usage.
        """
        from aiida.common.datastructures import calc_states

        # Check the calculation's state using ``from_attribute=True`` to
        # correctly handle IMPORTED calculations.
        if self.get_state(from_attribute=True) != calc_states.FINISHED:
            if not force_restart:
                raise InputValidationError(
                    "Calculation to be restarted must be "
                    "in the {} state. Otherwise, use the force_restart "
                    "flag".format(calc_states.FINISHED))

        if parent_folder_symlink is None:
            parent_folder_symlink = self._default_symlink_usage

        calc_inp = self.get_inputs_dict()

        old_inp_dict = calc_inp[self.get_linkname('neb_parameters')].get_dict()
        # add the restart flag
        old_inp_dict['PATH']['restart_mode'] = 'restart'
        inp_dict = ParameterData(dict=old_inp_dict)

        remote_folders = self.get_outputs(type=RemoteData)
        if len(remote_folders) != 1:
            raise InputValidationError("More than one output RemoteData found "
                                       "in calculation {}".format(self.pk))
        remote_folder = remote_folders[0]

        c2 = self.copy()

        #if not 'Restart' in c2.label:
        #    labelstring = c2.label + " Restart of {} {}.".format(
        #                                self.__class__.__name__,self.pk)
        #else:
        #    labelstring = " Restart of {} {}.".format(self.__class__.__name__,self.pk)
        #c2.label = labelstring.lstrip()

        # set the new links
        c2.use_neb_parameters(inp_dict)
        
        c2.use_pw_parameters(calc_inp[self.get_linkname('pw_parameters')])
        
        c2.use_first_structure(calc_inp[self.get_linkname('first_structure')])
        c2.use_last_structure(calc_inp[self.get_linkname('last_structure')])

        if self._use_kpoints:
            c2.use_kpoints(calc_inp[self.get_linkname('kpoints')])
        c2.use_code(calc_inp[self.get_linkname('code')])
        try:
            old_settings_dict = calc_inp[self.get_linkname('settings')
                                         ].get_dict()
        except KeyError:
            old_settings_dict = {}
        if parent_folder_symlink is not None:
            old_settings_dict['PARENT_FOLDER_SYMLINK'] = parent_folder_symlink

        if old_settings_dict:  # if not empty dictionary
            settings = ParameterData(dict=old_settings_dict)
            c2.use_settings(settings)

        c2._set_parent_remotedata(remote_folder)
        # set links for pseudos
        for linkname, input_node in self.get_inputs_dict().iteritems():
            if isinstance(input_node, UpfData):
                c2._add_link_from(input_node, label=linkname)

        # Add also the vdw table, if the parent had one
        try:
            old_vdw_table = calc_inp[self.get_linkname('vdw_table')]
        except KeyError:
            # No VdW table
            pass
        else:
            c2.use_vdw_table(old_vdw_table)

        return c2
