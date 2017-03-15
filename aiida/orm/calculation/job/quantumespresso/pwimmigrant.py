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
Plugin to immigrate a Quantum Espresso pw.x job that was not run using AiiDa.
"""
# TODO: Document the current limitations (e.g. ibrav == 0)
import os
from copy import deepcopy
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.orm.calculation.job import _input_subfolder
from aiida.orm.data.remote import RemoteData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.upf import UpfData
from aiida.common.folders import SandboxFolder
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import (FeatureNotAvailable, InvalidOperation,
                                     InputValidationError)
from aiida.common.links import LinkType
from aiida.tools.codespecific.quantumespresso import pwinputparser




class PwimmigrantCalculation(PwCalculation):
    """
    Create a PwCalculation object that can be used to import old jobs.

    This is a sublass of aiida.orm.calculation.quantumespresso.PwCalculation
    with slight modifications to some of the class variables and additional
    methods that

        a. parse the job's input file to create the calculation's input
           nodes that would exist if the calculation were submitted using AiiDa,
        b. bypass the functions of the daemon, and prepare the node's attributes
           such that all the processes (copying of the files to the repository,
           results parsing, ect.) can be performed

    .. note:: The keyword arguments of PwCalculation are also available.

    :param remote_workdir: Absolute path to the directory where the job was run.
        The transport of the computer you link ask input to the calculation is
        the transport that will be used to retrieve the calculation's files.
        Therefore, ``remote_workdir`` should be the absolute path to the job's
        directory on that computer.
    :type remote_workdir: str

    :param input_file_name: The file name of the job's input file.
    :type input_file_name: str

    :param output_file_name: The file name of the job's output file (i.e. the
        file containing the stdout of QE).
    :type output_file_name: str
    """

    def _init_internal_params(self):

        super(PwimmigrantCalculation, self)._init_internal_params()

    def create_input_nodes(self, open_transport, input_file_name=None,
                           output_file_name=None, remote_workdir=None):
        """
        Create calculation input nodes based on the job's files.

        :param open_transport: An open instance of the transport class of the
            calculation's computer. See the tutorial for more information.
        :type open_transport: :py:class:`aiida.transport.plugins.local.LocalTransport`
            | :py:class:`aiida.transport.plugins.ssh.SshTransport`

        This method parses the files in the job's remote working directory to
        create the input nodes that would exist if the calculation were
        submitted using AiiDa. These nodes are

            * a ``'parameters'`` ParameterData node, based on the namelists and
              their variable-value pairs;
            * a ``'kpoints'`` KpointsData node, based on the *K_POINTS* card;
            * a ``'structure'`` StructureData node, based on the
              *ATOMIC_POSITIONS* and *CELL_PARAMETERS* cards;
            * one ``'pseudo_X'`` UpfData node for the pseudopotential used for
              the atomic species with name ``X``, as specified in the
              *ATOMIC_SPECIES* card;
            * a ``'settings'`` ParameterData node, if there are any fixed
              coordinates, or if the gamma kpoint is used;

        and can be retrieved as a dictionary using the ``get_inputs_dict()``
        method. *These input links are cached-links; nothing is stored by this
        method (including the calculation node itself).*

        .. note:: QE stores the calculation's pseudopotential files in the
            ``<outdir>/<prefix>.save/`` subfolder of the job's working
            directory, where ``outdir`` and ``prefix`` are QE *CONTROL*
            variables (see
            `pw input file description <http://www.quantum-espresso.org/wp-content/uploads/Doc/INPUT_PW.html>`_).
            This method uses these files to either get--if the a node already
            exists for the pseudo--or create a UpfData node for each
            pseudopotential.


        **Keyword arguments**

        .. note:: These keyword arguments can also be set when instantiating the
            class or using the ``set_`` methods (e.g. ``set_remote_workdir``).
            Offering to set them here simply offers the user an additional
            place to set their values. *Only the values that have not yet been
            set need to be specified.*

        :param input_file_name: The file name of the job's input file.
        :type input_file_name: str

        :param output_file_name: The file name of the job's output file (i.e.
            the file containing the stdout of QE).
        :type output_file_name: str

        :param remote_workdir: Absolute path to the directory where the job
            was run. The transport of the computer you link ask input to the
            calculation is the transport that will be used to retrieve the
            calculation's files. Therefore, ``remote_workdir`` should be the
            absolute path to the job's directory on that computer.
        :type remote_workdir: str

        :raises aiida.common.exceptions.InputValidationError: if
            ``open_transport`` is a different type of transport than the
            computer's.
        :raises aiida.common.exceptions.InvalidOperation: if
            ``open_transport`` is not open.
        :raises aiida.common.exceptions.InputValidationError: if
            ``remote_workdir``, ``input_file_name``, and/or ``output_file_name``
            are not set prior to or during the call of this method.
        :raises aiida.common.exceptions.FeatureNotAvailable: if the input file
            uses anything other than ``ibrav = 0``, which is not currently
            implimented in aiida.
        :raises aiida.common.exceptions.ParsingError: if there are issues
            parsing the input file.
        :raises IOError: if there are issues reading the input file.
        """
        import re
        # Make sure the remote workdir and input + output file names were
        # provided either before or during the call to this method. If they
        # were just provided during this method call, store the values.
        if remote_workdir is not None:
            self.set_remote_workdir(remote_workdir)
        elif self.get_attr('remote_workdir', None) is None:
            raise InputValidationError(
                'The remote working directory has not been specified.\n'
                'Please specify it using one of the following...\n '
                '(a) pass as a keyword argument to create_input_nodes\n'
                '    [create_input_nodes(remote_workdir=your_remote_workdir)]\n'
                '(b) pass as a keyword argument when instantiating\n '
                '    [calc = PwCalculationImport(remote_workdir='
                'your_remote_workdir)]\n'
                '(c) use the set_remote_workdir method\n'
                '    [calc.set_remote_workdir(your_remote_workdir)]'
            )
        if input_file_name is not None:
            self._INPUT_FILE_NAME = input_file_name
        elif self._INPUT_FILE_NAME is None:
            raise InputValidationError(
                'The input file_name has not been specified.\n'
                'Please specify it using one of the following...\n '
                '(a) pass as a keyword argument to create_input_nodes\n'
                '    [create_input_nodes(input_file_name=your_file_name)]\n'
                '(b) pass as a keyword argument when instantiating\n '
                '    [calc = PwCalculationImport(input_file_name='
                'your_file_name)]\n'
                '(c) use the set_input_file_name method\n'
                '    [calc.set_input_file_name(your_file_name)]'
            )
        if output_file_name is not None:
            self._OUTPUT_FILE_NAME = output_file_name
        elif self._OUTPUT_FILE_NAME is None:
            raise InputValidationError(
                'The input file_name has not been specified.\n'
                'Please specify it using one of the following...\n '
                '(a) pass as a keyword argument to create_input_nodes\n'
                '    [create_input_nodes(output_file_name=your_file_name)]\n'
                '(b) pass as a keyword argument when instantiating\n '
                '    [calc = PwCalculationImport(output_file_name='
                'your_file_name)]\n'
                '(c) use the set_output_file_name method\n'
                '    [calc.set_output_file_name(your_file_name)]'
            )

        # Check that open_transport is the correct transport type.
        if type(open_transport) is not self.get_computer().get_transport_class():
            raise InputValidationError(
                "The transport passed as the `open_transport` parameter is "
                "not the same transport type linked to the computer. Please "
                "obtain the correct transport class using the "
                "`get_transport_class` method of the calculation's computer. "
                "See the tutorial for more information."
            )

        # Check that open_transport is actually open.
        if not open_transport._is_open:
            raise InvalidOperation(
                "The transport passed as the `open_transport` parameter is "
                "not open. Please execute the open the transport using it's "
                "`open` method, or execute the call to this method within a "
                "`with` statement context guard. See the tutorial for more "
                "information."
            )

        # Copy the input file and psuedo files to a temp folder for parsing.
        with SandboxFolder() as folder:

            # Copy the input file to the temp folder.
            remote_path = os.path.join(self._get_remote_workdir(),
                                       self._INPUT_FILE_NAME)
            open_transport.get(remote_path, folder.abspath)

            # Parse the input file.
            local_path = os.path.join(folder.abspath, self._INPUT_FILE_NAME)
            with open(local_path) as fin:
                pwinputfile = pwinputparser.PwInputFile(fin)


            # Determine PREFIX, if it hasn't already been set by the user.
            if self._PREFIX is None:
                control_dict = pwinputfile.namelists['CONTROL']
                # If prefix is not set in input file, use the default,
                # 'pwscf'.
                self._PREFIX = control_dict.get('prefix', 'pwscf')

            # Determine _OUTPUT_SUBFOLDER, if it hasn't already been set by
            # the user.
            # TODO: Prompt user before using the environment variable???
            if self._OUTPUT_SUBFOLDER is None:
                # See if it's specified in the CONTROL namelist.
                control_dict = pwinputfile.namelists['CONTROL']
                self._OUTPUT_SUBFOLDER = control_dict.get('outdir', None)
                if self._OUTPUT_SUBFOLDER is None:
                    # See if the $ESPRESSO_TMPDIR is set.
                    envar = open_transport.exec_command_wait(
                        'echo $ESPRESSO_TMPDIR'
                    )[1]
                    if len(envar.strip()) > 0:
                        self._OUTPUT_SUBFOLDER = envar.strip()
                    else:
                        # Use the default dir--the dir job was submitted in.
                        self._OUTPUT_SUBFOLDER = self._get_remote_workdir()

            # Copy the pseudo files to the temp folder.
            for fnm in pwinputfile.atomic_species['pseudo_file_names']:
                remote_path = os.path.join(self._get_remote_workdir(),
                                           self._OUTPUT_SUBFOLDER,
                                           '{}.save/'.format(self._PREFIX),
                                           fnm)
                open_transport.get(remote_path, folder.abspath)

            # Make sure that ibrav = 0, since aiida doesn't support anything
            # else.
            if pwinputfile.namelists['SYSTEM']['ibrav'] != 0:
                raise FeatureNotAvailable(
                    'Found ibrav !=0 while parsing the input file. '
                    'Currently, AiiDa only supports ibrav = 0.'
                )

            # Create ParameterData node based on the namelist and link as input.

            # First, strip the namelist items that aiida doesn't allow or sets
            # later.
            # NOTE: ibrav = 0 is checked above.
            # NOTE: If any of the position or cell units are in alat or crystal
            # units, that will be taken care of by the input parsing tools, and
            # we are safe to fake that they were never there in the first place.
            parameters_dict = deepcopy(pwinputfile.namelists)
            for namelist, blocked_key in self._blocked_keywords:
                keys = parameters_dict[namelist].keys()
                for this_key in parameters_dict[namelist].keys():
                    # take into account that celldm and celldm(*) must be blocked
                    if re.sub("[(0-9)]", "", this_key) == blocked_key:
                        parameters_dict[namelist].pop(this_key, None)

            parameters = ParameterData(dict=parameters_dict)
            self.use_parameters(parameters)

            # Initialize the dictionary for settings parameter data for possible
            # use later for gamma kpoint and fixed coordinates.
            settings_dict = {}

            # Create a KpointsData node based on the K_POINTS card block
            # and link as input.
            kpointsdata = pwinputfile.get_kpointsdata()
            self.use_kpoints(kpointsdata)
            # If only the gamma kpoint is used, add to the settings dictionary.
            if pwinputfile.k_points['type'] == 'gamma':
                settings_dict['gamma_only'] = True

            # Create a StructureData node based on the ATOMIC_POSITIONS,
            # CELL_PARAMETERS, and ATOMIC_SPECIES card blocks, and link as
            # input.
            structuredata = pwinputfile.get_structuredata()
            self.use_structure(structuredata)

            # Get or create a UpfData node for the pseudopotentials used for
            # the calculation.
            names = pwinputfile.atomic_species['names']
            pseudo_file_names = pwinputfile.atomic_species['pseudo_file_names']
            for name, fnm in zip(names, pseudo_file_names):
                local_path = os.path.join(folder.abspath, fnm)
                pseudo, created = UpfData.get_or_create(local_path)
                self.use_pseudo(pseudo, kind=name)

        # If there are any fixed coordinates (i.e. force modification
        # present in the input file, create a ParameterData node for these
        # special settings.
        fixed_coords = pwinputfile.atomic_positions['fixed_coords']
        # NOTE: any() only works for 1-dimensional lists.
        if any((any(fc_xyz) for fc_xyz in fixed_coords)):
            settings_dict['FIXED_COORDS'] = fixed_coords

        # If the settings_dict has been filled in, create a ParameterData
        # node from it and link as input.
        if settings_dict:
            self.use_settings(ParameterData(dict=settings_dict))

        self._set_attr('input_nodes_created', True)

    def _prepare_for_retrieval(self, open_transport):
        """
        Prepare the calculation for retrieval by daemon.

        :param open_transport: An open instance of the transport class of the
            calculation's computer.
        :type open_transport: :py:class:`aiida.transport.plugins.local.LocalTransport`
            | :py:class:`aiida.transport.plugins.ssh.SshTransport`

        Here, we

            * manually set the files to retrieve
            * store the calculation and all it's input nodes
            * copy the input file to the calculation's raw_input_folder in the
            * store the remote_workdir as a RemoteData output node

        """

        # Manually set the files that will be copied to the repository and that
        # the parser will extract the results from. This would normally be
        # performed in self._prepare_for_submission prior to submission.
        self._set_attr('retrieve_list',
                       [self._OUTPUT_FILE_NAME, self._DATAFILE_XML])
        self._set_attr('retrieve_singlefile_list', [])

        # Make sure the calculation and input links are stored.
        self.store_all()

        # Store the original input file in the calculation's repository folder.
        remote_path = os.path.join(self._get_remote_workdir(),
                                   self._INPUT_FILE_NAME)
        raw_input_folder = self.folder.get_subfolder(_input_subfolder,
                                                     create=True)
        open_transport.get(remote_path, raw_input_folder.abspath)

        # Manually add the remote working directory as a RemoteData output
        # node.
        self._set_state(calc_states.SUBMITTING)
        remotedata = RemoteData(computer=self.get_computer(),
                                remote_path=self._get_remote_workdir())
        remotedata.add_link_from(self, label='remote_folder',
                                 link_type=LinkType.CREATE)
        remotedata.store()

    def prepare_for_retrieval_and_parsing(self, open_transport):
        """
        Tell the daemon that the calculation is computed and ready to be parsed.

        :param open_transport: An open instance of the transport class of the
            calculation's computer. See the tutorial for more information.
        :type open_transport: :py:class:`aiida.transport.plugins.local.LocalTransport`
            | :py:class:`aiida.transport.plugins.ssh.SshTransport`

        The next time the daemon updates the status of calculations, it will
        see this job is in the 'COMPUTED' state and will retrieve its output
        files and parse the results.

        If the daemon is not currently running, nothing will happen until it is
        started again.

        This method also stores the calculation and all input nodes. It also
        copies the original input file to the calculation's repository folder.

        :raises aiida.common.exceptions.InputValidationError: if
            ``open_transport`` is a different type of transport than the
            computer's.
        :raises aiida.common.exceptions.InvalidOperation: if
            ``open_transport`` is not open.
        """

        # Check that the create_input_nodes method has run successfully.
        if not self.get_attr('input_nodes_created', False):
            raise InvalidOperation(
                "You must run the create_input_nodes method before calling "
                "prepare_for_retrieval_and_parsing!"
            )

        # Check that open_transport is the correct transport type.
        if type(open_transport) is not self.get_computer().get_transport_class():
            raise InputValidationError(
                "The transport passed as the `open_transport` parameter is "
                "not the same transport type linked to the computer. Please "
                "obtain the correct transport class using the "
                "`get_transport_class` method of the calculation's computer. "
                "See the tutorial for more information."
            )

        # Check that open_transport is actually open.
        if not open_transport._is_open:
            raise InvalidOperation(
                "The transport passed as the `open_transport` parameter is "
                "not open. Please execute the open the transport using it's "
                "`open` method, or execute the call to this method within a "
                "`with` statement context guard. See the tutorial for more "
                "information."
            )

        # Prepare the calculation for retrieval
        self._prepare_for_retrieval(open_transport)

        # Manually set the state of the calculation to "COMPUTED", so that it
        # will be retrieved and parsed the next time the daemon updates the
        # status of calculations.
        self._set_state(calc_states.COMPUTED)

    def set_remote_workdir(self, remote_workdir):
        """
        Set the job's remote working directory.

        :param remote_workdir: Absolute path of the job's remote working
            directory.
        :type remote_workdir: str
        """
        # This is the functionality as self._set_remote_workir, but it bypasses
        # the need to have the calculation state set as SUBMITTING.
        self._set_attr('remote_workdir', remote_workdir)

    def set_output_subfolder(self, output_subfolder):
        """
        Manually set the job's ``outdir`` variable (e.g. ``'./out/'``).

        .. note:: The outdir variable is normally set automatically by

                1. looking for the ``outdir`` ``CONTROL`` namelist variable
                2. looking for the ``$ESPRESSO_TMPDIR`` environment variable
                   on the calculation's computer (using the transport)
                3. using the QE default, the calculation's ``remote_workdir``

            but this method is made available to the user, in the event that
            they wish to set it manually.

        :param output_subfolder: The job's outdir variable.
        :type output_subfolder: str
        """
        self._OUTPUT_SUBFOLDER = output_subfolder

    def set_prefix(self, prefix):
        """
        Manually set the job's ``prefix`` variable (e.g. ``'pwscf'``).

        .. note:: The prefix variable is normally set automatically by

                1. looking for the ``prefix`` ``CONTROL`` namelist variable
                2. using the QE default, ``'pwscf'``

            but this method is made available to the user, in the event that
            they wish to set it manually.

        :param prefix: The job's prefix variable.
        :type prefix: str
        """
        self._PREFIX = prefix

    def set_input_file_name(self, input_file_name):
        """
        Set the file name of the job's input file (e.g. ``'pw.in'``).

        :param input_file_name: The file name of the job's input file.
        :type input_file_name: str
        """
        self._INPUT_FILE_NAME = input_file_name

    def set_output_file_name(self, output_file_name):
        """Set the file name of the job's output file (e.g. ``'pw.out'``).

        :param output_file_name: The file name of file containing the job's
            stdout.
        :type output_file_name: str
        """
        self._OUTPUT_FILE_NAME = output_file_name

    # These value are set as class attributes in the parent class,
    # BasePwInputGenerator, but they will be different for a job that wasn't
    # run using aiida, and they will likely vary from job to job. Therefore,
    # we override the parent class's attributes using properties, whose
    # setter methods store the values as db attributes, and whose getter
    # methods retrieve the stored values from the db.

    @property
    def _OUTPUT_SUBFOLDER(self):
        return self.get_attr('output_subfolder', None)

    @_OUTPUT_SUBFOLDER.setter
    def _OUTPUT_SUBFOLDER(self, value):
        self._set_attr('output_subfolder', value)

    @property
    def _PREFIX(self):
        return self.get_attr('prefix', None)

    @_PREFIX.setter
    def _PREFIX(self, value):
        self._set_attr('prefix', value)

    @property
    def _INPUT_FILE_NAME(self):
        return self.get_attr('input_file_name', None)

    @_INPUT_FILE_NAME.setter
    def _INPUT_FILE_NAME(self, value):
        self._set_attr('input_file_name', value)

    @property
    def _OUTPUT_FILE_NAME(self):
        return self.get_attr('output_file_name', None)

    @_OUTPUT_FILE_NAME.setter
    def _OUTPUT_FILE_NAME(self, value):
        self._set_attr('output_file_name', value)

    @property
    def _DATAFILE_XML(self):
        path = os.path.join(self._OUTPUT_SUBFOLDER,
                            '{}.save'.format(self._PREFIX),
                            self._DATAFILE_XML_BASENAME)
        return path

    @_DATAFILE_XML.setter
    def _DATAFILE_XML(self, value):
        # Don't store this value in the db, since it gets set to the Aiida
        # default in the parent class.
        pass
