"""
Plugin to create a Quantum Espresso ph.x input file.
"""
import os
from aiida.orm import Calculation, DataFactory, CalculationFactory
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo
from aiida.orm.calculation.quantumespresso import get_input_data_text,_lowercase_dict,_uppercase_dict
from aiida.common.exceptions import UniquenessError

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
UpfData = DataFactory('upf')
RemoteData = DataFactory('remote')
PwCalculation = CalculationFactory('quantumespresso.pw')

# List of namelists (uppercase) that are allowed to be found in the
# input_data, in the correct order
_compulsory_namelists = ['INPUTPH']

# Keywords that cannot be set manually, only by the plugin
_blocked_keywords = [('INPUTPH', 'outdir'),
    ('INPUTPH', 'iverbosity'),
    ('INPUTPH', 'prefix'),
    ('INPUTPH', 'fildyn'),
    ]

class PhCalculation(Calculation):

    OUTPUT_SUBFOLDER = './out/'
    PREFIX = 'aiida'
    INPUT_FILE_NAME = 'aiida.in'
    OUTPUT_FILE_NAME = 'aiida.out'
#    OUTPUT_XML_FILE_NAME = 'data-file.xml'
    OUTPUT_XML_TENSOR_FILE_NAME = 'tensors.xml'
    FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX = 'DYN_MAT'
    OUTPUT_DYNAMICAL_MATRIX_PREFIX = os.path.join(FOLDER_OUTPUT_DYNAMICAL_MATRIX_PREFIX,
                                                  'dynamical-matrix-')

    # Default PW output parser provided by AiiDA
    _default_parser = 'quantumespresso.ph'
    
    def _prepare_for_submission(self,tempfolder,inputdict=None):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.
        """
#        from aiida.common.utils import get_unique_filename, get_suggestion

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
            raise InputValidationError("parameters is not of type ParameterData")
        
        # Settings can be undefined, and defaults to an empty dictionary.
        # They will be used for any input that doen't fit elsewhere.
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
        if parent_calc_folder is None:
            raise InputValidationError("No parent calculation found, needed to compute phonons")
        # TODO: to be a PwCalculation is not sufficient: it could also be a nscf calculation that is invalid for phonons
        parent_calcs = parent_calc_folder.get_inputs(type=PwCalculation)
        if len(parent_calcs) != 1:
            raise UniquenessError("RemoteData found to be child to two PwCalcs!")
        parent_calc = parent_calcs[0]
        if not isinstance(parent_calc,PwCalculation):
            raise  InputValidationError("The parent is not a PwCalculation")
        if not isinstance(parent_calc_folder, RemoteData):
            raise InputValidationError("parent_calc_folder, if specified,"
                    "must be of type RemoteData")

        # Also, the parent calculation must be on the same computer
        new_comp = self.get_computer()
        old_comp = parent_calc.get_computer()
        if ( not new_comp.uuid == old_comp.uuid ):
            raise IOError("PhCalculation must be launched on the same computer"
                          "of the parent: {}".format(old_comp.get_name()))

        default_parent_output_folder = parent_calc.OUTPUT_SUBFOLDER
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
        for nl, flag in _blocked_keywords:
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
            namelists_toprint = _compulsory_namelists
        
        input_filename = tempfolder.get_abs_path(self.INPUT_FILE_NAME)

        # create a folder for the dynamical matrices
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
        
        remote_copy_list.append(
                (parent_calc_folder.get_computer().uuid,
                 os.path.join(parent_calc_folder.get_remote_path(),
                              parent_calc_out_subfolder),
                 self.OUTPUT_SUBFOLDER))
        
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
        if not isinstance(data, RemoteData):
            raise ValueError("The data must be an instance of the RemoteData class")

        self._add_link_from(data, self.get_linkname_parent_calc_folder())

    def get_linkname_parent_calc_folder(self):
        """
        The name of the link used for the calculation folder of the parent (if any)
        """
        return "parent_calc_folder" 
    
    def set_parent_calc(self,calc):
        """
        Set the parent calculation of Ph, 
        from which it will inherit the outputsubfolder.
        The link will be created from parent RemoteData and PhCalculation 
        """
        if not isinstance(calc,PwCalculation):
            raise ValueError("Parent calculation must be a PwCalculation")
        
        remotedatas = calc.get_outputs(type=RemoteData)
        if len(remotedatas) != 1:
            raise UniquenessError("More than one output remotedata found")
        remotedata = remotedatas[0]
        
        self.use_parent_folder(remotedata)
        
