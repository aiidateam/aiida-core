"""
Plugin to create a Quantum Espresso pw.x file.

TODO: COPY OUTDIR FROM PREVIOUS CALCULATION! Should be an input node of type
     RemoteData (or maybe subclass it?).
TODO: tests!
TODO: DOC + implementation of SETTINGS
TODO: preexec, postexec
TODO: Check that no further parameters are passed in SETTINGS
TODO: many cards missing: check and implement
      e.g.: ['CONSTRAINTS', 'OCCUPATIONS']
TODO: implement pre_... and post_... hooks to add arbitrary strings before
      and after a namelist, and a 'final_string' (all optional); useful 
      for development when new cards are needed
TODO: all a lot of logger.debug stuff
"""
import os

from aiida.orm import Calculation, DataFactory
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
UpfData = DataFactory('upf')


# List of namelists (uppercase) that are allowed to be found in the
# input_data, in the correct order
_compulsory_namelists = ['CONTROL', 'SYSTEM', 'ELECTRONS']

# Add here if new calculation types are added to QE
_calc_types_noionscells = ['scf','nscf','bands']
_calc_types_onlyions = ['relax', 'md']
_calc_types_bothionscells = ['vc-relax', 'vc-md']

# Keywords that cannot be set
_blocked_keywords = [('CONTROL', 'pseudo_dir'), # set later
    ('CONTROL', 'outdir'),  # set later
    ('CONTROL', 'verbosity'),  # set later
    ('CONTROL', 'prefix'),  # set later
    ('SYSTEM', 'ibrav'),  # set later
    ('SYSTEM', 'celldm'),
    ('SYSTEM', 'nat'),  # set later
    ('SYSTEM', 'ntyp'),  # set later
    ('SYSTEM', 'a'), ('SYSTEM', 'b'), ('SYSTEM', 'c'),
    ('SYSTEM', 'cosab'), ('SYSTEM', 'cosac'), ('SYSTEM', 'cosbc'),
    ]

def get_input_data_text(key,val):
    """
    Given a key and a value, return a string (possibly multiline for arrays)
    with the text to be added to the input file.
    
    Args:
        key: the flag name
        val: the flag value. If it is an array, a line for each element
            is produced, with variable indexing starting from 1.
            Each value is formatted using the conv_to_fortran function.
    """
    from aiida.common.utils import conv_to_fortran
    # I don't try to do iterator=iter(val) and catch TypeError because
    # it would also match strings
    if hasattr(val,'__iter__'):
        # a list/array/tuple of values
        list_of_strings = [
            "  {0}({2}) = {1}\n".format(key, conv_to_fortran(itemval),
                                        idx+1)
            for idx, itemval in enumerate(val)]
        return "".join(list_of_strings)
    else:
        # single value
        return "  {0} = {1}\n".format(key, conv_to_fortran(val))

def _if_pos(fixed):
    """
    Simple function that returns 0 if fixed is True, 1 otherwise.
    Useful to convert from the boolean value of fixed_coords to the value required
    by Quantum Espresso as if_pos.
    """
    if fixed:
        return 0
    else:
        return 1

def _lowercase_dict(d, dict_name):
    from collections import Counter
    
    if isinstance(d,dict):
        new_dict = dict((str(k).lower(), v) for k, v in d.iteritems())
        if len(new_dict) != len(d):
            num_items = Counter(str(k).lower() for k in d.keys())
            double_keys = ",".join([k for k, v in num_items if v > 1])
            raise InputValidationError(
                "Inside the dictionary '{}' there are the following keys that "
                "are repeated more than once when compared case-insensitively: {}."
                "This is not allowed.".format(dict_name, double_keys))
        return new_dict
    else:
        raise TypeError("_lowercase_dict accepts only dictionaries as argument")
    
def _uppercase_dict(d, dict_name):
    from collections import Counter
    
    if isinstance(d,dict):
        new_dict = dict((str(k).upper(), v) for k, v in d.iteritems())
        if len(new_dict) != len(d):
            
            num_items = Counter(str(k).upper() for k in d.keys())
            double_keys = ",".join([k for k, v in num_items if v > 1])
            raise InputValidationError(
                "Inside the dictionary '{}' there are the following keys that "
                "are repeated more than once when compared case-insensitively: {}."
                "This is not allowed.".format(dict_name, double_keys))
        return new_dict
    else:
        raise TypeError("_lowercase_dict accepts only dictionaries as argument")
    
    
