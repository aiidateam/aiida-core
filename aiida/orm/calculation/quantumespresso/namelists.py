"""
Plugin to create a Quantum Espresso input file for a generic post-processing
(or similar) code that only requires a few namelists (plus possibly some text
afterwards).
"""
import os

from aiida.orm import Calculation, DataFactory
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo
from aiida.orm.calculation.quantumespresso import (
    _lowercase_dict, _uppercase_dict, get_input_data_text)

ParameterData = DataFactory('parameter') 
RemoteData = DataFactory('remote') 
FolderData = DataFactory('folder') 

    
class NamelistsCalculation(Calculation):   

    OUTPUT_SUBFOLDER = './out/'
    PREFIX = 'aiida'
    INPUT_FILE_NAME = 'aiida.in'
    OUTPUT_FILE_NAME = 'aiida.out'
    _internal_retrieve_list = []
    _default_namelists = ['INPUTPP']
    _default_parent_output_folder = './out/'
    _blocked_keywords = [] # a list of tuples with key and value fixed
    _parent_folder_type = 'RemoteData'
    _default_parser = None

    def _get_following_text(self, inputdict, settings):
        """
        By default, no text follows the namelists section.
        This function should consume the content of inputdict (if it requires
        a different node) or the keys inside settings, using the 'pop' method,
        so that inputdict and settings should remain empty at the end of 
        _prepare_for_submission, if all flags/nodes were recognized
        """
        return ""
    
    def _prepare_for_submission(self,tempfolder, inputdict = None):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """
        local_copy_list = []
        remote_copy_list = []
        
        # The code is not here, only the data        
        if inputdict is None:
            inputdict = self.get_inputdata_dict()

        try:
            parameters = inputdict.pop(self.get_linkname_parameters())
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterDa")
        
        # Settings can be undefined, and defaults to an empty dictionary
        settings = inputdict.pop(self.get_linkname_settings(),None)
        if settings is None:
            settings_dict = {}
        else:
            if not isinstance(settings,  ParameterData):
                raise InputValidationError("settings, if specified, must be of "
                                           "type ParameterData")
            # Settings converted to uppercase
            settings_dict = _uppercase_dict(settings.get_dict(),
                                            dict_name='settings')

        parent_calc_folder = inputdict.pop(self.get_linkname_parent_calc_folder(),None)
        
        if parent_calc_folder is not None:
            if not isinstance(parent_calc_folder, self._parent_folder_type):
                raise InputValidationError("parent_calc_folder, if specified,"
                    "must be of type {}".format(self._parent_folder_type.__name__))

        following_text = self._get_following_text(inputdict, settings)
                
        # Here, there should be no more parameters...
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
        
        # set default values. NOTE: this is different from PW/CP
        for blocked in self._blocked_keywords:
            namelist = blocked[0].upper()
            key = blocked[1].lower()
            value = blocked[2]
            
            if namelist in input_params:
                if key in input_params[namelist]:
                    raise InputValidationError(
                        "You cannot specify explicitly the '{}' key in the '{}' "
                        "namelist.".format(key, namelist))
                    
            # set to a default
            if not input_params[namelist]:
                input_params[namelist] = {}
            input_params[namelist][key] = value
        
        # =================== NAMELISTS AND CARDS ========================
        try:
            namelists_toprint = settings_dict.pop('NAMELISTS')
            if not isinstance(namelists_toprint, list):
                raise InputValidationError(
                    "The 'NAMELISTS' value, if specified in the settings input "
                    "node, must be a list of strings")
        except KeyError: # list of namelists not specified; do automatic detection
            namelists_toprint = self._default_namelists
        
        input_filename = tempfolder.get_abs_path(self.INPUT_FILE_NAME)

        with open(input_filename,'w') as infile:
            for namelist_name in namelists_toprint:
                infile.write("&{0}\n".format(namelist_name))
                # namelist content; set to {} if not present, so that we leave an 
                # empty namelist
                namelist = input_params.pop(namelist_name,{})
                for k, v in sorted(namelist.iteritems()):
                    infile.write(get_input_data_text(k,v))
                infile.write("/\n")

            # Write remaning text now, if any
            infile.write(following_text)

        # Check for specified namelists that are not expected
        if input_params:
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))
        
        # copy remote output dir, if specified
        print parent_calc_folder
        if parent_calc_folder is not None:
            if isinstance(parent_calc_folder,RemoteData):
                parent_calc_out_subfolder = settings_dict.pop('parent_calc_out_subfolder',
                                              self._default_parent_output_folder)
                remote_copy_list.append(
                         (parent_calc_folder.get_computer().uuid,
                          os.path.join(parent_calc_folder.get_remote_path(),
                                       parent_calc_out_subfolder),
                          self.OUTPUT_SUBFOLDER))
            elif isinstance(parent_calc_folder,FolderData):
                local_copy_list.append( (parent_calc_folder.get_abs_path(self.OUTPUT_SUBFOLDER),
                                         self.OUTPUT_SUBFOLDER
                                        )
                                      )
        calcinfo = CalcInfo()

        calcinfo.uuid = self.uuid
        # Empty command line by default
        calcinfo.cmdline_params = settings_dict.pop('CMDLINE', [])
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.stdin_name = self.INPUT_FILE_NAME
        calcinfo.stdout_name = self.OUTPUT_FILE_NAME
        
        # Retrieve by default the output file and the xml file
        calcinfo.retrieve_list = []        
        calcinfo.retrieve_list.append(self.OUTPUT_FILE_NAME)
        settings_retrieve_list = settings_dict.pop('additional_retrieve_list', [])
        calcinfo.retrieve_list += settings_retrieve_list
        calcinfo.retrieve_list += self._internal_retrieve_list
        
        if settings_dict:
            try:
                Parserclass = self.get_parserclass()
                parser = Parserclass(self)
                parser_opts = parser.get_parser_settings_key()
                settings_dict.pop(parser_opts)
            except (KeyError,AttributeError): # the key parser_opts isn't inside the dictionary, or it is set to None
                raise InputValidationError("The following keys have been found in "
                  "the settings input node, but were not understood: {}".format(
                  ",".join(settings_dict.keys())))
        
        return calcinfo

    def use_settings(self, data):
        """
        Set the settings for this calculation
        """
        if not isinstance(data, ParameterData):
            raise ValueError("The data must be an instance of the ParameterData class")

        self._replace_link_from(data, self.get_linkname_settings())

    def get_linkname_settings(self):
        """
        The name of the link used for the settings
        """
        return "settings"

    def use_parameters(self, data):
        """
        Set the parameters for this calculation
        """
        if not isinstance(data, ParameterData):
            raise ValueError("The data must be an instance of the ParameterData class")

        self._replace_link_from(data, self.get_linkname_parameters())

    def get_linkname_parameters(self):
        """
        The name of the link used for the parameters
        """
        return "parameters"
        
    def use_parent_folder(self, data):
        """
        Set the folder of the parent calculation, if any
        """
        if not isinstance(data, self._parent_folder_type):
            raise ValueError("The data must be an instance of the {} class"
                             .format(self._parent_folder_type))

        self._replace_link_from(data, self.get_linkname_parent_calc_folder())

    def set_parent_calc(self,calc):
        """
        Set the parent calculation, from which it will inherit the 
        outputsubfolder. The link will be created from parent 
        RemoteData/FolderData to NamelistCalculation. 
        """
        from aiida.common.exceptions import UniquenessError
        remotedatas = calc.get_outputs(type=self._parent_folder_type)
        if len(remotedatas) != 1:
            raise UniquenessError("More than one output {} found".format(self._parent_folder_type))
        remotedata = remotedatas[0]
        
        self.use_parent_folder(remotedata)

    def get_linkname_parent_calc_folder(self):
        """
        The name of the link used for the calculation folder of the parent (if any)
        """
        return "parent_calc_folder"
