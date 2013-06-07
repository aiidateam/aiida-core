"""
Plugin to create a Quantum Espresso pw.x file.

TODO: many cards missing
TODO: implement if_pos
TODO: implement pre_... and post_... hooks to add arbitrary strings before
      and after a namelist, and a 'final_string' (all optional); useful 
      for development when new cards are needed
"""

from aiida.orm import Calculation, DataFactory
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
UpfData = DataFactory('upf')


class PwCalculation(Calculation):   
    
    def _prepare_for_submission(self,tempfolder):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.

        TODO: document what it has to return (probably a CalcInfo object)
              and what is the behavior on the tempfolder
        """
        input_file_name = 'aiida.in'
        output_file_name = 'aiida.out'
        
        # The code is not here        
        inputdict = self.get_inputdata_dict()

        try:
            parameters = inputdict.pop(self.get_linkname_parameters())
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterDa")
        
        try:
            structure = inputdict.pop(self.get_linkname_parameters())
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(structure,  StructureData):
            raise InputValidationError("structure is not of type StructureData")
        
        try:
            kpoints = inputdict.pop(self.get_linkname_kpoints())
        except KeyError:
            raise InputValidationError("No kpoints specified for this calculation")
        if not isinstance(kpoints,  ParameterData):
            raise InputValidationError("kpoints is not of type ParameterData")

        # Settings can be undefined, and defaults to an empty dictionary
        settings = inputdict.pop(self.get_linkname_settings(),{})
        
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

        # TODO: Check parameters here
        # Check structure, get species, check peudos
        # Check also pseudo type? Maybe not



        local_copy_list = []
        remote_copy_list = []
        cmdline_params = []
        
        # local_copy_list.append((fileobj.get_file_abs_path(),dest_rel_path))
        # remote_copy_list.append(
        # (fileobj.get_remote_machine(), fileobj.get_remote_path(),dest_rel_path))


        # raise InputValidationError

        calcinfo = CalcInfo()
        calcinfo.retrieve_list = []

        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = cmdline_params
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.stdin_name = input_file_name
        calcinfo.stdout_name = output_file_name
        calcinfo.retrieve_list.append(output_file_name)
        
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


comment = '''
from aiida.common.exceptions import InputValidationError
from aiida.common.classes.structure import Sites
from aiida.common.utils import get_suggestion
from aiida.codeplugins.quantumespresso import (
    conv_to_fortran, get_input_data_text)
from aiida.common.utils import get_unique_filename
from aiida.repository.structure import get_sites_from_uuid
from aiida.repository.potential import get_potential_from_uuid
import os

# List of namelists (uppercase) that are allowed to be found in the
# input_data, in the correct order
_compulsory_namelists = ['CONTROL', 'SYSTEM', 'ELECTRONS']

# List of cards (uppercase) that are allowed to be found in the
# input_data. 'atomic_species', 'atomic_positions' not allowed since they
# are automatically generated by the plugin
#_allowed_cards = ['K_POINTS', 'CONSTRAINTS', 'OCCUPATIONS']

# This is used to set the if_pos value in the ATOMIC_POSITIONS card
#_further_allowed = ['BLOCKED_COORDS']

_calc_types_noionscells = ['scf','nscf','bands']
_calc_types_onlyions = ['relax', 'md']
_calc_types_bothionscells = ['vc-relax', 'vc-md']

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

def _lowercase_dict(d, name=None):
    if isinstance(d,dict):
        new_dict = dict((k.lower(), v) for k, v in d.iteritems())
        if len(new_dict) != len(d):
            if name is None:
                raise InputValidationError("There is a dictionary with two keys "
                    "with the same name when compared case-insensitively. "
                    "This is not allowed.")
            else:
                raise InputValidationError("Inside the dictionary '{}' there are two keys "
                    "with the same name when compared case-insensitively. "
                    "This is not allowed.".format(name))
        return new_dict
    else:
        return d

def create_calc_input(calc, work_folder):
    """
    Create the necessary input files in work_folder for calculation calc.

    Note: for the moment, it requires that flags are provided lowercase,
        while namelists/cards are provided uppercase.
    
    Args:
        calc: the calculation object for which we want to create the 
            input file.
        work_folder: the folder where we want to create the files. Should
            be a aiida.common.classes.folder.Folder object.

    Returns:
        a dictionary with the following keys:
            retrieve_output: a list of files, directories or patterns to be
                retrieved from the cluster scratch dir and copied in the
                permanent aiida repository.
            cmdline_params: a (possibly empty) string with the command line
                parameters to pass to the code.
            stdin: a string with the file name to be used as standard input,
                or None if no stdin redirection is required. 
                Note: if you want to pass a string, create a file with the 
                string and use that file as stdin.
            stdout: a string with the file name to which the standard output
                should be redirected, or None if no stdout redirection is
                required. 
            stderr: a string with the file name to which the standard error
                should be redirected, or None if no stderr redirection is
                required. 
            preexec: a (possibly empty) string containing commands that may be
                required to be run before the code executes.
            postexec: a (possibly empty) string containing commands that may be
                required to be run after the code has executed.

    TODO: this function should equally work if called from the API client or
        from within django. To check/implement! May require some work

    TODO: options to set cmdline_params

    TODO: decide whether to return a namedtuple instead of a dict
        (see http://docs.python.org/2/library/collections.html#namedtuple-factory-function-for-tuples-with-named-fields )
    """
    PSEUDO_SUBFOLDER = './pseudo/'
    OUTPUT_SUBFOLDER = './out/'
    PREFIX = 'aiida'

    retdict = {}
    retdict['cmdline_params'] = "" # possibly -npool and similar
    retdict['stdin'] = 'aiida.in'
    retdict['stdout'] = 'aiida.out'
    retdict['stderr'] = None
    retdict['preexec'] = ""
    retdict['postexec'] = ""
    retdict['retrieve_output'] = []
    retdict['retrieve_output'].append(retdict['stdout'])
    retdict['retrieve_output'].append(os.path.join(OUTPUT_SUBFOLDER, 'data-file.xml'))

    input_filename = work_folder.get_filename(retdict['stdin'])

    # I get input parameters
    try:
        input_data = calc.get_input_data()
        read_input_params = input_data.pop('input_params')
    except Exception as e:
        import traceback
        print traceback.format_exc()
        raise InputValidationError('Unable to retrieve the input data. '
                                   'I got exception "{}" with message: '
                                   '{}'.format(str(type(e)), e.message))

    # I put the first-level keys as uppercase (i.e., namelist and card names)
    # and the second-level keys as lowercase, if they are dictionaries (deeper levels are
    # unchanged)
    input_params = dict((k.upper(), _lowercase_dict(v, name=k.upper())) 
                for k, v in read_input_params.iteritems())
    if len(input_params) != len(read_input_params):
        raise InputValidationError('There was at least a pair of keys in the '
            'input_params dictionary which were identically when compared '
            'case-insensitively. This is not allowed.')

    # I remove unwanted elements (for the moment, instead, I stop; to change when
    # we setup a reasonable logging)
    for nl, flag in _blocked_keywords:
        if nl in input_params:
            if flag in input_params[nl]:
                #del input_params[nl][flag]
                raise ValueError("You cannot specify explicitly the '{}' flag in the '{}' "
                                 "namelist or card.".format(flag, nl))

    # Set some variables (look out at the case! NAMELISTS should be uppercase, internal
    # flag names must be lowercase)
    if 'CONTROL' not in input_params:
        input_params['CONTROL'] = {}
    input_params['CONTROL']['pseudo_dir'] = PSEUDO_SUBFOLDER
    input_params['CONTROL']['outdir'] = OUTPUT_SUBFOLDER
    input_params['CONTROL']['verbosity'] = 'high'
    input_params['CONTROL']['prefix'] = PREFIX

    # get_input_sites returns a list, I check that I have only
    # one input site and then I save it in input_site
    input_structures = input_data.pop('structure_list',[])
    if len(input_structures) != 1:
        raise InputValidationError('One and only one input structure can be '
            'attached to a QE pw.x calculation. '
            'You provided {} structures instead.'.format(len(input_structures)))
    input_site_uuid = input_structures[0]
    input_site = get_sites_from_uuid(input_site_uuid)

    input_potentials_uuid = input_data.pop('potential_list',[])
    
    input_potentials = [get_potential_from_uuid(p) for p in 
                        input_potentials_uuid]


    # ============ I prepare the input site data =============
    # ------------ CELL_PARAMETERS -----------
    cell_parameters_card = "CELL_PARAMETERS angstrom\n"
    for vector in input_site.cell:
        cell_parameters_card += ("{0:18.10f} {1:18.10f} {2:18.10f}"
                                 "\n".format(*vector))

    # ------------- ATOMIC_SPECIES ------------
    specie_names, specie_indices = zip(*input_site.get_types())
    first_specie_sites = tuple(input_site.sites[sp_idx[0]] for
                               sp_idx in specie_indices)
    if len(specie_names) != len(input_potentials):
        raise InputValidationError('The number of provided pseudopotentials '
            'in the potential_list variable is different from the number of '
            'species of the input structure.')
    for i, (pot, site) in enumerate(zip(input_potentials, first_specie_sites)):
        if set(site.symbols) != pot.get_element_set():
            pot_el_str = ",".join(sorted(list(pot.get_element_set())))
            site_el_str = ",".join(sorted(site.symbols))
            errstr = ('Different set of elements for the '
                'potential at position {:d} and the corresponding atom: ({}) '
                'vs. ({})'.format(i+1, pot_el_str, site_el_str))
            raise InputValidationError(errstr)

    # I create the subfolder that contains the pseudopotentials
    pseudo_folder = work_folder.get_subfolder(PSEUDO_SUBFOLDER,create=True)

    # Will contain the filenames of the pseudopotentials (may not be exactly
    # the ones used in the repository due to name collisions)
    potential_filenames = []

    # I copy the potential files in the suitable subfolder.
    # .. todo:: change in so that it works also on the client side.
    for pot in input_potentials:
        pot_repo_folder = pot.get_repo_folder()
        # I get all filenames, excluding those starting with a dot
        # (I also exclude subfolders by using i[1]==True)
        pot_file_list = [i[0] for i in 
                         pot_repo_folder.get_content_list(pattern='[!.]*') 
                         if i[1]]
        if len(pot_file_list) != 1:
            raise InputValidationError(
                "The potential folder on the AiiDA repository "
                "contains {:d} files, while I can manage only 1 file for "
                "Quantum Espresso.".format(len(pot_file_list)))
        # I create a unique filename. This is only the file name
        pot_file = get_unique_filename(pot_file_list[0],
                                       potential_filenames)

        # The path to the pseudo folder within the calculation in the
        # repository. I must set the correct RELATIVE symlink!
        final_pseudo_subdir = calc.get_repo_inputs_folder().get_subfolder(
            PSEUDO_SUBFOLDER)
        relative_path = os.path.relpath(pot_repo_folder.get_filename(pot_file),
                                        start=final_pseudo_subdir.abspath)
        pseudo_folder.create_symlink(src=relative_path, name=pot_file)
        potential_filenames.append(pot_file)

    atomic_species_card_list = ["ATOMIC_SPECIES\n"]
    for specie_name, first_specie_site, pot_name in zip(
        specie_names, first_specie_sites, potential_filenames):
        atomic_species_card_list.append("{} {} {}\n".format(
                specie_name.ljust(6), first_specie_site.mass, pot_name))
    atomic_species_card = "".join(atomic_species_card_list)

    # ------------ ATOMIC_POSITIONS -----------
    atomic_positions_card_list = ["ATOMIC_POSITIONS angstrom\n"]

    # Check on validity of FIXED_COORDS
    fixed_coords_strings = []
    try:
        fixed_coords = input_params.pop('FIXED_COORDS')
        if len(fixed_coords) != len(input_site.sites):
            raise InputValidationError("Input structure contains {:d} atoms, but "
                "fixed_coords has length {:d}".format(len(input_site.sites),
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
    except KeyError:
        # No fixed_coords specified: I store a list of empty strings
        fixed_coords_strings = [""] * len(input_site.sites)

    # TODO: implement if_pos
    for idx, (site, fixed_coords_string) in enumerate(
        zip(input_site.sites,fixed_coords_strings)):
        if site.is_alloy() or site.has_vacancies():
            raise InputValidationError("The {}-th site is an alloy or has "
                "vacancies. This is not allowed for pw.x input structures.")
        atomic_positions_card_list.append(
            "{0} {1:18.10f} {2:18.10f} {3:18.10f} {4}\n".format(
                site.type.ljust(6), site.position[0], site.position[1],
                site.position[2], fixed_coords_string))
    atomic_positions_card = "".join(atomic_positions_card_list)

    # I set the variables that must be specified, related to the system
    # Set some variables (look out at the case! NAMELISTS should be uppercase, internal
    # flag names must be lowercase)
    input_params['SYSTEM']['ibrav'] = 0
    input_params['SYSTEM']['nat'] = len(input_site.sites)
    input_params['SYSTEM']['ntyp'] = len(specie_names)

    # ============ I prepare the k-points =============
    try:
        k_points = input_params.pop('K_POINTS')
    except KeyError: 
        raise InputValidationError("No K_POINTS specified.")

    try:
        k_points_type = k_points['type']
    except KeyError: 
        raise InputValidationError("No 'type' specified in K_POINTS card.")
    
    if k_points_type != "gamma":
        try:
            k_points_list = k_points["points"]
            num_k_points = len(k_points_list)
        except KeyError:
            raise InputValidationError("'K_POINTS' does not contain a 'points' "
                                       "key")
        except TypeError:
            raise InputValidationError("'points' key is not a list")
        if num_k_points == 0:
            raise InputValidationError("At least one k point must be "
                "provided for non-gamma calculations")

    k_points_card = "K_POINTS {}\n".format(k_points_type)

    if k_points_type == "automatic":
        if len(k_points_list) != 6:
            raise InputValidationError("k_points type is automatic, but "
                "'points' is not a list of 6 integers")
        try: 
            k_points_card += ("{:d} {:d} {:d} {:d} {:d} {:d}\n"
                             "".format(*k_points_list))
        except ValueError:
            raise InputValidationError("Some elements  of the 'points' key "
                "in the K_POINTS card are not integers")
            
    elif k_points_type == "gamma":
        # nothing to be written in this case
        pass
    else:
        k_points_card += "{:d}\n".format(num_k_points)
        try:
            if all(len(i)==4 for i in k_points_list):
                for kpoint in k_points_list:
                    k_points_card += ("  {:18.10f} {:18.10f} {:18.10f} {:18.10f}"
                        "\n".format(kpoint))
            else:
                raise InputValidationError("points must either all have "
                    "length four (3 coordinates + last value: weight)")
        except (KeyError, TypeError):
            raise InputValidationError("'points' must be a list of k points, "
                "each k point must be provided as a list of 4 items: its "
                "coordinates and its weight")


    # =================== NAMELISTS AND CARDS ========================
    try:
        control_nl = input_params['CONTROL']
        calculation_type = control_nl['calculation']
    except KeyError as e:
        raise InputValidationError("No 'calculation' in CONTROL namelist.")
            
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
                                   "CONTROL namelist {}".format(sugg_string))

    
    # TODO: set default/forced values

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
        infile.write(k_points_card)
        infile.write(cell_parameters_card)
        #TODO: write CONSTRAINTS
        #TODO: write OCCUPATIONS

    #TODO: improve this debug
    if len(input_params):
        print "Warning, following nl/cards in input_params not consumed: " + ",".join(
            input_params.keys())
    if len(input_data):
        print "Warning, following options in input_data not consumed: " + ",".join(
            input_data.keys())

    return retdict
'''