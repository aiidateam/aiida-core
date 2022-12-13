# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines
"""Implementation of the CalcJob process."""
from __future__ import annotations

import dataclasses
import io
import json
import os
import shutil
from typing import Any, Dict, Hashable, Optional, Type, Union

import plumpy.ports
import plumpy.process_states

from aiida import orm
from aiida.common import AttributeDict, exceptions
from aiida.common.datastructures import CalcInfo
from aiida.common.folders import Folder
from aiida.common.lang import classproperty, override
from aiida.common.links import LinkType

from ..exit_code import ExitCode
from ..ports import PortNamespace
from ..process import Process, ProcessState
from ..process_spec import CalcJobProcessSpec
from .importer import CalcJobImporter
from .monitors import CalcJobMonitor
from .tasks import UPLOAD_COMMAND, Waiting

__all__ = ('CalcJob',)


def validate_calc_job(inputs: Any, ctx: PortNamespace) -> Optional[str]:  # pylint: disable=too-many-return-statements
    """Validate the entire set of inputs passed to the `CalcJob` constructor.

    Reasons that will cause this validation to raise an `InputValidationError`:

     * No `Computer` has been specified, neither directly in `metadata.computer` nor indirectly through the `Code` input
     * The specified computer is not stored
     * The `Computer` specified in `metadata.computer` is not the same as that of the specified `Code`
     * No `Code` has been specified and no `remote_folder` input has been specified, i.e. this is no import run

    :return: string with error message in case the inputs are invalid
    """
    try:
        ctx.get_port('code')
        ctx.get_port('metadata.computer')
    except ValueError:
        # If the namespace no longer contains the `code` or `metadata.computer` ports we skip validation
        return None

    remote_folder = inputs.get('remote_folder', None)

    if remote_folder is not None:
        # The `remote_folder` input has been specified and so this concerns an import run, which means that neither
        # a `Code` nor a `Computer` are required. However, they are allowed to be specified but will not be explicitly
        # checked for consistency.
        return None

    code = inputs.get('code', None)
    computer_from_code = code.computer
    computer_from_metadata = inputs.get('metadata', {}).get('computer', None)

    if not computer_from_code and not computer_from_metadata:
        return 'no computer has been specified in `metadata.computer` nor via `code`.'

    if computer_from_code and not computer_from_code.is_stored:
        return f'the Computer<{computer_from_code}> is not stored'

    if computer_from_metadata and not computer_from_metadata.is_stored:
        return f'the Computer<{computer_from_metadata}> is not stored'

    if computer_from_code and computer_from_metadata and computer_from_code.uuid != computer_from_metadata.uuid:
        return (
            'Computer<{}> explicitly defined in `metadata.computer` is different from Computer<{}> which is the '
            'computer of Code<{}> defined as the `code` input.'.format(
                computer_from_metadata, computer_from_code, code
            )
        )

    try:
        resources_port = ctx.get_port('metadata.options.resources')
    except ValueError:
        return None

    # If the resources port exists but is not required, we don't need to validate it against the computer's scheduler
    if not resources_port.required:
        return None

    computer = computer_from_code or computer_from_metadata
    scheduler = computer.get_scheduler()
    try:
        resources = inputs['metadata']['options']['resources']
    except KeyError:
        return 'input `metadata.options.resources` is required but is not specified'

    scheduler.preprocess_resources(resources, computer.get_default_mpiprocs_per_machine())

    try:
        scheduler.validate_resources(**resources)
    except ValueError as exception:
        return f'input `metadata.options.resources` is not valid for the `{scheduler}` scheduler: {exception}'

    return None


def validate_stash_options(stash_options: Any, _: Any) -> Optional[str]:
    """Validate the ``stash`` options."""
    from aiida.common.datastructures import StashMode

    target_base = stash_options.get('target_base', None)
    source_list = stash_options.get('source_list', None)
    stash_mode = stash_options.get('mode', StashMode.COPY.value)

    if not isinstance(target_base, str) or not os.path.isabs(target_base):
        return f'`metadata.options.stash.target_base` should be an absolute filepath, got: {target_base}'

    if (
        not isinstance(source_list, (list, tuple)) or
        any(not isinstance(src, str) or os.path.isabs(src) for src in source_list)
    ):
        port = 'metadata.options.stash.source_list'
        return f'`{port}` should be a list or tuple of relative filepaths, got: {source_list}'

    try:
        StashMode(stash_mode)
    except ValueError:
        port = 'metadata.options.stash.mode'
        return f'`{port}` should be a member of aiida.common.datastructures.StashMode, got: {stash_mode}'

    return None


def validate_monitors(monitors: Any, _: PortNamespace) -> Optional[str]:
    """Validate the ``monitors`` input namespace."""
    for key, monitor_node in monitors.items():
        try:
            CalcJobMonitor(**monitor_node.get_dict())
        except (exceptions.EntryPointError, TypeError, ValueError) as exception:
            return f'`monitors.{key}` is invalid: {exception}'
    return None