class PwCalculation(Calculation):   

    PSEUDO_SUBFOLDER = './pseudo/'
    OUTPUT_SUBFOLDER = './out/'
    PREFIX = 'aiida'
    INPUT_FILE_NAME = 'aiida.in'
    OUTPUT_FILE_NAME = 'aiida.out'

    def _prepare_for_submission(self,tempfolder):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.
        """
        from aiida.common.utils import get_unique_filename, get_suggestion

        local_copy_list = []
        remote_copy_list = []
        
        # The code is not here, only the data        
        inputdict = self.get_inputdata_dict()

        try:
            parameters = inputdict.pop(self.get_linkname_parameters())
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterDa")
        
        try:
            structure = inputdict.pop(self.get_linkname_structure())
        except KeyError:
            raise InputValidationError("No structure specified for this calculation")
        if not isinstance(structure,  StructureData):
            raise InputValidationError("structure is not of type StructureData")
        
        try:
            kpoints = inputdict.pop(self.get_linkname_kpoints())
        except KeyError:
            raise InputValidationError("No kpoints specified for this calculation")
        if not isinstance(kpoints,  ParameterData):
            raise InputValidationError("kpoints is not of type ParameterData")

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
        
        pseudos = {}
        for link in inputdict.keys():
            if link.startswith(self.get_linkname_pseudo_prefix()):
                kind = link[len(self.get_linkname_pseudo_prefix()):]
                pseudos[kind] = inputdict.pop(link)
                if not isinstance(pseudos[kind], UpfData):
                    raise InputValidationError("Pseudo for kind {} is not of "
                                               "type UpfData".format(kind))
        
        # Here, there should be no more parameters...
        if inputdict:
            raise InputValidationError("The following input data nodes are "
                "unrecognized: {}".format(inputdict.keys()))

        # Check structure, get species, check peudos
        kindnames = [k.name for k in structure.kinds]
        if set(kindnames) != set(pseudos.keys()):
            err_msg = ("Mismatch between the defined pseudos and the list of "
                       "kinds of the structure. Pseudos: {}; kinds: {}".format(
                        ",".join(pseudos.keys()), ",".join(list(kindnames))))
            raise InputValidationError(err_msg)

        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################

        # Kpoints converted to uppercase
        kpoints_dict = _uppercase_dict(kpoints.get_dict(),
                                       dict_name='kpoints')

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
        if 'CONTROL' not in input_params:
            input_params['CONTROL'] = {}
        input_params['CONTROL']['pseudo_dir'] = self.PSEUDO_SUBFOLDER
        input_params['CONTROL']['outdir'] = self.OUTPUT_SUBFOLDER
        input_params['CONTROL']['verbosity'] = 'high'
        input_params['CONTROL']['prefix'] = self.PREFIX

        # ============ I prepare the input site data =============
        # ------------ CELL_PARAMETERS -----------
        cell_parameters_card = "CELL_PARAMETERS angstrom\n"
        for vector in structure.cell:
            cell_parameters_card += ("{0:18.10f} {1:18.10f} {2:18.10f}"
                                     "\n".format(*vector))

        # ------------- ATOMIC_SPECIES ------------
        # I create the subfolder that will contain the pseudopotentials
        tempfolder.get_subfolder(self.PSEUDO_SUBFOLDER, create=True)
        
        atomic_species_card_list = ["ATOMIC_SPECIES\n"]

        # Keep track of the filenames to avoid to overwrite files
        pseudo_filenames = []
        # I add the pseudopotential files to the list of files to be copied
        for kind in structure.kinds:
            # This should not give errors, I already checked before that
            # the list of keys of pseudos and kinds coincides
            ps = pseudos[kind.name]
            if kind.is_alloy() or kind.has_vacancies():
                raise InputValidationError("Kind '{}' is an alloy or has "
                    "vacancies. This is not allowed for pw.x input structures."
                    "".format(kind.name))

            filename = get_unique_filename(ps.filename, pseudo_filenames)
            pseudo_filenames.append(filename)
            # I add this pseudo file to the list of files to copy            
            local_copy_list.append((ps.get_file_abs_path(),
                                   os.path.join(self.PSEUDO_SUBFOLDER,filename)))
            
            atomic_species_card_list.append("{} {} {}\n".format(
                kind.name.ljust(6), kind.mass, filename))
        atomic_species_card = "".join(atomic_species_card_list)
        del atomic_species_card_list # Free memory

        # ------------ ATOMIC_POSITIONS -----------
        atomic_positions_card_list = ["ATOMIC_POSITIONS angstrom\n"]

        # Check on validity of FIXED_COORDS
        fixed_coords_strings = []
        fixed_coords = settings_dict.pop('FIXED_COORDS',None)
        if fixed_coords is None:
            # No fixed_coords specified: I store a list of empty strings
            fixed_coords_strings = [""] * len(structure.sites)            
        else:
            if len(fixed_coords) != len(structure.sites):
                raise InputValidationError(
                    "Input structure contains {:d} sites, but "
                    "fixed_coords has length {:d}".format(len(structure.sites),
                                                          len(fixed_coords)))

            for i, this_atom_fix in enumerate(fixed_coords):
                if len(this_atom_fix) != 3:
                    raise InputValidationError("fixed_coords({:d}) has not length three"
                                               "".format(i+1))
                for fixed_c in this_atom_fix:
                    if not isinstance(fixed_c, bool):
                        raise InputValidationError("fixed_coords({:d}) has non-boolean "
                                                   "elements".format(i+1))

                if_pos_values = [_if_pos(_) for _ in this_atom_fix]
                fixed_coords_strings.append("  {:d} {:d} {:d}".format(*if_pos_values))
    
    
        for site, fixed_coords_string in zip(
              structure.sites,fixed_coords_strings):
            atomic_positions_card_list.append(
            "{0} {1:18.10f} {2:18.10f} {3:18.10f} {4}\n".format(
                site.kind.ljust(6), site.position[0], site.position[1],
                site.position[2], fixed_coords_string))
        atomic_positions_card = "".join(atomic_positions_card_list)
        del atomic_positions_card_list # Free memory

        # I set the variables that must be specified, related to the system
        # Set some variables (look out at the case! NAMELISTS should be
        # uppercase, internal flag names must be lowercase)
        if 'SYSTEM' not in input_params:
            input_params['SYSTEM'] = {}
        input_params['SYSTEM']['ibrav'] = 0
        input_params['SYSTEM']['nat'] = len(structure.sites)
        input_params['SYSTEM']['ntyp'] = len(kindnames)

        # ============ I prepare the k-points =============
        try:
            kpoints_type = kpoints_dict['TYPE']
        except KeyError: 
            raise InputValidationError("No 'TYPE' specified in the "
                                       "kpooints input node.")
    
        if kpoints_type != "gamma":
            try:
                kpoints_list = kpoints_dict["POINTS"]
                num_kpoints = len(kpoints_list)
            except KeyError:
                raise InputValidationError(
                    "the kpoints input node does not contain a 'POINTS' "
                    "key")
            except TypeError:
                raise InputValidationError("'POINTS' key is not a list")
        if num_kpoints == 0:
            raise InputValidationError("At least one k point must be "
                "provided for non-gamma calculations")

        kpoints_card_list = ["K_POINTS {}\n".format(kpoints_type)]

        if kpoints_type == "automatic":
            if len(kpoints_list) != 6:
                raise InputValidationError("k-points type is automatic, but "
                    "'POINTS' is not a list of 6 integers")
            try: 
                kpoints_card_list.append("{:d} {:d} {:d} {:d} {:d} {:d}\n"
                    "".format(*kpoints_list))
            except ValueError:
                raise InputValidationError("Some elements  of the 'POINTS' key "
                    "in the K_POINTS card are not integers")        
        elif kpoints_type == "gamma":
            # nothing to be written in this case
            pass
        else:
            kpoints_card_list.append("{:d}\n".format(num_kpoints))
            try:
                if all(len(i)==4 for i in kpoints_list):
                    for kpoint in kpoints_list:
                        kpoints_card_list.append(
                            "  {:18.10f} {:18.10f} {:18.10f} {:18.10f}"
                            "\n".format(kpoint))
                else:
                    raise InputValidationError("'POINTS' must either all have "
                        "length four (3 coordinates + last value: weight)")
            except (KeyError, TypeError):
                raise InputValidationError("'POINTS' must be a list of k points, "
                    "each k point must be provided as a list of 4 items: its "
                    "coordinates and its weight")
        kpoints_card = "".join(kpoints_card_list)
        del kpoints_card_list

        # =================== NAMELISTS AND CARDS ========================
        try:
            namelists_toprint = settings_dict.pop('NAMELISTS')
            if not isinstance(namelists_toprint, list):
                raise InputValidationError(
                    "The 'NAMELISTS' value, if specified in the settings input "
                    "node, must be a list of strings")
        except KeyError: # list of namelists not specified; do automatic detection
            try:
                control_nl = input_params['CONTROL']
                calculation_type = control_nl['calculation']
            except KeyError:
                raise InputValidationError(
                    "No 'calculation' in CONTROL namelist."
                    "It is required for automatic detection of the valid list of "
                    "namelists.")
            
            if calculation_type in _calc_types_noionscells:
                namelists_toprint = _compulsory_namelists
            elif calculation_type in _calc_types_bothionscells:
                namelists_toprint = _compulsory_namelists + ['IONS', 'CELL']
            elif calculation_type in _calc_types_onlyions:
                namelists_toprint = _compulsory_namelists + ['IONS']
            else:
                sugg_string = get_suggestion(calculation_type,
                                             _calc_types_noionscells + 
                                             _calc_types_onlyions + 
                                             _calc_types_bothionscells)
                raise InputValidationError("Unknown 'calculation' value in "
                    "CONTROL namelist {}. Otherwise, specify the list of "
                    "namelists using the NAMELISTS inside the settings input "
                    "node".format(sugg_string))
        
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

            # Write cards now
            infile.write(atomic_species_card)
            infile.write(atomic_positions_card)
            infile.write(kpoints_card)
            infile.write(cell_parameters_card)
            #TODO: write CONSTRAINTS
            #TODO: write OCCUPATIONS

        if input_params:
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))

        # TODO: copy remote output dir, if specified
        # remote_copy_list.append(
        # (fileobj.get_remote_machine(), fileobj.get_remote_path(),dest_rel_path))

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
        calcinfo.retrieve_list.append(
            os.path.join(self.OUTPUT_SUBFOLDER, 
                         '{}.save'.format(self.PREFIX), 'data-file.xml'))
        
        if settings_dict:
            raise InputValidationError("The following keys have been found in "
                "the settings input node, but were not understood: {}".format(
                ",".join(settings_dict.keys())))
        
        return calcinfo


    def use_kpoints(self, data):
        """
        Set the kpoints for this calculation
        """
        if not isinstance(data, ParameterData):
            raise ValueError("The data must be an instance of the ParameterData class")

        self.replace_link_from(data, self.get_linkname_kpoints())

    def get_linkname_kpoints(self):
        """
        The name of the link used for the kpoints
        """
        return "kpoints"

    def use_structure(self, data):
        """
        Set the structure for this calculation
        """
        if not isinstance(data, StructureData):
            raise ValueError("The data must be an instance of the StructureData class")

        self.replace_link_from(data, self.get_linkname_structure())

    def get_linkname_structure(self):
        """
        The name of the link used for the structure
        """
        return "structure"

    def use_settings(self, data):
        """
        Set the settings for this calculation
        """
        if not isinstance(data, ParameterData):
            raise ValueError("The data must be an instance of the ParameterData class")

        self.replace_link_from(data, self.get_linkname_settings())

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

        self.replace_link_from(data, self.get_linkname_parameters())

    def get_linkname_parameters(self):
        """
        The name of the link used for the parameters
        """
        return "parameters"

    def use_pseudo(self, data, kind):
        """
        Set the pseudo to use for the atomic kind 'kind' for this calculation
        
        Args:
            data: the Data object of type UpfData
            kind: a string identifying the kind for which this pseudo should be used
        """
        if not isinstance(data, UpfData):
            raise ValueError("The data must be an instance of the UpfData class")

        self.replace_link_from(data, self.get_linkname_pseudo(kind))
        
    def get_linkname_pseudo(self, kind):
        """
        The name of the link used for the pseudo for kind 'kind'. 
        It appends the pseudo name to the pseudo_prefix, as returned by the
        get_linkname_pseudo_prefix() method.
        
        Args:
            kind: a string for the atomic kind for which we want to get the link name
        """
        return "{}{}".format(self.get_linkname_pseudo_prefix(),kind)


    def get_linkname_pseudo_prefix(self):
        """
        The prefix for the name of the link used for the pseudo for kind 'kind'
        
        Args:
            kind: a string for the atomic kind for which we want to get the link name
        """
        return "pseudo_"


