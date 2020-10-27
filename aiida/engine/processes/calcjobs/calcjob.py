# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of the CalcJob process."""
import io

import plumpy

from aiida import orm
from aiida.common import exceptions, AttributeDict
from aiida.common.datastructures import CalcInfo
from aiida.common.folders import Folder
from aiida.common.lang import override, classproperty
from aiida.common.links import LinkType

from ..exit_code import ExitCode
from ..process import Process, ProcessState
from ..process_spec import CalcJobProcessSpec
from .tasks import Waiting, UPLOAD_COMMAND

__all__ = ('CalcJob',)


def validate_calc_job(inputs, ctx):  # pylint: disable=too-many-return-statements
    """Validate the entire set of inputs passed to the `CalcJob` constructor.

    Reasons that will cause this validation to raise an `InputValidationError`:

     * No `Computer` has been specified, neither directly in `metadata.computer` nor indirectly through the `Code` input
     * The specified computer is not stored
     * The `Computer` specified in `metadata.computer` is not the same as that of the specified `Code`

    :return: string with error message in case the inputs are invalid
    """
    try:
        ctx.get_port('code')
        ctx.get_port('metadata.computer')
    except ValueError:
        # If the namespace no longer contains the `code` or `metadata.computer` ports we skip validation
        return

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
        return

    # If the resources port exists but is not required, we don't need to validate it against the computer's scheduler
    if not resources_port.required:
        return

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


def validate_parser(parser_name, _):
    """Validate the parser.

    :return: string with error message in case the inputs are invalid
    """
    from aiida.plugins import ParserFactory

    if parser_name is not plumpy.UNSPECIFIED:
        try:
            ParserFactory(parser_name)
        except exceptions.EntryPointError as exception:
            return f'invalid parser specified: {exception}'