def validate_parser(parser_name: Any, _: PortNamespace) -> Optional[str]:
    """Validate the parser.

    :return: string with error message in case the inputs are invalid
    """
    from aiida.plugins import ParserFactory

    try:
        ParserFactory(parser_name)
    except exceptions.EntryPointError as exception:
        return f'invalid parser specified: {exception}'

    return None


def validate_additional_retrieve_list(additional_retrieve_list: Any, _: Any) -> Optional[str]:
    """Validate the additional retrieve list.

    :return: string with error message in case the input is invalid.
    """
    if any(not isinstance(value, str) or os.path.isabs(value) for value in additional_retrieve_list):
        return f'`additional_retrieve_list` should only contain relative filepaths but got: {additional_retrieve_list}'

    return None


class CalcJob(Process):
    """Implementation of the CalcJob process."""

    _node_class = orm.CalcJobNode
    _spec_class = CalcJobProcessSpec
    link_label_retrieved: str = 'retrieved'

    def __init__(self, *args, **kwargs) -> None:
        """Construct a CalcJob instance.

        Construct the instance only if it is a sub class of `CalcJob`, otherwise raise `InvalidOperation`.

        See documentation of :class:`aiida.engine.Process`.
        """
        if self.__class__ == CalcJob:
            raise exceptions.InvalidOperation('cannot construct or launch a base `CalcJob` class.')

        super().__init__(*args, **kwargs)

    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:  # type: ignore[override]
        """Define the process specification, including its inputs, outputs and known exit codes.

        Ports are added to the `metadata` input namespace (inherited from the base Process),
        and a `code` input Port, a `remote_folder` output Port and retrieved folder output Port
        are added.

        :param spec: the calculation job process spec to define.
        """
        super().define(spec)
        spec.inputs.validator = validate_calc_job  # type: ignore[assignment]  # takes only PortNamespace not Port
        spec.input(
            'code',
            valid_type=orm.AbstractCode,
            required=False,
            help='The `Code` to use for this job. This input is required, unless the `remote_folder` input is '
            'specified, which means an existing job is being imported and no code will actually be run.'
        )
        spec.input_namespace(
            'monitors',
            valid_type=orm.Dict,
            required=False,
            validator=validate_monitors,
            help='Add monitoring functions that can inspect output files while the job is running and decide to '
            'prematurely terminate the job.'
        )
        spec.input(
            'remote_folder',
            valid_type=orm.RemoteData,
            required=False,
            help='Remote directory containing the results of an already completed calculation job without AiiDA. The '
            'inputs should be passed to the `CalcJob` as normal but instead of launching the actual job, the '
            'engine will recreate the input files and then proceed straight to the retrieve step where the files '
            'of this `RemoteData` will be retrieved as if it had been actually launched through AiiDA. If a '
            'parser is defined in the inputs, the results are parsed and attached as output nodes as usual.'
        )
        spec.input(
            'metadata.dry_run',
            valid_type=bool,
            default=False,
            help='When set to `True` will prepare the calculation job for submission but not actually launch it.'
        )
        spec.input(
            'metadata.computer',
            valid_type=orm.Computer,
            required=False,
            help='When using a "local" code, set the computer on which the calculation should be run.'
        )
        spec.input_namespace(f'{spec.metadata_key}.{spec.options_key}', required=False)
        spec.input(
            'metadata.options.input_filename',
            valid_type=str,
            required=False,
            help='Filename to which the input for the code that is to be run is written.'
        )
        spec.input(
            'metadata.options.output_filename',
            valid_type=str,
            required=False,
            help='Filename to which the content of stdout of the code that is to be run is written.'
        )
        spec.input(
            'metadata.options.submit_script_filename',
            valid_type=str,
            default='_aiidasubmit.sh',
            help='Filename to which the job submission script is written.'
        )
        spec.input(
            'metadata.options.scheduler_stdout',
            valid_type=str,
            default='_scheduler-stdout.txt',
            help='Filename to which the content of stdout of the scheduler is written.'
        )
        spec.input(
            'metadata.options.scheduler_stderr',
            valid_type=str,
            default='_scheduler-stderr.txt',
            help='Filename to which the content of stderr of the scheduler is written.'
        )
        spec.input(
            'metadata.options.resources',
            valid_type=dict,
            required=True,
            help='Set the dictionary of resources to be used by the scheduler plugin, like the number of nodes, '
            'cpus etc. This dictionary is scheduler-plugin dependent. Look at the documentation of the '
            'scheduler for more details.'
        )
        spec.input(
            'metadata.options.max_wallclock_seconds',
            valid_type=int,
            required=False,
            help='Set the wallclock in seconds asked to the scheduler'
        )
        spec.input(
            'metadata.options.custom_scheduler_commands',
            valid_type=str,
            default='',
            help='Set a (possibly multiline) string with the commands that the user wants to manually set for the '
            'scheduler. The difference of this option with respect to the `prepend_text` is the position in '
            'the scheduler submission file where such text is inserted: with this option, the string is '
            'inserted before any non-scheduler command'
        )
        spec.input(
            'metadata.options.queue_name',
            valid_type=str,
            required=False,
            help='Set the name of the queue on the remote computer'
        )
        spec.input(
            'metadata.options.rerunnable',
            valid_type=bool,
            required=False,
            help='Determines if the calculation can be requeued / rerun.'
        )
        spec.input(
            'metadata.options.account',
            valid_type=str,
            required=False,
            help='Set the account to use in for the queue on the remote computer'
        )
        spec.input(
            'metadata.options.qos',
            valid_type=str,
            required=False,
            help='Set the quality of service to use in for the queue on the remote computer'
        )
        spec.input(
            'metadata.options.withmpi',
            valid_type=bool,
            default=False,
            help='Set the calculation to use mpi',
        )
        spec.input(
            'metadata.options.mpirun_extra_params',
            valid_type=(list, tuple),
            default=lambda: [],
            help='Set the extra params to pass to the mpirun (or equivalent) command after the one provided in '
            'computer.mpirun_command. Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x',
        )
        spec.input(
            'metadata.options.import_sys_environment',
            valid_type=bool,
            default=True,
            help='If set to true, the submission script will load the system environment variables',
        )
        spec.input(
            'metadata.options.environment_variables',
            valid_type=dict,
            default=lambda: {},
            help='Set a dictionary of custom environment variables for this calculation',
        )
        spec.input(
            'metadata.options.environment_variables_double_quotes',
            valid_type=bool,
            default=False,
            help='If set to True, use double quotes instead of single quotes to escape the environment variables '
            'specified in ``environment_variables``.',
        )
        spec.input(
            'metadata.options.priority',
            valid_type=str,
            required=False,
            help='Set the priority of the job to be queued'
        )
        spec.input(
            'metadata.options.max_memory_kb',
            valid_type=int,
            required=False,
            help='Set the maximum memory (in KiloBytes) to be asked to the scheduler'
        )
        spec.input(
            'metadata.options.prepend_text',
            valid_type=str,
            default='',
            help='Set the calculation-specific prepend text, which is going to be prepended in the scheduler-job '
            'script, just before the code execution',
        )
        spec.input(
            'metadata.options.append_text',
            valid_type=str,
            default='',
            help='Set the calculation-specific append text, which is going to be appended in the scheduler-job '
            'script, just after the code execution',
        )
        spec.input(
            'metadata.options.parser_name',
            valid_type=str,
            required=False,
            validator=validate_parser,
            help='Set a string for the output parser. Can be None if no output plugin is available or needed'
        )
        spec.input(
            'metadata.options.additional_retrieve_list',
            required=False,
            valid_type=(list, tuple),
            validator=validate_additional_retrieve_list,
            help='List of relative file paths that should be retrieved in addition to what the plugin specifies.'
        )
        spec.input_namespace(
            'metadata.options.stash',
            required=False,
            populate_defaults=False,
            validator=validate_stash_options,
            help='Optional directives to stash files after the calculation job has completed.'
        )
        spec.input(
            'metadata.options.stash.target_base',
            valid_type=str,
            required=False,
            help='The base location to where the files should be stashd. For example, for the `copy` stash mode, this '
            'should be an absolute filepath on the remote computer.'
        )
        spec.input(
            'metadata.options.stash.source_list',
            valid_type=(tuple, list),
            required=False,
            help='Sequence of relative filepaths representing files in the remote directory that should be stashed.'
        )
        spec.input(
            'metadata.options.stash.stash_mode',
            valid_type=str,
            required=False,
            help='Mode with which to perform the stashing, should be value of `aiida.common.datastructures.StashMode`.'
        )

        spec.output(
            'remote_folder',
            valid_type=orm.RemoteData,
            help='Input files necessary to run the process will be stored in this folder node.'
        )
        spec.output(
            'remote_stash',
            valid_type=orm.RemoteStashData,
            required=False,
            help='Contents of the `stash.source_list` option are stored in this remote folder after job completion.'
        )
        spec.output(
            cls.link_label_retrieved,
            valid_type=orm.FolderData,
            pass_to_parser=True,
            help='Files that are retrieved by the daemon will be stored in this node. By default the stdout and stderr '
            'of the scheduler will be added, but one can add more by specifying them in `CalcInfo.retrieve_list`.'
        )

        spec.exit_code(
            100,
            'ERROR_NO_RETRIEVED_FOLDER',
            invalidates_cache=True,
            message='The process did not have the required `retrieved` output.'
        )
        spec.exit_code(
            110, 'ERROR_SCHEDULER_OUT_OF_MEMORY', invalidates_cache=True, message='The job ran out of memory.'
        )
        spec.exit_code(
            120, 'ERROR_SCHEDULER_OUT_OF_WALLTIME', invalidates_cache=True, message='The job ran out of walltime.'
        )
        spec.exit_code(150, 'STOPPED_BY_MONITOR', invalidates_cache=True, message='{message}')

    @classproperty
    def spec_options(cls):  # pylint: disable=no-self-argument
        """Return the metadata options port namespace of the process specification of this process.

        :return: options dictionary
        :rtype: dict
        """
        return cls.spec_metadata['options']  # pylint: disable=unsubscriptable-object

    @classmethod
    def get_importer(cls, entry_point_name: str | None = None) -> CalcJobImporter:
        """Load the `CalcJobImporter` associated with this `CalcJob` if it exists.

        By default an importer with the same entry point as the ``CalcJob`` will be loaded, however, this can be
        overridden using the ``entry_point_name`` argument.

        :param entry_point_name: optional entry point name of a ``CalcJobImporter`` to override the default.
        :return: the loaded ``CalcJobImporter``.
        :raises: if no importer class could be loaded.
        """
        from aiida.plugins import CalcJobImporterFactory
        from aiida.plugins.entry_point import get_entry_point_from_class

        if entry_point_name is None:
            _, entry_point = get_entry_point_from_class(cls.__module__, cls.__name__)
            if entry_point is not None:
                entry_point_name = entry_point.name  # type: ignore

        assert entry_point_name is not None

        return CalcJobImporterFactory(entry_point_name)()

    @property
    def options(self) -> AttributeDict:
        """Return the options of the metadata that were specified when this process instance was launched.

        :return: options dictionary

        """
        try:
            return self.metadata.options
        except AttributeError:
            return AttributeDict()

    @classmethod
    def get_state_classes(cls) -> Dict[Hashable, Type[plumpy.process_states.State]]:
        """A mapping of the State constants to the corresponding state class.

        Overrides the waiting state with the Calcjob specific version.
        """
        # Overwrite the waiting state
        states_map = super().get_state_classes()
        states_map[ProcessState.WAITING] = Waiting
        return states_map

    @property
    def node(self) -> orm.CalcJobNode:
        return super().node  # type: ignore

    @override
    def on_terminated(self) -> None:
        """Cleanup the node by deleting the calulation job state.

        .. note:: This has to be done before calling the super because that will seal the node after we cannot change it
        """
        self.node.delete_state()
        super().on_terminated()

    @override
    def run(self) -> Union[plumpy.process_states.Stop, int, plumpy.process_states.Wait]:
        """Run the calculation job.

        This means invoking the `presubmit` and storing the temporary folder in the node's repository. Then we move the
        process in the `Wait` state, waiting for the `UPLOAD` transport task to be started.

        :returns: the `Stop` command if a dry run, int if the process has an exit status,
            `Wait` command if the calcjob is to be uploaded

        """
        if self.inputs.metadata.dry_run:  # type: ignore[union-attr]
            self._perform_dry_run()
            return plumpy.process_states.Stop(None, True)

        if 'remote_folder' in self.inputs:  # type: ignore[operator]
            exit_code = self._perform_import()
            return exit_code

        # The following conditional is required for the caching to properly work. Even if the source node has a process
        # state of `Finished` the cached process will still enter the running state. The process state will have then
        # been overridden by the engine to `Running` so we cannot check that, but if the `exit_status` is anything other
        # than `None`, it should mean this node was taken from the cache, so the process should not be rerun.
        if self.node.exit_status is not None:
            return self.node.exit_status

        # Launch the upload operation
        return plumpy.process_states.Wait(msg='Waiting to upload', data=UPLOAD_COMMAND)

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare the calculation for submission.

        Convert the input nodes into the corresponding input files in the format that the code will expect. In addition,
        define and return a `CalcInfo` instance, which is a simple data structure that contains  information for the
        engine, for example, on what files to copy to the remote machine, what files to retrieve once it has completed,
        specific scheduler settings and more.

        :param folder: a temporary folder on the local file system.
        :returns: the `CalcInfo` instance
        """
        raise NotImplementedError()

    def _setup_metadata(self, metadata: dict) -> None:
        """Store the metadata on the ProcessNode."""
        computer = metadata.pop('computer', None)
        if computer is not None:
            self.node.computer = computer

        options = metadata.pop('options', {})
        for option_name, option_value in options.items():
            self.node.set_option(option_name, option_value)

        super()._setup_metadata(metadata)

    def _setup_inputs(self) -> None:
        """Create the links between the input nodes and the ProcessNode that represents this process."""
        super()._setup_inputs()

        # If a computer has not yet been set, which should have been done in ``_setup_metadata`` if it was specified
        # in the ``metadata`` inputs, set the computer associated with the ``code`` input. Note that not all ``code``s
        # will have an associated computer, but in that case the ``computer`` property should return ``None`` and
        # nothing would change anyway.
        if not self.node.computer:
            self.node.computer = self.inputs.code.computer  # type: ignore[union-attr]

    def _perform_dry_run(self):
        """Perform a dry run.

        Instead of performing the normal sequence of steps, just the `presubmit` is called, which will call the method
        `prepare_for_submission` of the plugin to generate the input files based on the inputs. Then the upload action
        is called, but using a normal local transport that will copy the files to a local sandbox folder. The generated
        input script and the absolute path to the sandbox folder are stored in the `dry_run_info` attribute of the node
        of this process.
        """
        from aiida.common.folders import SubmitTestFolder
        from aiida.engine.daemon.execmanager import upload_calculation
        from aiida.transports.plugins.local import LocalTransport

        with LocalTransport() as transport:
            with SubmitTestFolder() as folder:
                calc_info = self.presubmit(folder)
                transport.chdir(folder.abspath)
                upload_calculation(self.node, transport, calc_info, folder, inputs=self.inputs, dry_run=True)
                self.node.dry_run_info = {  # type: ignore
                    'folder': folder.abspath,
                    'script_filename': self.node.get_option('submit_script_filename')
                }

    def _perform_import(self):
        """Perform the import of an already completed calculation.

        The inputs contained a `RemoteData` under the key `remote_folder` signalling that this is not supposed to be run
        as a normal calculation job, but rather the results are already computed outside of AiiDA and merely need to be
        imported.
        """
        from aiida.common.datastructures import CalcJobState
        from aiida.common.folders import SandboxFolder
        from aiida.engine.daemon.execmanager import retrieve_calculation
        from aiida.manage import get_config_option
        from aiida.transports.plugins.local import LocalTransport

        filepath_sandbox = get_config_option('storage.sandbox') or None

        with LocalTransport() as transport:
            with SandboxFolder(filepath_sandbox) as folder:
                with SandboxFolder(filepath_sandbox) as retrieved_temporary_folder:
                    self.presubmit(folder)
                    self.node.set_remote_workdir(
                        self.inputs.remote_folder.get_remote_path()  # type: ignore[union-attr]
                    )
                    retrieve_calculation(self.node, transport, retrieved_temporary_folder.abspath)
                    self.node.set_state(CalcJobState.PARSING)
                    self.node.base.attributes.set(orm.CalcJobNode.IMMIGRATED_KEY, True)
                    return self.parse(retrieved_temporary_folder.abspath)

    def parse(
        self, retrieved_temporary_folder: Optional[str] = None, existing_exit_code: ExitCode | None = None
    ) -> ExitCode:
        """Parse a retrieved job calculation.

        This is called once it's finished waiting for the calculation to be finished and the data has been retrieved.

        :param retrieved_temporary_folder: The path to the temporary folder

        """
        try:
            retrieved = self.node.outputs.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER  # pylint: disable=no-member

        # Call the scheduler output parser
        exit_code_scheduler = self.parse_scheduler_output(retrieved)

        if exit_code_scheduler is not None and exit_code_scheduler.status > 0:
            # If an exit code is returned by the scheduler output parser, we log it and set it on the node. This will
            # allow the actual `Parser` implementation, if defined in the inputs, to inspect it and decide to keep it,
            # or override it with a more specific exit code, if applicable.
            msg = f'scheduler parser returned exit code<{exit_code_scheduler.status}>: {exit_code_scheduler.message}'
            self.logger.warning(msg)
            self.node.set_exit_status(exit_code_scheduler.status)
            self.node.set_exit_message(exit_code_scheduler.message)

        # Call the retrieved output parser
        try:
            exit_code_retrieved = self.parse_retrieved_output(retrieved_temporary_folder)
        finally:
            if retrieved_temporary_folder is not None:
                shutil.rmtree(retrieved_temporary_folder, ignore_errors=True)

        if exit_code_retrieved is not None and exit_code_retrieved.status > 0:
            msg = f'output parser returned exit code<{exit_code_retrieved.status}>: {exit_code_retrieved.message}'
            self.logger.warning(msg)

        # The final exit code is that of the scheduler, unless the output parser returned one
        exit_code: Optional[ExitCode]
        if exit_code_retrieved is not None:
            exit_code = exit_code_retrieved
        else:
            exit_code = exit_code_scheduler

        # Finally link up the outputs and we're done
        for entry in self.node.base.links.get_outgoing():
            self.out(entry.link_label, entry.node)

        if existing_exit_code is not None:
            return existing_exit_code

        return exit_code or ExitCode(0)

    @staticmethod
    def terminate(exit_code: ExitCode) -> ExitCode:
        """Terminate the process immediately and return the given exit code.

        This method is called by :meth:`aiida.engine.processes.calcjobs.tasks.Waiting.execute` if a monitor triggered
        the job to be terminated and specified the parsing to be skipped. It will construct the running state and tell
        this method to be run, which returns the given exit code which will cause the process to be terminated.

        :param exit_code: The exit code to return.
        :returns: The provided exit code.
        """
        return exit_code

    def parse_scheduler_output(self, retrieved: orm.Node) -> Optional[ExitCode]:
        """Parse the output of the scheduler if that functionality has been implemented for the plugin."""
        computer = self.node.computer

        if computer is None:
            self.logger.info(
                'no computer is defined for this calculation job which suggest that it is an imported job and so '
                'scheduler output probably is not available or not in a format that can be reliably parsed, skipping..'
            )
            return None

        scheduler = computer.get_scheduler()
        filename_stderr = self.node.get_option('scheduler_stderr')
        filename_stdout = self.node.get_option('scheduler_stdout')

        detailed_job_info = self.node.get_detailed_job_info()

        if detailed_job_info is None:
            self.logger.info('could not parse scheduler output: the `detailed_job_info` attribute is missing')
        elif detailed_job_info.get('retval', 0) != 0:
            self.logger.info('could not parse scheduler output: return value of `detailed_job_info` is non-zero')
            detailed_job_info = None

        if filename_stderr is None:
            self.logger.warning('could not determine `stderr` filename because `scheduler_stderr` option was not set.')
        else:
            try:
                scheduler_stderr = retrieved.base.repository.get_object_content(filename_stderr)
            except FileNotFoundError:
                scheduler_stderr = None
                self.logger.warning(f'could not parse scheduler output: the `{filename_stderr}` file is missing')

        if filename_stdout is None:
            self.logger.warning('could not determine `stdout` filename because `scheduler_stdout` option was not set.')
        else:
            try:
                scheduler_stdout = retrieved.base.repository.get_object_content(filename_stdout)
            except FileNotFoundError:
                scheduler_stdout = None
                self.logger.warning(f'could not parse scheduler output: the `{filename_stdout}` file is missing')

        try:
            exit_code = scheduler.parse_output(detailed_job_info, scheduler_stdout, scheduler_stderr)
        except exceptions.FeatureNotAvailable:
            self.logger.info(f'`{scheduler.__class__.__name__}` does not implement scheduler output parsing')
            return None
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.error(f'the `parse_output` method of the scheduler excepted: {exception}')
            return None

        if exit_code is not None and not isinstance(exit_code, ExitCode):
            args = (scheduler.__class__.__name__, type(exit_code))
            raise ValueError('`{}.parse_output` returned neither an `ExitCode` nor None, but: {}'.format(*args))

        return exit_code

    def parse_retrieved_output(self, retrieved_temporary_folder: Optional[str] = None) -> Optional[ExitCode]:
        """Parse the retrieved data by calling the parser plugin if it was defined in the inputs."""
        parser_class = self.node.get_parser_class()

        if parser_class is None:
            return None

        parser = parser_class(self.node)
        parse_kwargs = parser.get_outputs_for_parsing()

        if retrieved_temporary_folder:
            parse_kwargs['retrieved_temporary_folder'] = retrieved_temporary_folder

        exit_code = parser.parse(**parse_kwargs)

        for link_label, node in parser.outputs.items():
            try:
                self.out(link_label, node)
            except ValueError as exception:
                self.logger.error(f'invalid value {node} specified with label {link_label}: {exception}')
                exit_code = self.exit_codes.ERROR_INVALID_OUTPUT  # pylint: disable=no-member
                break

        if exit_code is not None and not isinstance(exit_code, ExitCode):
            args = (parser_class.__name__, type(exit_code))
            raise ValueError('`{}.parse` returned neither an `ExitCode` nor None, but: {}'.format(*args))

        return exit_code

    def presubmit(self, folder: Folder) -> CalcInfo:
        """Prepares the calculation folder with all inputs, ready to be copied to the cluster.

        :param folder: a SandboxFolder that can be used to write calculation input files and the scheduling script.

        :return calcinfo: the CalcInfo object containing the information needed by the daemon to handle operations.

        """
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        from aiida.common.datastructures import CodeInfo, CodeRunMode
        from aiida.common.exceptions import InputValidationError, InvalidOperation, PluginInternalError, ValidationError
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.orm import AbstractCode, Computer, load_code
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        inputs = self.node.base.links.get_incoming(link_type=LinkType.INPUT_CALC)

        if not self.inputs.metadata.dry_run and not self.node.is_stored:  # type: ignore[union-attr]
            raise InvalidOperation('calculation node is not stored.')

        computer = self.node.computer
        assert computer is not None
        codes = [_ for _ in inputs.all_nodes() if isinstance(_, AbstractCode)]

        for code in codes:
            if not code.can_run_on_computer(computer):
                raise InputValidationError(
                    'The selected code {} for calculation {} cannot run on computer {}'.format(
                        code.pk, self.node.pk, computer.label
                    )
                )

            code.validate_working_directory(folder)

        calc_info = self.prepare_for_submission(folder)
        calc_info.uuid = str(self.node.uuid)

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        job_tmpl.submit_as_hold = False
        job_tmpl.rerunnable = self.options.get('rerunnable', False)
        job_tmpl.job_environment = {}
        # 'email', 'email_on_started', 'email_on_terminated',
        job_tmpl.job_name = f'aiida-{self.node.pk}'
        job_tmpl.sched_output_path = self.options.scheduler_stdout
        if computer is not None:
            job_tmpl.shebang = computer.get_shebang()
        if self.options.scheduler_stderr == self.options.scheduler_stdout:
            job_tmpl.sched_join_files = True
        else:
            job_tmpl.sched_error_path = self.options.scheduler_stderr
            job_tmpl.sched_join_files = False

        # Set retrieve path, add also scheduler STDOUT and STDERR
        retrieve_list = calc_info.retrieve_list or []
        if (job_tmpl.sched_output_path is not None and job_tmpl.sched_output_path not in retrieve_list):
            retrieve_list.append(job_tmpl.sched_output_path)
        if not job_tmpl.sched_join_files:
            if (job_tmpl.sched_error_path is not None and job_tmpl.sched_error_path not in retrieve_list):
                retrieve_list.append(job_tmpl.sched_error_path)
        retrieve_list.extend(self.node.get_option('additional_retrieve_list') or [])
        self.node.set_retrieve_list(retrieve_list)

        # Handle the retrieve_temporary_list
        retrieve_temporary_list = calc_info.retrieve_temporary_list or []
        self.node.set_retrieve_temporary_list(retrieve_temporary_list)

        # If the inputs contain a ``remote_folder`` input node, we are in an import scenario and can skip the rest
        if 'remote_folder' in inputs.all_link_labels():
            return calc_info

        # The remaining code is only necessary for actual runs, for example, creating the submission script
        scheduler = computer.get_scheduler()

        # the if is done so that if the method returns None, this is
        # not added. This has two advantages:
        # - it does not add too many \n\n if most of the prepend_text are empty
        # - most importantly, skips the cases in which one of the methods
        #   would return None, in which case the join method would raise
        #   an exception
        prepend_texts = [computer.get_prepend_text()] + \
            [code.prepend_text for code in codes] + \
            [calc_info.prepend_text, self.node.get_option('prepend_text')]
        job_tmpl.prepend_text = '\n\n'.join(prepend_text for prepend_text in prepend_texts if prepend_text)

        append_texts = [self.node.get_option('append_text'), calc_info.append_text] + \
            [code.append_text for code in codes] + \
            [computer.get_append_text()]
        job_tmpl.append_text = '\n\n'.join(append_text for append_text in append_texts if append_text)

        # Set resources, also with get_default_mpiprocs_per_machine
        resources = self.node.get_option('resources')
        scheduler.preprocess_resources(resources, computer.get_default_mpiprocs_per_machine())
        job_tmpl.job_resource = scheduler.create_job_resource(**resources)  # type: ignore

        subst_dict = {'tot_num_mpiprocs': job_tmpl.job_resource.get_tot_num_mpiprocs()}

        for key, value in job_tmpl.job_resource.items():
            subst_dict[key] = value
        mpi_args = [arg.format(**subst_dict) for arg in computer.get_mpirun_command()]
        extra_mpirun_params = self.node.get_option('mpirun_extra_params')  # same for all codes in the same calc

        # set the codes_info
        if not isinstance(calc_info.codes_info, (list, tuple)):
            raise PluginInternalError('codes_info passed to CalcInfo must be a list of CalcInfo objects')

        tmpl_codes_info = []
        for code_info in calc_info.codes_info:

            if not isinstance(code_info, CodeInfo):
                raise PluginInternalError('Invalid codes_info, must be a list of CodeInfo objects')

            if code_info.code_uuid is None:
                raise PluginInternalError('CalcInfo should have the information of the code to be launched')
            this_code = load_code(code_info.code_uuid)

            # To determine whether this code should be run with MPI enabled, we get the value that was set in the inputs
            # of the entire process, which can then be overwritten by the value from the `CodeInfo`. This allows plugins
            # to force certain codes to run without MPI, even if the user wants to run all codes with MPI whenever
            # possible. This use case is typically useful for `CalcJob`s that consist of multiple codes where one or
            # multiple codes always have to be executed without MPI.

            this_withmpi = self.node.get_option('withmpi')

            # Override the value of `withmpi` with that of the `CodeInfo` if and only if it is set
            if code_info.withmpi is not None:
                this_withmpi = code_info.withmpi

            if this_withmpi:
                prepend_cmdline_params = this_code.get_prepend_cmdline_params(mpi_args, extra_mpirun_params)
            else:
                prepend_cmdline_params = this_code.get_prepend_cmdline_params()

            cmdline_params = this_code.get_executable_cmdline_params(code_info.cmdline_params)

            tmpl_code_info = JobTemplateCodeInfo()
            tmpl_code_info.prepend_cmdline_params = prepend_cmdline_params
            tmpl_code_info.cmdline_params = cmdline_params
            tmpl_code_info.use_double_quotes = [computer.get_use_double_quotes(), this_code.use_double_quotes]
            tmpl_code_info.stdin_name = code_info.stdin_name
            tmpl_code_info.stdout_name = code_info.stdout_name
            tmpl_code_info.stderr_name = code_info.stderr_name
            tmpl_code_info.join_files = code_info.join_files

            tmpl_codes_info.append(tmpl_code_info)
        job_tmpl.codes_info = tmpl_codes_info

        # set the codes execution mode, default set to `SERIAL`
        codes_run_mode = CodeRunMode.SERIAL
        if calc_info.codes_run_mode:
            codes_run_mode = calc_info.codes_run_mode

        job_tmpl.codes_run_mode = codes_run_mode
        ########################################################################

        custom_sched_commands = self.node.get_option('custom_scheduler_commands')
        if custom_sched_commands:
            job_tmpl.custom_scheduler_commands = custom_sched_commands

        job_tmpl.import_sys_environment = self.node.get_option('import_sys_environment')

        job_tmpl.job_environment = self.node.get_option('environment_variables')
        job_tmpl.environment_variables_double_quotes = self.node.get_option('environment_variables_double_quotes')

        queue_name = self.node.get_option('queue_name')
        account = self.node.get_option('account')
        qos = self.node.get_option('qos')
        if queue_name is not None:
            job_tmpl.queue_name = queue_name
        if account is not None:
            job_tmpl.account = account
        if qos is not None:
            job_tmpl.qos = qos
        priority = self.node.get_option('priority')
        if priority is not None:
            job_tmpl.priority = priority

        job_tmpl.max_memory_kb = self.node.get_option('max_memory_kb') or computer.get_default_memory_per_machine()

        max_wallclock_seconds = self.node.get_option('max_wallclock_seconds')
        if max_wallclock_seconds is not None:
            job_tmpl.max_wallclock_seconds = max_wallclock_seconds

        submit_script_filename = self.node.get_option('submit_script_filename')
        script_content = scheduler.get_submit_script(job_tmpl)
        folder.create_file_from_filelike(io.StringIO(script_content), submit_script_filename, 'w', encoding='utf8')

        def encoder(obj):
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
            raise TypeError(f' {obj!r} is not JSON serializable')

        subfolder = folder.get_subfolder('.aiida', create=True)
        subfolder.create_file_from_filelike(
            io.StringIO(json.dumps(job_tmpl, default=encoder)), 'job_tmpl.json', 'w', encoding='utf8'
        )
        subfolder.create_file_from_filelike(io.StringIO(json.dumps(calc_info)), 'calcinfo.json', 'w', encoding='utf8')

        if calc_info.local_copy_list is None:
            calc_info.local_copy_list = []

        if calc_info.remote_copy_list is None:
            calc_info.remote_copy_list = []

        # Some validation
        this_pk = self.node.pk if self.node.pk is not None else '[UNSTORED]'
        local_copy_list = calc_info.local_copy_list
        try:
            validate_list_of_string_tuples(local_copy_list, tuple_length=3)
        except ValidationError as exception:
            raise PluginInternalError(
                f'[presubmission of calc {this_pk}] local_copy_list format problem: {exception}'
            ) from exception

        remote_copy_list = calc_info.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list, tuple_length=3)
        except ValidationError as exception:
            raise PluginInternalError(
                f'[presubmission of calc {this_pk}] remote_copy_list format problem: {exception}'
            ) from exception

        for (remote_computer_uuid, _, dest_rel_path) in remote_copy_list:
            try:
                Computer.collection.get(uuid=remote_computer_uuid)  # pylint: disable=unused-variable
            except exceptions.NotExistent as exception:
                raise PluginInternalError(
                    '[presubmission of calc {}] '
                    'The remote copy requires a computer with UUID={}'
                    'but no such computer was found in the '
                    'database'.format(this_pk, remote_computer_uuid)
                ) from exception
            if os.path.isabs(dest_rel_path):
                raise PluginInternalError(
                    '[presubmission of calc {}] '
                    'The destination path of the remote copy '
                    'is absolute! ({})'.format(this_pk, dest_rel_path)
                )

        return calc_info
