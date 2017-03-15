# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os

from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo
from aiida.orm.data.upf import get_pseudos_from_structure
from aiida.common.utils import classproperty

from aiida.orm.data.structure import StructureData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.array.kpoints import KpointsData
from aiida.orm.data.upf import UpfData
from aiida.orm.data.singlefile import SinglefileData
from aiida.orm.data.remote import RemoteData
from aiida.common.datastructures import CodeInfo
from aiida.common.links import LinkType



class BasePwCpInputGenerator(object):
    """
    Baseclass for the common things between CP and PW of Quantum ESPRESSO.
    """
    _PSEUDO_SUBFOLDER = './pseudo/'
    _OUTPUT_SUBFOLDER = './out/'
    _PREFIX = 'aiida'
    _INPUT_FILE_NAME = 'aiida.in'
    _OUTPUT_FILE_NAME = 'aiida.out'
    _DATAFILE_XML_BASENAME = 'data-file.xml'
    _DATAFILE_XML = 'undefined.xml'
    _ENVIRON_INPUT_FILE_NAME = 'environ.in'

    ## NOTE!! DO NOT UPDATE lists and dictionaries defined here,
    ## they will be changed for all classes of the current run!

    # Additional files that should always be retrieved for the specific plugin
    _internal_retrieve_list = []

    ## Default PW output parser provided by AiiDA
    # to be defined in the subclass

    _automatic_namelists = {}

    # in restarts, will not copy but use symlinks
    _default_symlink_usage = True

    # in restarts, it will copy from the parent the following
    _restart_copy_from = os.path.join(_OUTPUT_SUBFOLDER, '*')

    # in restarts, it will copy the previous folder in the following one
    _restart_copy_to = _OUTPUT_SUBFOLDER

    # Default verbosity; change in subclasses
    _default_verbosity = 'high'

    # To be specified in the subclass:
    # _automatic_namelists = {
    #        'scf':   ['CONTROL', 'SYSTEM', 'ELECTRONS'],
    #        'nscf':  ['CONTROL', 'SYSTEM', 'ELECTRONS'],
    #        'bands': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
    #        'relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
    #        'md':    ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
    #        'vc-md':    ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
    #        'vc-relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
    #        }

    # Keywords that cannot be set
    # If the length of the tuple is three, the third value is the value that
    # will be automatically set.
    # Note that some values (ibrav, nat, ntyp, ...) are overridden anyway
    #     _blocked_keywords = [('CONTROL', 'pseudo_dir'), # set later
    #          ('CONTROL', 'outdir'),  # set later
    #          ('CONTROL', 'prefix'),  # set later
    #          ('SYSTEM', 'ibrav'),  # set later
    #          ('SYSTEM', 'celldm'),
    #          ('SYSTEM', 'nat'),  # set later
    #          ('SYSTEM', 'ntyp'),  # set later
    #          ('SYSTEM', 'a'), ('SYSTEM', 'b'), ('SYSTEM', 'c'),
    #     ('SYSTEM', 'cosab'), ('SYSTEM', 'cosac'), ('SYSTEM', 'cosbc'),
    # ]

    # _use_kpoints = False

    @classproperty
    def _baseclass_use_methods(cls):
        """
        This will be manually added to the _use_methods in each subclass
        """
        return {
            "structure": {
                'valid_types': StructureData,
                'additional_parameter': None,
                'linkname': 'structure',
                'docstring': "Choose the input structure to use",
            },
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
            "pseudo": {
                'valid_types': UpfData,
                'additional_parameter': "kind",
                'linkname': cls._get_linkname_pseudo,
                'docstring': (
                    "Use a node for the UPF pseudopotential of one of "
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
        }

    def _generate_PWCPinputdata(self,parameters,settings_dict,pseudos,structure,kpoints=None):
        """
        This method creates the content of an input file
        in the PW/CP format.
        :
        """
        from aiida.common.utils import get_unique_filename, get_suggestion
        import re
        local_copy_list_to_append = []

        # I put the first-level keys as uppercase (i.e., namelist and card names)
        # and the second-level keys as lowercase
        # (deeper levels are unchanged)
        input_params = _uppercase_dict(parameters.get_dict(),
                                       dict_name='parameters')
        input_params = {k: _lowercase_dict(v, dict_name=k)
                        for k, v in input_params.iteritems()}

        # I remove unwanted elements (for the moment, instead, I stop; to change when
        # we setup a reasonable logging)
        for blocked in self._blocked_keywords:
            nl = blocked[0].upper()
            flag = blocked[1].lower()
            defaultvalue = None
            if len(blocked) >= 3:
                defaultvalue = blocked[2]
            if nl in input_params:
                # The following lines is meant to avoid putting in input the
                # parameters like celldm(*)
                stripped_inparams = [re.sub("[(0-9)]", "", _)
                                     for _ in input_params[nl].keys()]
                if flag in stripped_inparams:
                    raise InputValidationError(
                        "You cannot specify explicitly the '{}' flag in the '{}' "
                        "namelist or card.".format(flag, nl))
                if defaultvalue is not None:
                    if nl not in input_params:
                        input_params[nl] = {}
                    input_params[nl][flag] = defaultvalue

        # Set some variables (look out at the case! NAMELISTS should be uppercase,
        # internal flag names must be lowercase)
        if 'CONTROL' not in input_params:
            input_params['CONTROL'] = {}
        input_params['CONTROL']['pseudo_dir'] = self._PSEUDO_SUBFOLDER
        input_params['CONTROL']['outdir'] = self._OUTPUT_SUBFOLDER
        input_params['CONTROL']['prefix'] = self._PREFIX

        input_params['CONTROL']['verbosity'] = input_params['CONTROL'].get(
            'verbosity',
            self._default_verbosity)  # Set to high if not specified

        # ============ I prepare the input site data =============
        # ------------ CELL_PARAMETERS -----------
        cell_parameters_card = "CELL_PARAMETERS angstrom\n"
        for vector in structure.cell:
            cell_parameters_card += ("{0:18.10f} {1:18.10f} {2:18.10f}"
                                     "\n".format(*vector))

        # ------------- ATOMIC_SPECIES ------------
        atomic_species_card_list = []

        # Keep track of the filenames to avoid to overwrite files
        # I use a dictionary where the key is the pseudo PK and the value
        # is the filename I used. In this way, I also use the same filename
        # if more than one kind uses the same pseudo.
        pseudo_filenames = {}

        # I keep track of the order of species
        kind_names = []
        # I add the pseudopotential files to the list of files to be copied
        for kind in structure.kinds:
            # This should not give errors, I already checked before that
            # the list of keys of pseudos and kinds coincides
            ps = pseudos[kind.name]
            if kind.is_alloy() or kind.has_vacancies():
                raise InputValidationError("Kind '{}' is an alloy or has "
                                           "vacancies. This is not allowed for pw.x input structures."
                                           "".format(kind.name))

            try:
                # It it is the same pseudopotential file, use the same filename
                filename = pseudo_filenames[ps.pk]
            except KeyError:
                # The pseudo was not encountered yet; use a new name and
                # also add it to the local copy list
                filename = get_unique_filename(ps.filename,
                                               pseudo_filenames.values())
                pseudo_filenames[ps.pk] = filename
                # I add this pseudo file to the list of files to copy
                local_copy_list_to_append.append((ps.get_file_abs_path(),
                                        os.path.join(self._PSEUDO_SUBFOLDER,
                                                     filename)))
            kind_names.append(kind.name)
            atomic_species_card_list.append("{} {} {}\n".format(
                kind.name.ljust(6), kind.mass, filename))

        # I join the lines, but I resort them using the alphabetical order of
        # species, given by the kind_names list. I also store the mapping_species
        # list, with the order of species used in the file
        mapping_species, sorted_atomic_species_card_list = zip(
            *sorted(zip(kind_names, atomic_species_card_list)))
        # The format of mapping_species required later is a dictionary, whose
        # values are the indices, so I convert to this format
        # Note the (idx+1) to convert to fortran 1-based lists
        mapping_species = {sp_name: (idx + 1) for idx, sp_name
                           in enumerate(mapping_species)}
        # I add the first line
        sorted_atomic_species_card_list = (["ATOMIC_SPECIES\n"] +
                                           list(
                                               sorted_atomic_species_card_list))
        atomic_species_card = "".join(sorted_atomic_species_card_list)
        # Free memory
        del sorted_atomic_species_card_list
        del atomic_species_card_list

        # ------------ ATOMIC_POSITIONS -----------
        atomic_positions_card_list = ["ATOMIC_POSITIONS angstrom\n"]

        # Check on validity of FIXED_COORDS
        fixed_coords_strings = []
        fixed_coords = settings_dict.pop('FIXED_COORDS', None)
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
                    raise InputValidationError(
                        "fixed_coords({:d}) has not length three"
                        "".format(i + 1))
                for fixed_c in this_atom_fix:
                    if not isinstance(fixed_c, bool):
                        raise InputValidationError(
                            "fixed_coords({:d}) has non-boolean "
                            "elements".format(i + 1))

                if_pos_values = [self._if_pos(_) for _ in this_atom_fix]
                fixed_coords_strings.append(
                    "  {:d} {:d} {:d}".format(*if_pos_values))

        for site, fixed_coords_string in zip(
                structure.sites, fixed_coords_strings):
            atomic_positions_card_list.append(
                "{0} {1:18.10f} {2:18.10f} {3:18.10f} {4}\n".format(
                    site.kind_name.ljust(6), site.position[0], site.position[1],
                    site.position[2], fixed_coords_string))
        atomic_positions_card = "".join(atomic_positions_card_list)
        del atomic_positions_card_list  # Free memory

        # velocities (to initialize MD, if set)
        atomic_velocities = settings_dict.pop('ATOMIC_VELOCITIES', None)
        if atomic_velocities is not None:
            # Checking if as many velocities are set as structures:
            if len(atomic_velocities) != len(structure.sites):
                raise InputValidationError(
                    "Input structure contains {:d} sites, but "
                    "atomic velocities has length {:d}".format(
                            len(structure.sites),
                            len(atomic_velocities)
                        )
                    )
            atomic_velocities_strings = ["ATOMIC_VELOCITIES\n"]
            for site, vel in zip(structure.sites, atomic_velocities):
                # Checking that all 3 dimension are specified:
                if len(vel) != 3:
                    raise InputValidationError(
                        "Velocities({}) for {} has not length three"
                        "".format(vel, site))
                # Appending to atomic_velocities_strings
                atomic_velocities_strings.append(
                    "{0} {1:18.10f} {2:18.10f} {3:18.10f}\n".format(
                            site.kind_name.ljust(6),
                            vel[0], vel[1], vel[2]
                        )
                    )
            # I append to atomic_positions_card  so that velocities 
            # are defined right after positions:
            atomic_positions_card = atomic_positions_card + "".join(atomic_velocities_strings)
            # Freeing the memory
            del atomic_velocities_strings
        # I set the variables that must be specified, related to the system
        # Set some variables (look out at the case! NAMELISTS should be
        # uppercase, internal flag names must be lowercase)
        if 'SYSTEM' not in input_params:
            input_params['SYSTEM'] = {}
        input_params['SYSTEM']['ibrav'] = 0
        input_params['SYSTEM']['nat'] = len(structure.sites)
        input_params['SYSTEM']['ntyp'] = len(structure.kinds)

        # ============ I prepare the k-points =============
        if self._use_kpoints:
            try:
                mesh, offset = kpoints.get_kpoints_mesh()
                has_mesh = True
                force_kpoints_list = settings_dict.pop('FORCE_KPOINTS_LIST',
                                                       False)
                if force_kpoints_list:
                    kpoints_list = kpoints.get_kpoints_mesh(print_list=True)
                    num_kpoints = len(kpoints_list)
                    has_mesh = False
                    weights = [1.] * num_kpoints

            except AttributeError:

                try:
                    kpoints_list = kpoints.get_kpoints()
                    num_kpoints = len(kpoints_list)
                    has_mesh = False
                    if num_kpoints == 0:
                        raise InputValidationError(
                            "At least one k point must be "
                            "provided for non-gamma calculations")
                except AttributeError:
                    raise InputValidationError(
                        "No valid kpoints have been found")

                try:
                    _, weights = kpoints.get_kpoints(also_weights=True)
                except AttributeError:
                    weights = [1.] * num_kpoints

            gamma_only = settings_dict.pop("GAMMA_ONLY", False)

            if gamma_only:
                if has_mesh:
                    if tuple(mesh) != (1, 1, 1) or tuple(offset) != (
                            0., 0., 0.):
                        raise InputValidationError(
                            "If a gamma_only calculation is requested, the "
                            "kpoint mesh must be (1,1,1),offset=(0.,0.,0.)")

                else:
                    if (len(kpoints_list) != 1 or
                                tuple(kpoints_list[0]) != tuple(0., 0., 0.)):
                        raise InputValidationError(
                            "If a gamma_only calculation is requested, the "
                            "kpoints coordinates must only be (0.,0.,0.)")

                kpoints_type = "gamma"

            elif has_mesh:
                kpoints_type = "automatic"

            else:
                kpoints_type = "crystal"

            kpoints_card_list = ["K_POINTS {}\n".format(kpoints_type)]

            if kpoints_type == "automatic":
                if any([(i != 0. and i != 0.5) for i in offset]):
                    raise InputValidationError("offset list must only be made "
                                               "of 0 or 0.5 floats")
                the_offset = [0 if i == 0. else 1 for i in offset]
                the_6_integers = list(mesh) + the_offset
                kpoints_card_list.append("{:d} {:d} {:d} {:d} {:d} {:d}\n"
                                         "".format(*the_6_integers))

            elif kpoints_type == "gamma":
                # nothing to be written in this case
                pass
            else:
                kpoints_card_list.append("{:d}\n".format(num_kpoints))
                for kpoint, weight in zip(kpoints_list, weights):
                    kpoints_card_list.append(
                        "  {:18.10f} {:18.10f} {:18.10f} {:18.10f}"
                        "\n".format(kpoint[0], kpoint[1], kpoint[2], weight))

            kpoints_card = "".join(kpoints_card_list)
            del kpoints_card_list

        # =================== NAMELISTS AND CARDS ========================
        try:
            namelists_toprint = settings_dict.pop('NAMELISTS')
            if not isinstance(namelists_toprint, list):
                raise InputValidationError(
                    "The 'NAMELISTS' value, if specified in the settings input "
                    "node, must be a list of strings")
        except KeyError:  # list of namelists not specified; do automatic detection
            try:
                control_nl = input_params['CONTROL']
                calculation_type = control_nl['calculation']
            except KeyError:
                raise InputValidationError(
                    "No 'calculation' in CONTROL namelist."
                    "It is required for automatic detection of the valid list "
                    "of namelists. Otherwise, specify the list of namelists "
                    "using the NAMELISTS key inside the 'settings' input node")

            try:
                namelists_toprint = self._automatic_namelists[calculation_type]
            except KeyError:
                sugg_string = get_suggestion(calculation_type,
                                             self._automatic_namelists.keys())
                raise InputValidationError("Unknown 'calculation' value in "
                                           "CONTROL namelist {}. Otherwise, specify the list of "
                                           "namelists using the NAMELISTS inside the 'settings' input "
                                           "node".format(sugg_string))

        inputfile = ""
        for namelist_name in namelists_toprint:
            inputfile += "&{0}\n".format(namelist_name)
            # namelist content; set to {} if not present, so that we leave an 
            # empty namelist
            namelist = input_params.pop(namelist_name, {})
            for k, v in sorted(namelist.iteritems()):
                inputfile += get_input_data_text(k, v, mapping=mapping_species)
            inputfile += "/\n"
    
        # Write cards now
        inputfile += atomic_species_card
        inputfile += atomic_positions_card
        if self._use_kpoints:
            inputfile += kpoints_card
        inputfile += cell_parameters_card
        #TODO: write CONSTRAINTS
        #TODO: write OCCUPATIONS
            
        if input_params:            
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))

        return inputfile, local_copy_list_to_append

    def _prepare_for_submission(self, tempfolder,
                                inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputs_dict (without the Code!)
        """
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
            structure = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("No structure specified for this calculation")
        if not isinstance(structure, StructureData):
            raise InputValidationError("structure is not of type StructureData")

        if self._use_kpoints:
            try:
                kpoints = inputdict.pop(self.get_linkname('kpoints'))
            except KeyError:
                raise InputValidationError("No kpoints specified for this calculation")
            if not isinstance(kpoints, KpointsData):
                raise InputValidationError("kpoints is not of type KpointsData")
        else:
            kpoints = None

        # Settings can be undefined, and defaults to an empty dictionary
        settings = inputdict.pop(self.get_linkname('settings'), None)
        if settings is None:
            settings_dict = {}
        else:
            if not isinstance(settings, ParameterData):
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

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this calculation")

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
        # I create the subfolder that will contain the pseudopotentials
        tempfolder.get_subfolder(self._PSEUDO_SUBFOLDER, create=True)
        # I create the subfolder with the output data (sometimes Quantum
        # Espresso codes crash if an empty folder is not already there
        tempfolder.get_subfolder(self._OUTPUT_SUBFOLDER, create=True)

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

        input_filecontent, local_copy_pseudo_list = self._generate_PWCPinputdata(parameters,settings_dict,pseudos,
                                                                                 structure,kpoints)
        local_copy_list += local_copy_pseudo_list

        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
        with open(input_filename, 'w') as infile:
            infile.write(input_filecontent)

        # operations for restart
        symlink = settings_dict.pop('PARENT_FOLDER_SYMLINK',
                                    self._default_symlink_usage)  # a boolean
        if symlink:
            if parent_calc_folder is not None:
                # I put the symlink to the old parent ./out folder
                remote_symlink_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                                  self._restart_copy_from),
                     self._restart_copy_to
                     ))
        else:
            # copy remote output dir, if specified
            if parent_calc_folder is not None:
                remote_copy_list.append(
                    (parent_calc_folder.get_computer().uuid,
                     os.path.join(parent_calc_folder.get_remote_path(),
                                  self._restart_copy_from),
                     self._restart_copy_to
                     ))

        # here we may create an aiida.EXIT file
        create_exit_file = settings_dict.pop('ONLY_INITIALIZATION', False)
        if create_exit_file:
            exit_filename = tempfolder.get_abs_path(
                '{}.EXIT'.format(self._PREFIX))
            with open(exit_filename, 'w') as f:
                f.write('\n')

        # Check if specific inputs for the ENVIRON module where specified
        environ_namelist = settings_dict.pop('ENVIRON', None)
        if environ_namelist is not None:
            if not isinstance(environ_namelist, dict):
                raise InputValidationError(
                    "ENVIRON namelist should be specified as a dictionary")
            # We first add the environ flag to the command-line options (if not already present)
            try:
                if '-environ' not in settings_dict['CMDLINE']:
                    settings_dict['CMDLINE'].append('-environ')
            except KeyError:
                settings_dict['CMDLINE'] = ['-environ']
            # To create a mapping from the species to an incremental fortran 1-based index
            # we use the alphabetical order as in the inputdata generation
            mapping_species = {sp_name: (idx+1) for idx, sp_name in 
                               enumerate(sorted([kind.name for kind in structure.kinds]))}
            environ_input_filename = tempfolder.get_abs_path(
                self._ENVIRON_INPUT_FILE_NAME)
            with open(environ_input_filename, 'w') as environ_infile:
                environ_infile.write("&ENVIRON\n")
                for k, v in sorted(environ_namelist.iteritems()):
                    environ_infile.write(
                        get_input_data_text(k, v, mapping=mapping_species))
                environ_infile.write("/\n")

        calcinfo = CalcInfo()

        calcinfo.uuid = self.uuid
        # Empty command line by default
        cmdline_params = settings_dict.pop('CMDLINE', [])
        # we commented calcinfo.stin_name and added it here in cmdline_params
        # in this way the mpirun ... pw.x ... < aiida.in
        # is replaced by mpirun ... pw.x ... -in aiida.in
        # in the scheduler, _get_run_line, if cmdline_params is empty, it
        # simply uses < calcinfo.stin_name
        calcinfo.cmdline_params = (list(cmdline_params)
                                   + ["-in", self._INPUT_FILE_NAME])
        # calcinfo.stdin_name = self._INPUT_FILE_NAME
        # calcinfo.stdout_name = self._OUTPUT_FILE_NAME

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = (list(cmdline_params)
                                   + ["-in", self._INPUT_FILE_NAME])
        # calcinfo.stdin_name = self._INPUT_FILE_NAME
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list

        # Retrieve by default the output file and the xml file
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append(self._DATAFILE_XML)
        settings_retrieve_list = settings_dict.pop('ADDITIONAL_RETRIEVE_LIST',
                                                   [])

        if settings_dict.pop('ALSO_BANDS', False):
            # To retrieve also the bands data
            settings_retrieve_list.append([os.path.join(self._OUTPUT_SUBFOLDER,
                                                        self._PREFIX + '.save',
                                                        'K*[0-9]',
                                                        'eigenval*.xml'),
                                           '.',
                                           2])

        calcinfo.retrieve_list += settings_retrieve_list
        calcinfo.retrieve_list += self._internal_retrieve_list

        try:
            Parserclass = self.get_parserclass()
            parser = Parserclass(self)
            parser_opts = parser.get_parser_settings_key()
            settings_dict.pop(parser_opts)
        except (KeyError, AttributeError):
            # the key parser_opts isn't inside the dictionary
            pass

        if settings_dict:
            raise InputValidationError("The following keys have been found in "
                                       "the settings input node, but were not understood: {}".format(
                ",".join(settings_dict.keys())))

        return calcinfo

    def _if_pos(self, fixed):
        """
        Simple function that returns 0 if fixed is True, 1 otherwise.
        Useful to convert from the boolean value of fixed_coords to the value required
        by Quantum Espresso as if_pos.
        """
        if fixed:
            return 0
        else:
            return 1

    @classmethod
    def _get_linkname_pseudo_prefix(cls):
        """
        The prefix for the name of the link used for each pseudo before the kind name
        """
        return "pseudo_"

    @classmethod
    def _get_linkname_pseudo(cls, kind):
        """
        The name of the link used for the pseudo for kind 'kind'.
        It appends the pseudo name to the pseudo_prefix, as returned by the
        _get_linkname_pseudo_prefix() method.

        :note: if a list of strings is given, the elements are appended
          in the same order, separated by underscores

        :param kind: a string (or list of strings) for the atomic kind(s) for
            which we want to get the link name
        """
        # If it is a list of strings, and not a single string: join them
        # by underscore
        if isinstance(kind, (tuple, list)):
            suffix_string = "_".join(kind)
        elif isinstance(kind, basestring):
            suffix_string = kind
        else:
            raise TypeError("The parameter 'kind' of _get_linkname_pseudo can "
                            "only be a string or a list of strings")
        return "{}{}".format(cls._get_linkname_pseudo_prefix(), suffix_string)

    def use_pseudos_from_family(self, family_name):
        """
        Set the pseudo to use for all atomic kinds, picking pseudos from the
        family with name family_name.

        :note: The structure must already be set.

        :param family_name: the name of the group containing the pseudos
        """
        from collections import defaultdict

        try:
            structure = self._get_reference_structure()
        except AttributeError:
            raise ValueError("Structure is not set yet! Therefore, the method "
                             "use_pseudos_from_family cannot automatically set "
                             "the pseudos")

        # A dict {kind_name: pseudo_object}
        kind_pseudo_dict = get_pseudos_from_structure(structure, family_name)

        # We have to group the species by pseudo, I use the pseudo PK
        # pseudo_dict will just map PK->pseudo_object
        pseudo_dict = {}
        # Will contain a list of all species of the pseudo with given PK
        pseudo_species = defaultdict(list)

        for kindname, pseudo in kind_pseudo_dict.iteritems():
            pseudo_dict[pseudo.pk] = pseudo
            pseudo_species[pseudo.pk].append(kindname)

        for pseudo_pk in pseudo_dict:
            pseudo = pseudo_dict[pseudo_pk]
            kinds = pseudo_species[pseudo_pk]
            # I set the pseudo for all species, sorting alphabetically
            self.use_pseudo(pseudo, sorted(kinds))

    def _get_reference_structure(self):
        """
        Used to get the reference structure to obtain which 
        pseudopotentials to use from a given family using 
        use_pseudos_from_family. 
        
        :note: this method can be redefined in a given subclass
               to specify which is the reference structure to consider.
        """
        return self.get_inputs_dict()[self.get_linkname('structure')]

    def _set_parent_remotedata(self, remotedata):
        """
        Used to set a parent remotefolder in the restart of ph.
        """
        from aiida.common.exceptions import ValidationError

        if not isinstance(remotedata, RemoteData):
            raise ValueError('remotedata must be a RemoteData')

        # complain if another remotedata is already found
        input_remote = self.get_inputs(node_type=RemoteData)
        if input_remote:
            raise ValidationError("Cannot set several parent calculation to a "
                                  "{} calculation".format(
                self.__class__.__name__))

        self.use_parent_folder(remotedata)

    def create_restart(self, force_restart=False, parent_folder_symlink=None,
                       use_output_structure=False,
                       restart_from_beginning=False):
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
        :param bool use_output_structure: if True, the output structure
           of the restarted calculation is used if available, rather than its
           input structure. Useful for nscf or bands calculations, but it
           SHOULD NOT be used for the restart of a relaxation run.
           Default=False.
        :param bool restart_from_beginning: If set to True, creates a copy of
           the parent calculation, without using the scratch for the restart.
           Useful to restart calculations that have crashed on the cluster for
           external reasons. Default=False
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

        if restart_from_beginning:
            inp_dict = calc_inp[self.get_linkname('parameters')]
        else:  # case of restart without using the parent scratch
            old_inp_dict = calc_inp[self.get_linkname('parameters')].get_dict()
            # add the restart flag
            old_inp_dict['CONTROL']['restart_mode'] = 'restart'
            inp_dict = ParameterData(dict=old_inp_dict)

        remote_folders = self.get_outputs(type=RemoteData)
        if len(remote_folders) != 1:
            raise InputValidationError("More than one output RemoteData found "
                                       "in calculation {}".format(self.pk))
        remote_folder = remote_folders[0]

        c2 = self.copy()

        # if not 'Restart' in c2.label:
        #    labelstring = c2.label + " Restart of {} {}.".format(
        #                                self.__class__.__name__,self.pk)
        # else:
        #    labelstring = " Restart of {} {}.".format(self.__class__.__name__,self.pk)
        # c2.label = labelstring.lstrip()

        # set the new links
        c2.use_parameters(inp_dict)
        if use_output_structure:
            # use OUTPUT structure if available
            try:
                c2.use_structure(self.out.output_structure)
            except AttributeError:
                c2.use_structure(calc_inp[self.get_linkname('structure')])
        else:
            c2.use_structure(calc_inp[self.get_linkname('structure')])

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
                c2.add_link_from(input_node, label=linkname)

        # Add also the vdw table, if the parent had one
        try:
            old_vdw_table = calc_inp[self.get_linkname('vdw_table')]
        except KeyError:
            # No VdW table
            pass
        else:
            c2.use_vdw_table(old_vdw_table)

        return c2


def get_input_data_text(key, val, mapping=None):
    """
    Given a key and a value, return a string (possibly multiline for arrays)
    with the text to be added to the input file.

    :param key: the flag name
    :param val: the flag value. If it is an array, a line for each element
            is produced, with variable indexing starting from 1.
            Each value is formatted using the conv_to_fortran function.
    :param mapping: Optional parameter, must be provided if val is a dictionary.
            It maps each key of the 'val' dictionary to the corresponding
            list index. For instance, if ``key='magn'``,
            ``val = {'Fe': 0.1, 'O': 0.2}`` and ``mapping = {'Fe': 2, 'O': 1}``,
            this function will return the two lines ``magn(1) = 0.2`` and
            ``magn(2) = 0.1``. This parameter is ignored if 'val'
            is not a dictionary.
    """
    from aiida.common.utils import conv_to_fortran
    # I don't try to do iterator=iter(val) and catch TypeError because
    # it would also match strings
    # I check first the dictionary, because it would also match hasattr(__iter__)
    if isinstance(val, dict):
        if mapping is None:
            raise ValueError("If 'val' is a dictionary, you must provide also "
                             "the 'mapping' parameter")

        # At difference with the case of a list, at the beginning list_of_strings
        # is a list of 2-tuples where the first element is the idx, and the
        # second is the actual line. This is used at the end to resort everything.
        list_of_strings = []
        for elemk, itemval in val.iteritems():
            try:
                idx = mapping[elemk]
            except KeyError:
                raise ValueError("Unable to find the key '{}' in the mapping "
                                 "dictionary".format(elemk))

            list_of_strings.append((idx, "  {0}({2}) = {1}\n".format(
                key, conv_to_fortran(itemval), idx)))

        # I first have to resort, then to remove the index from the first
        # column, finally to join the strings
        list_of_strings = zip(*sorted(list_of_strings))[1]
        return "".join(list_of_strings)
    elif hasattr(val, '__iter__'):
        # a list/array/tuple of values
        list_of_strings = [
            "  {0}({2}) = {1}\n".format(key, conv_to_fortran(itemval),
                                        idx + 1)
            for idx, itemval in enumerate(val)]
        return "".join(list_of_strings)
    else:
        # single value
        return "  {0} = {1}\n".format(key, conv_to_fortran(val))


def _lowercase_dict(d, dict_name):
    from collections import Counter

    if isinstance(d, dict):
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

    if isinstance(d, dict):
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