class CalcJob(Process):
    """Implementation of the CalcJob process."""

    _node_class = orm.CalcJobNode
    _spec_class = CalcJobProcessSpec
    link_label_retrieved = 'retrieved'

    def __init__(self, *args, **kwargs):
        """Construct a CalcJob instance.

        Construct the instance only if it is a sub class of `CalcJob`, otherwise raise `InvalidOperation`.

        See documentation of :class:`aiida.engine.Process`.
        """
        if self.__class__ == CalcJob:
            raise exceptions.InvalidOperation('cannot construct or launch a base `CalcJob` class.')

        super().__init__(*args, **kwargs)

    @classmethod
    def define(cls, spec: CalcJobProcessSpec):
        # yapf: disable
        """Define the process specification, including its inputs, outputs and known exit codes.

        :param spec: the calculation job process spec to define.
        """
        super().define(spec)
        spec.inputs.validator = validate_calc_job
        spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')
        spec.input('metadata.dry_run', valid_type=bool, default=False,
            help='When set to `True` will prepare the calculation job for submission but not actually launch it.')
        spec.input('metadata.computer', valid_type=orm.Computer, required=False,
            help='When using a "local" code, set the computer on which the calculation should be run.')
        spec.input_namespace(f'{spec.metadata_key}.{spec.options_key}', required=False)
        spec.input('metadata.options.input_filename', valid_type=str, required=False,
            help='Filename to which the input for the code that is to be run is written.')
        spec.input('metadata.options.output_filename', valid_type=str, required=False,
            help='Filename to which the content of stdout of the code that is to be run is written.')
        spec.input('metadata.options.submit_script_filename', valid_type=str, default='_aiidasubmit.sh',
            help='Filename to which the job submission script is written.')
        spec.input('metadata.options.scheduler_stdout', valid_type=str, default='_scheduler-stdout.txt',
            help='Filename to which the content of stdout of the scheduler is written.')
        spec.input('metadata.options.scheduler_stderr', valid_type=str, default='_scheduler-stderr.txt',
            help='Filename to which the content of stderr of the scheduler is written.')
        spec.input('metadata.options.resources', valid_type=dict, required=True,
            help='Set the dictionary of resources to be used by the scheduler plugin, like the number of nodes, '
                 'cpus etc. This dictionary is scheduler-plugin dependent. Look at the documentation of the '
                 'scheduler for more details.')
        spec.input('metadata.options.max_wallclock_seconds', valid_type=int, required=False,
            help='Set the wallclock in seconds asked to the scheduler')
        spec.input('metadata.options.custom_scheduler_commands', valid_type=str, default='',
            help='Set a (possibly multiline) string with the commands that the user wants to manually set for the '
                 'scheduler. The difference of this option with respect to the `prepend_text` is the position in '
                 'the scheduler submission file where such text is inserted: with this option, the string is '
                 'inserted before any non-scheduler command')
        spec.input('metadata.options.queue_name', valid_type=str, required=False,
            help='Set the name of the queue on the remote computer')
        spec.input('metadata.options.account', valid_type=str, required=False,
            help='Set the account to use in for the queue on the remote computer')
        spec.input('metadata.options.qos', valid_type=str, required=False,
            help='Set the quality of service to use in for the queue on the remote computer')
        spec.input('metadata.options.withmpi', valid_type=bool, default=False,
            help='Set the calculation to use mpi',)
        spec.input('metadata.options.mpirun_extra_params', valid_type=(list, tuple), default=lambda: [],
            help='Set the extra params to pass to the mpirun (or equivalent) command after the one provided in '
                 'computer.mpirun_command. Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x',)
        spec.input('metadata.options.import_sys_environment', valid_type=bool, default=True,
            help='If set to true, the submission script will load the system environment variables',)
        spec.input('metadata.options.environment_variables', valid_type=dict, default=lambda: {},
            help='Set a dictionary of custom environment variables for this calculation',)
        spec.input('metadata.options.priority', valid_type=str, required=False,
            help='Set the priority of the job to be queued')
        spec.input('metadata.options.max_memory_kb', valid_type=int, required=False,
            help='Set the maximum memory (in KiloBytes) to be asked to the scheduler')
        spec.input('metadata.options.prepend_text', valid_type=str, default='',
            help='Set the calculation-specific prepend text, which is going to be prepended in the scheduler-job '
                 'script, just before the code execution',)
        spec.input('metadata.options.append_text', valid_type=str, default='',
            help='Set the calculation-specific append text, which is going to be appended in the scheduler-job '
                 'script, just after the code execution',)
        spec.input('metadata.options.parser_name', valid_type=str, required=False, validator=validate_parser,
            help='Set a string for the output parser. Can be None if no output plugin is available or needed')

        spec.output('remote_folder', valid_type=orm.RemoteData,
            help='Input files necessary to run the process will be stored in this folder node.')
        spec.output(cls.link_label_retrieved, valid_type=orm.FolderData, pass_to_parser=True,
            help='Files that are retrieved by the daemon will be stored in this node. By default the stdout and stderr '
                 'of the scheduler will be added, but one can add more by specifying them in `CalcInfo.retrieve_list`.')

        # Errors caused or returned by the scheduler
        spec.exit_code(100, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The process did not have the required `retrieved` output.')
        spec.exit_code(110, 'ERROR_SCHEDULER_OUT_OF_MEMORY',
            message='The job ran out of memory.')
        spec.exit_code(120, 'ERROR_SCHEDULER_OUT_OF_WALLTIME',
            message='The job ran out of walltime.')

    @classproperty
    def spec_options(cls):  # pylint: disable=no-self-argument
        """Return the metadata options port namespace of the process specification of this process.

        :return: options dictionary
        :rtype: dict
        """
        return cls.spec_metadata['options']  # pylint: disable=unsubscriptable-object

    @property
    def options(self):
        """Return the options of the metadata that were specified when this process instance was launched.

        :return: options dictionary
        :rtype: dict
        """
        try:
            return self.metadata.options
        except AttributeError:
            return AttributeDict()

    @classmethod
    def get_state_classes(cls):
        # Overwrite the waiting state
        states_map = super().get_state_classes()
        states_map[ProcessState.WAITING] = Waiting
        return states_map

    @override
    def on_terminated(self):
        """Cleanup the node by deleting the calulation job state.

        .. note:: This has to be done before calling the super because that will seal the node after we cannot change it
        """
        self.node.delete_state()
        super().on_terminated()

    @override
    def run(self):
        """Run the calculation job.

        This means invoking the `presubmit` and storing the temporary folder in the node's repository. Then we move the
        process in the `Wait` state, waiting for the `UPLOAD` transport task to be started.
        """
        if self.inputs.metadata.dry_run:
            from aiida.common.folders import SubmitTestFolder
            from aiida.engine.daemon.execmanager import upload_calculation
            from aiida.transports.plugins.local import LocalTransport

            with LocalTransport() as transport:
                with SubmitTestFolder() as folder:
                    calc_info = self.presubmit(folder)
                    transport.chdir(folder.abspath)
                    upload_calculation(self.node, transport, calc_info, folder, inputs=self.inputs, dry_run=True)
                    self.node.dry_run_info = {
                        'folder': folder.abspath,
                        'script_filename': self.node.get_option('submit_script_filename')
                    }
            return plumpy.Stop(None, True)

        # The following conditional is required for the caching to properly work. Even if the source node has a process
        # state of `Finished` the cached process will still enter the running state. The process state will have then
        # been overridden by the engine to `Running` so we cannot check that, but if the `exit_status` is anything other
        # than `None`, it should mean this node was taken from the cache, so the process should not be rerun.
        if self.node.exit_status is not None:
            return self.node.exit_status

        # Launch the upload operation
        return plumpy.Wait(msg='Waiting to upload', data=UPLOAD_COMMAND)

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare the calculation for submission.

        Convert the input nodes into the corresponding input files in the format that the code will expect. In addition,
        define and return a `CalcInfo` instance, which is a simple data structure that contains  information for the
        engine, for example, on what files to copy to the remote machine, what files to retrieve once it has completed,
        specific scheduler settings and more.

        :param folder: a temporary folder on the local file system.
        :returns: the `CalcInfo` instance
        """
        raise NotImplementedError

    def parse(self, retrieved_temporary_folder=None):
        """Parse a retrieved job calculation.

        This is called once it's finished waiting for the calculation to be finished and the data has been retrieved.
        """
        import shutil

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
        if exit_code_retrieved is not None:
            exit_code = exit_code_retrieved
        else:
            exit_code = exit_code_scheduler

        # Finally link up the outputs and we're done
        for entry in self.node.get_outgoing():
            self.out(entry.link_label, entry.node)

        return exit_code or ExitCode(0)

    def parse_scheduler_output(self, retrieved):
        """Parse the output of the scheduler if that functionality has been implemented for the plugin."""
        scheduler = self.node.computer.get_scheduler()
        filename_stderr = self.node.get_option('scheduler_stderr')
        filename_stdout = self.node.get_option('scheduler_stdout')

        detailed_job_info = self.node.get_detailed_job_info()

        if detailed_job_info is None:
            self.logger.info('could not parse scheduler output: the `detailed_job_info` attribute is missing')
        elif detailed_job_info.get('retval', 0) != 0:
            self.logger.info('could not parse scheduler output: return value of `detailed_job_info` is non-zero')
            detailed_job_info = None

        try:
            scheduler_stderr = retrieved.get_object_content(filename_stderr)
        except FileNotFoundError:
            scheduler_stderr = None
            self.logger.warning(f'could not parse scheduler output: the `{filename_stderr}` file is missing')

        try:
            scheduler_stdout = retrieved.get_object_content(filename_stdout)
        except FileNotFoundError:
            scheduler_stdout = None
            self.logger.warning(f'could not parse scheduler output: the `{filename_stdout}` file is missing')

        # Only attempt to call the scheduler parser if all three resources of information are available
        if any(entry is None for entry in [detailed_job_info, scheduler_stderr, scheduler_stdout]):
            return

        try:
            exit_code = scheduler.parse_output(detailed_job_info, scheduler_stdout, scheduler_stderr)
        except exceptions.FeatureNotAvailable:
            self.logger.info(f'`{scheduler.__class__.__name__}` does not implement scheduler output parsing')
            return
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.error(f'the `parse_output` method of the scheduler excepted: {exception}')
            return

        if exit_code is not None and not isinstance(exit_code, ExitCode):
            args = (scheduler.__class__.__name__, type(exit_code))
            raise ValueError('`{}.parse_output` returned neither an `ExitCode` nor None, but: {}'.format(*args))

        return exit_code

    def parse_retrieved_output(self, retrieved_temporary_folder=None):
        """Parse the retrieved data by calling the parser plugin if it was defined in the inputs."""
        parser_class = self.node.get_parser_class()

        if parser_class is None:
            return

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

    def presubmit(self, folder):
        """Prepares the calculation folder with all inputs, ready to be copied to the cluster.

        :param folder: a SandboxFolder that can be used to write calculation input files and the scheduling script.
        :type folder: :class:`aiida.common.folders.Folder`

        :return calcinfo: the CalcInfo object containing the information needed by the daemon to handle operations.
        :rtype calcinfo: :class:`aiida.common.CalcInfo`
        """
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        import os

        from aiida.common.exceptions import PluginInternalError, ValidationError, InvalidOperation, InputValidationError
        from aiida.common import json
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.common.datastructures import CodeInfo, CodeRunMode
        from aiida.orm import load_node, Code, Computer
        from aiida.plugins import DataFactory
        from aiida.schedulers.datastructures import JobTemplate

        computer = self.node.computer
        inputs = self.node.get_incoming(link_type=LinkType.INPUT_CALC)

        if not self.inputs.metadata.dry_run and self.node.has_cached_links():
            raise InvalidOperation('calculation node has unstored links in cache')

        codes = [_ for _ in inputs.all_nodes() if isinstance(_, Code)]

        for code in codes:
            if not code.can_run_on(computer):
                raise InputValidationError('The selected code {} for calculation {} cannot run on computer {}'.format(
                    code.pk, self.node.pk, computer.label))

            if code.is_local() and code.get_local_executable() in folder.get_content_list():
                raise PluginInternalError('The plugin created a file {} that is also the executable name!'.format(
                    code.get_local_executable()))

        calc_info = self.prepare_for_submission(folder)
        calc_info.uuid = str(self.node.uuid)
        scheduler = computer.get_scheduler()

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        job_tmpl.shebang = computer.get_shebang()
        job_tmpl.submit_as_hold = False
        job_tmpl.rerunnable = False
        job_tmpl.job_environment = {}
        # 'email', 'email_on_started', 'email_on_terminated',
        job_tmpl.job_name = f'aiida-{self.node.pk}'
        job_tmpl.sched_output_path = self.options.scheduler_stdout
        if self.options.scheduler_stderr == self.options.scheduler_stdout:
            job_tmpl.sched_join_files = True
        else:
            job_tmpl.sched_error_path = self.options.scheduler_stderr
            job_tmpl.sched_join_files = False

        # Set retrieve path, add also scheduler STDOUT and STDERR
        retrieve_list = (calc_info.retrieve_list if calc_info.retrieve_list is not None else [])
        if (job_tmpl.sched_output_path is not None and job_tmpl.sched_output_path not in retrieve_list):
            retrieve_list.append(job_tmpl.sched_output_path)
        if not job_tmpl.sched_join_files:
            if (job_tmpl.sched_error_path is not None and job_tmpl.sched_error_path not in retrieve_list):
                retrieve_list.append(job_tmpl.sched_error_path)
        self.node.set_retrieve_list(retrieve_list)

        retrieve_singlefile_list = (calc_info.retrieve_singlefile_list
                                    if calc_info.retrieve_singlefile_list is not None else [])
        # a validation on the subclasses of retrieve_singlefile_list
        for _, subclassname, _ in retrieve_singlefile_list:
            file_sub_class = DataFactory(subclassname)
            if not issubclass(file_sub_class, orm.SinglefileData):
                raise PluginInternalError(
                    '[presubmission of calc {}] retrieve_singlefile_list subclass problem: {} is '
                    'not subclass of SinglefileData'.format(self.node.pk, file_sub_class.__name__))
        if retrieve_singlefile_list:
            self.node.set_retrieve_singlefile_list(retrieve_singlefile_list)

        # Handle the retrieve_temporary_list
        retrieve_temporary_list = (calc_info.retrieve_temporary_list
                                   if calc_info.retrieve_temporary_list is not None else [])
        self.node.set_retrieve_temporary_list(retrieve_temporary_list)

        # the if is done so that if the method returns None, this is
        # not added. This has two advantages:
        # - it does not add too many \n\n if most of the prepend_text are empty
        # - most importantly, skips the cases in which one of the methods
        #   would return None, in which case the join method would raise
        #   an exception
        prepend_texts = [computer.get_prepend_text()] + \
            [code.get_prepend_text() for code in codes] + \
            [calc_info.prepend_text, self.node.get_option('prepend_text')]
        job_tmpl.prepend_text = '\n\n'.join(prepend_text for prepend_text in prepend_texts if prepend_text)

        append_texts = [self.node.get_option('append_text'), calc_info.append_text] + \
            [code.get_append_text() for code in codes] + \
            [computer.get_append_text()]
        job_tmpl.append_text = '\n\n'.join(append_text for append_text in append_texts if append_text)

        # Set resources, also with get_default_mpiprocs_per_machine
        resources = self.node.get_option('resources')
        scheduler.preprocess_resources(resources, computer.get_default_mpiprocs_per_machine())
        job_tmpl.job_resource = scheduler.create_job_resource(**resources)

        subst_dict = {'tot_num_mpiprocs': job_tmpl.job_resource.get_tot_num_mpiprocs()}

        for key, value in job_tmpl.job_resource.items():
            subst_dict[key] = value
        mpi_args = [arg.format(**subst_dict) for arg in computer.get_mpirun_command()]
        extra_mpirun_params = self.node.get_option('mpirun_extra_params')  # same for all codes in the same calc

        # set the codes_info
        if not isinstance(calc_info.codes_info, (list, tuple)):
            raise PluginInternalError('codes_info passed to CalcInfo must be a list of CalcInfo objects')

        codes_info = []
        for code_info in calc_info.codes_info:

            if not isinstance(code_info, CodeInfo):
                raise PluginInternalError('Invalid codes_info, must be a list of CodeInfo objects')

            if code_info.code_uuid is None:
                raise PluginInternalError('CalcInfo should have '
                                          'the information of the code '
                                          'to be launched')
            this_code = load_node(code_info.code_uuid, sub_classes=(Code,))

            this_withmpi = code_info.withmpi  # to decide better how to set the default
            if this_withmpi is None:
                if len(calc_info.codes_info) > 1:
                    raise PluginInternalError('For more than one code, it is '
                                              'necessary to set withmpi in '
                                              'codes_info')
                else:
                    this_withmpi = self.node.get_option('withmpi')

            if this_withmpi:
                this_argv = (mpi_args + extra_mpirun_params + [this_code.get_execname()] +
                             (code_info.cmdline_params if code_info.cmdline_params is not None else []))
            else:
                this_argv = [this_code.get_execname()] + (code_info.cmdline_params
                                                          if code_info.cmdline_params is not None else [])

            # overwrite the old cmdline_params and add codename and mpirun stuff
            code_info.cmdline_params = this_argv

            codes_info.append(code_info)
        job_tmpl.codes_info = codes_info

        # set the codes execution mode

        if len(codes) > 1:
            try:
                job_tmpl.codes_run_mode = calc_info.codes_run_mode
            except KeyError:
                raise PluginInternalError('Need to set the order of the code execution (parallel or serial?)')
        else:
            job_tmpl.codes_run_mode = CodeRunMode.SERIAL
        ########################################################################

        custom_sched_commands = self.node.get_option('custom_scheduler_commands')
        if custom_sched_commands:
            job_tmpl.custom_scheduler_commands = custom_sched_commands

        job_tmpl.import_sys_environment = self.node.get_option('import_sys_environment')

        job_tmpl.job_environment = self.node.get_option('environment_variables')

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
        max_memory_kb = self.node.get_option('max_memory_kb')
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb
        max_wallclock_seconds = self.node.get_option('max_wallclock_seconds')
        if max_wallclock_seconds is not None:
            job_tmpl.max_wallclock_seconds = max_wallclock_seconds
        max_memory_kb = self.node.get_option('max_memory_kb')
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb

        submit_script_filename = self.node.get_option('submit_script_filename')
        script_content = scheduler.get_submit_script(job_tmpl)
        folder.create_file_from_filelike(io.StringIO(script_content), submit_script_filename, 'w', encoding='utf8')

        subfolder = folder.get_subfolder('.aiida', create=True)
        subfolder.create_file_from_filelike(io.StringIO(json.dumps(job_tmpl)), 'job_tmpl.json', 'w', encoding='utf8')
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
        except ValidationError as exc:
            raise PluginInternalError(f'[presubmission of calc {this_pk}] local_copy_list format problem: {exc}')

        remote_copy_list = calc_info.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list, tuple_length=3)
        except ValidationError as exc:
            raise PluginInternalError(f'[presubmission of calc {this_pk}] remote_copy_list format problem: {exc}')

        for (remote_computer_uuid, _, dest_rel_path) in remote_copy_list:
            try:
                Computer.objects.get(uuid=remote_computer_uuid)  # pylint: disable=unused-variable
            except exceptions.NotExistent:
                raise PluginInternalError('[presubmission of calc {}] '
                                          'The remote copy requires a computer with UUID={}'
                                          'but no such computer was found in the '
                                          'database'.format(this_pk, remote_computer_uuid))
            if os.path.isabs(dest_rel_path):
                raise PluginInternalError('[presubmission of calc {}] '
                                          'The destination path of the remote copy '
                                          'is absolute! ({})'.format(this_pk, dest_rel_path))

        return calc_info
