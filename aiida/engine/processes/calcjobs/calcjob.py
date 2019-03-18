# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of the CalcJob process."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import six

import plumpy

from aiida import orm
from aiida.common import exceptions
from aiida.common.lang import override
from aiida.common.links import LinkType

from ..process import Process, ProcessState
from ..process_spec import CalcJobProcessSpec
from .tasks import Waiting, UPLOAD_COMMAND

__all__ = ('CalcJob',)


class CalcJob(Process):
    """Implementation of the CalcJob process."""

    _node_class = orm.CalcJobNode
    _spec_class = CalcJobProcessSpec
    link_label_retrieved = 'retrieved'

    def __init__(self, *args, **kwargs):
        """Construct the instance only if it is a sub class of `CalcJob` otherwise raise `InvalidOperation`."""
        if self.__class__ == CalcJob:
            raise exceptions.InvalidOperation('cannot construct or launch a base `CalcJob` class.')

        super(CalcJob, self).__init__(*args, **kwargs)

    @classmethod
    def define(cls, spec):
        # yapf: disable
        super(CalcJob, cls).define(spec)
        spec.input('code', valid_type=orm.Code, help='The Code to use for this job.')
        spec.input('metadata.options.input_filename', valid_type=six.string_types, required=False,
            help='Filename to which the input for the code that is to be run will be written.')
        spec.input('metadata.options.output_filename', valid_type=six.string_types, required=False,
            help='Filename to which the content of stdout of the code that is to be run will be written.')
        spec.input('metadata.options.scheduler_stdout', valid_type=six.string_types, default='_scheduler-stdout.txt',
            help='Filename to which the content of stdout of the scheduler will be written.')
        spec.input('metadata.options.scheduler_stderr', valid_type=six.string_types, default='_scheduler-stderr.txt',
            help='Filename to which the content of stderr of the scheduler will be written.')
        spec.input('metadata.options.resources', valid_type=dict, required=True,
            help='Set the dictionary of resources to be used by the scheduler plugin, like the number of nodes, '
                 'cpus etc. This dictionary is scheduler-plugin dependent. Look at the documentation of the '
                 'scheduler for more details.')
        spec.input('metadata.options.max_wallclock_seconds', valid_type=int, required=False,
            help='Set the wallclock in seconds asked to the scheduler')
        spec.input('metadata.options.custom_scheduler_commands', valid_type=six.string_types, default='',
            help='Set a (possibly multiline) string with the commands that the user wants to manually set for the '
                 'scheduler. The difference of this option with respect to the `prepend_text` is the position in '
                 'the scheduler submission file where such text is inserted: with this option, the string is '
                 'inserted before any non-scheduler command')
        spec.input('metadata.options.queue_name', valid_type=six.string_types, required=False,
            help='Set the name of the queue on the remote computer')
        spec.input('metadata.options.account', valid_type=six.string_types, required=False,
            help='Set the account to use in for the queue on the remote computer')
        spec.input('metadata.options.qos', valid_type=six.string_types, required=False,
            help='Set the quality of service to use in for the queue on the remote computer')
        spec.input('metadata.options.computer', valid_type=orm.Computer, required=False,
            help='Set the computer to be used by the calculation')
        spec.input('metadata.options.withmpi', valid_type=bool, default=True,
            help='Set the calculation to use mpi',)
        spec.input('metadata.options.mpirun_extra_params', valid_type=(list, tuple), default=[],
            help='Set the extra params to pass to the mpirun (or equivalent) command after the one provided in '
                 'computer.mpirun_command. Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x',)
        spec.input('metadata.options.import_sys_environment', valid_type=bool, default=True,
            help='If set to true, the submission script will load the system environment variables',)
        spec.input('metadata.options.environment_variables', valid_type=dict, default={},
            help='Set a dictionary of custom environment variables for this calculation',)
        spec.input('metadata.options.priority', valid_type=six.string_types[0], required=False,
            help='Set the priority of the job to be queued')
        spec.input('metadata.options.max_memory_kb', valid_type=int, required=False,
            help='Set the maximum memory (in KiloBytes) to be asked to the scheduler')
        spec.input('metadata.options.prepend_text', valid_type=six.string_types[0], default='',
            help='Set the calculation-specific prepend text, which is going to be prepended in the scheduler-job '
                 'script, just before the code execution',)
        spec.input('metadata.options.append_text', valid_type=six.string_types[0], default='',
            help='Set the calculation-specific append text, which is going to be appended in the scheduler-job '
                 'script, just after the code execution',)
        spec.input('metadata.options.parser_name', valid_type=six.string_types[0], required=False,
            help='Set a string for the output parser. Can be None if no output plugin is available or needed')

        spec.output('remote_folder', valid_type=orm.RemoteData,
            help='Input files necessary to run the process will be stored in this folder node.')
        spec.output(cls.link_label_retrieved, valid_type=orm.FolderData, pass_to_parser=True,
            help='Files that are retrieved by the daemon will be stored in this node. By default the stdout and stderr '
                 'of the scheduler will be added, but one can add more by specifying them in `CalcInfo.retrieve_list`.')

        spec.exit_code(10, 'ERROR_PARSING_FAILED', message='the parsing of the job failed')
        spec.exit_code(20, 'ERROR_FAILED', message='the job failed for an unspecified reason')

    @classmethod
    def get_state_classes(cls):
        # Overwrite the waiting state
        states_map = super(CalcJob, cls).get_state_classes()
        states_map[ProcessState.WAITING] = Waiting
        return states_map

    @override
    def on_terminated(self):
        """Cleanup the node by deleting the calulation job state.

        .. note:: This has to be done before calling the super because that will seal the node after we cannot change it
        """
        self.node.delete_state()
        super(CalcJob, self).on_terminated()

    @override
    def run(self):
        """Run the calculation, we put it in the TOSUBMIT state and then wait for it to be completed."""
        from aiida.orm import Code, load_node
        from aiida.common.folders import SandboxFolder
        from aiida.common.exceptions import InputValidationError

        # The following conditional is required for the caching to properly work. Even if the source node has a process
        # state of `Finished` the cached process will still enter the running state. The process state will have then
        # been overridden by the engine to `Running` so we cannot check that, but if the `exit_status` is anything other
        # than `None`, it should mean this node was taken from the cache, so the process should not be rerun.
        if self.node.exit_status is not None:
            return self.node.exit_status

        with SandboxFolder() as folder:
            computer = self.node.computer
            if self.node.has_cached_links():
                raise exceptions.InvalidOperation('calculation node has unstored links in cache')
            calc_info, script_filename = self.presubmit(folder)
            input_codes = [load_node(_.code_uuid, sub_classes=(Code,)) for _ in calc_info.codes_info]

            for code in input_codes:
                if not code.can_run_on(computer):
                    raise InputValidationError(
                        'The selected code {} for calculation {} cannot run on computer {}'.format(
                            code.pk, self.node.pk, computer.name))

            # After this call, no modifications to the folder should be done
            self.node.put_object_from_tree(folder.abspath, force=True)

        # Launch the upload operation
        return plumpy.Wait(msg='Waiting to upload', data=(UPLOAD_COMMAND, calc_info, script_filename))

    def prepare_for_submission(self, folder):
        """Docs."""
        raise NotImplementedError

    def parse(self, retrieved_temporary_folder=None):
        """
        Parse a retrieved job calculation.

        This is called once it's finished waiting for the calculation to be finished and the data has been retrieved.
        """
        import shutil
        from aiida.engine.daemon import execmanager

        try:
            exit_code = execmanager.parse_results(self, retrieved_temporary_folder)
        finally:
            # Delete the temporary folder
            try:
                shutil.rmtree(retrieved_temporary_folder)
            except OSError as exception:
                if exception.errno != 2:
                    raise

        # Finally link up the outputs and we're done
        for entry in self.node.get_outgoing():
            self.out(entry.link_label, entry.node)

        return exit_code

    def presubmit(self, folder):
        """
        Prepares the calculation folder with all inputs, ready to be copied to the cluster.

        :param folder: a SandboxFolder, empty in input, that will be filled with
          calculation input files and the scheduling script.

        :return calcinfo: the CalcInfo object containing the information
            needed by the daemon to handle operations.
        """
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        import os

        from aiida.common.exceptions import PluginInternalError, ValidationError
        from aiida.common import json
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.common.datastructures import CodeInfo, CodeRunMode
        from aiida.orm import load_node, Code, Computer
        from aiida.plugins import DataFactory
        from aiida.schedulers.datastructures import JobTemplate

        computer = self.node.computer
        inputs = self.node.get_incoming(link_type=LinkType.INPUT_CALC)

        codes = [_ for _ in inputs.all_nodes() if isinstance(_, Code)]

        calcinfo = self.prepare_for_submission(folder)
        scheduler = computer.get_scheduler()

        for code in codes:
            if code.is_local():
                if code.get_local_executable() in folder.get_content_list():
                    raise PluginInternalError("The plugin created a file {} that is also "
                                              "the executable name!".format(code.get_local_executable()))

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        job_tmpl.shebang = computer.get_shebang()
        job_tmpl.submit_as_hold = False
        job_tmpl.rerunnable = False
        job_tmpl.job_environment = {}
        # 'email', 'email_on_started', 'email_on_terminated',
        job_tmpl.job_name = 'aiida-{}'.format(self.node.pk)
        job_tmpl.sched_output_path = self.options.scheduler_stdout
        if self.options.scheduler_stderr == self.options.scheduler_stdout:
            job_tmpl.sched_join_files = True
        else:
            job_tmpl.sched_error_path = self.options.scheduler_stderr
            job_tmpl.sched_join_files = False

        # Set retrieve path, add also scheduler STDOUT and STDERR
        retrieve_list = (calcinfo.retrieve_list if calcinfo.retrieve_list is not None else [])
        if (job_tmpl.sched_output_path is not None and job_tmpl.sched_output_path not in retrieve_list):
            retrieve_list.append(job_tmpl.sched_output_path)
        if not job_tmpl.sched_join_files:
            if (job_tmpl.sched_error_path is not None and job_tmpl.sched_error_path not in retrieve_list):
                retrieve_list.append(job_tmpl.sched_error_path)
        self.node.set_retrieve_list(retrieve_list)

        retrieve_singlefile_list = (calcinfo.retrieve_singlefile_list
                                    if calcinfo.retrieve_singlefile_list is not None else [])
        # a validation on the subclasses of retrieve_singlefile_list
        for _, subclassname, _ in retrieve_singlefile_list:
            file_sub_class = DataFactory(subclassname)
            if not issubclass(file_sub_class, orm.SinglefileData):
                raise PluginInternalError(
                    "[presubmission of calc {}] retrieve_singlefile_list subclass problem: {} is "
                    "not subclass of SinglefileData".format(self.node.pk, file_sub_class.__name__))
        self.node.set_retrieve_singlefile_list(retrieve_singlefile_list)

        # Handle the retrieve_temporary_list
        retrieve_temporary_list = (calcinfo.retrieve_temporary_list
                                   if calcinfo.retrieve_temporary_list is not None else [])
        self.node.set_retrieve_temporary_list(retrieve_temporary_list)

        # the if is done so that if the method returns None, this is
        # not added. This has two advantages:
        # - it does not add too many \n\n if most of the prepend_text are empty
        # - most importantly, skips the cases in which one of the methods
        #   would return None, in which case the join method would raise
        #   an exception
        prepend_texts = [computer.get_prepend_text()] + \
            [code.get_prepend_text() for code in codes] + \
            [calcinfo.prepend_text, self.node.get_option('prepend_text')]
        job_tmpl.prepend_text = '\n\n'.join(prepend_text for prepend_text in prepend_texts if prepend_text)

        append_texts = [self.node.get_option('append_text'), calcinfo.append_text] + \
            [code.get_append_text() for code in codes] + \
            [computer.get_append_text()]
        job_tmpl.append_text = '\n\n'.join(append_text for append_text in append_texts if append_text)

        # Set resources, also with get_default_mpiprocs_per_machine
        resources = self.node.get_option('resources')
        def_cpus_machine = computer.get_default_mpiprocs_per_machine()
        if def_cpus_machine is not None:
            resources['default_mpiprocs_per_machine'] = def_cpus_machine
        job_tmpl.job_resource = scheduler.create_job_resource(**resources)

        subst_dict = {'tot_num_mpiprocs': job_tmpl.job_resource.get_tot_num_mpiprocs()}

        for key, value in job_tmpl.job_resource.items():
            subst_dict[key] = value
        mpi_args = [arg.format(**subst_dict) for arg in computer.get_mpirun_command()]
        extra_mpirun_params = self.node.get_option('mpirun_extra_params')  # same for all codes in the same calc

        # set the codes_info
        if not isinstance(calcinfo.codes_info, (list, tuple)):
            raise PluginInternalError("codes_info passed to CalcInfo must be a list of CalcInfo objects")

        codes_info = []
        for code_info in calcinfo.codes_info:

            if not isinstance(code_info, CodeInfo):
                raise PluginInternalError("Invalid codes_info, must be a list of CodeInfo objects")

            if code_info.code_uuid is None:
                raise PluginInternalError("CalcInfo should have "
                                          "the information of the code "
                                          "to be launched")
            this_code = load_node(code_info.code_uuid, sub_classes=(Code,))

            this_withmpi = code_info.withmpi  # to decide better how to set the default
            if this_withmpi is None:
                if len(calcinfo.codes_info) > 1:
                    raise PluginInternalError("For more than one code, it is "
                                              "necessary to set withmpi in "
                                              "codes_info")
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
                job_tmpl.codes_run_mode = calcinfo.codes_run_mode
            except KeyError:
                raise PluginInternalError("Need to set the order of the code execution (parallel or serial?)")
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

        script_filename = '_aiidasubmit.sh'
        script_content = scheduler.get_submit_script(job_tmpl)
        folder.create_file_from_filelike(six.StringIO(script_content), script_filename, 'w', encoding='utf8')

        subfolder = folder.get_subfolder('.aiida', create=True)
        subfolder.create_file_from_filelike(six.StringIO(json.dumps(job_tmpl)), 'job_tmpl.json', 'w', encoding='utf8')
        subfolder.create_file_from_filelike(six.StringIO(json.dumps(calcinfo)), 'calcinfo.json', 'w', encoding='utf8')

        if calcinfo.local_copy_list is None:
            calcinfo.local_copy_list = []

        if calcinfo.remote_copy_list is None:
            calcinfo.remote_copy_list = []

        # Some validation
        this_pk = self.node.pk if self.node.pk is not None else "[UNSTORED]"
        local_copy_list = calcinfo.local_copy_list
        try:
            validate_list_of_string_tuples(local_copy_list, tuple_length=3)
        except ValidationError as exc:
            raise PluginInternalError("[presubmission of calc {}] "
                                      "local_copy_list format problem: {}".format(this_pk, exc))

        remote_copy_list = calcinfo.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list, tuple_length=3)
        except ValidationError as exc:
            raise PluginInternalError("[presubmission of calc {}] "
                                      "remote_copy_list format problem: {}".format(this_pk, exc))

        for (remote_computer_uuid, _, dest_rel_path) in remote_copy_list:
            try:
                Computer.objects.get(uuid=remote_computer_uuid)  # pylint: disable=unused-variable
            except exceptions.NotExistent:
                raise PluginInternalError("[presubmission of calc {}] "
                                          "The remote copy requires a computer with UUID={}"
                                          "but no such computer was found in the "
                                          "database".format(this_pk, remote_computer_uuid))
            if os.path.isabs(dest_rel_path):
                raise PluginInternalError("[presubmission of calc {}] "
                                          "The destination path of the remote copy "
                                          "is absolute! ({})".format(this_pk, dest_rel_path))

        return calcinfo, script_filename
