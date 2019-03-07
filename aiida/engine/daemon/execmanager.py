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
This file contains the main routines to submit, check and retrieve calculation
results. These are general and contain only the main logic; where appropriate,
the routines make reference to the suitable plugins for all
plugin-specific operations.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os

from six.moves import zip

from aiida.common import AIIDA_LOGGER, exceptions
from aiida.common.datastructures import CalcJobState
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.orm import FolderData
from aiida.orm.utils.log import get_dblogger_extra
from aiida.plugins import DataFactory
from aiida.schedulers.datastructures import JobState

REMOTE_WORK_DIRECTORY_LOST_FOUND = 'lost+found'

execlogger = AIIDA_LOGGER.getChild('execmanager')


def upload_calculation(node, transport, calc_info, script_filename):
    """Upload a `CalcJob` instance

    :param node: the `CalcJobNode`.
    :param transport: an already opened transport to use to submit the calculation.
    :param calc_info: the calculation info datastructure returned by `CalcJobNode.presubmit`
    :param script_filename: the job launch script returned by `CalcJobNode.presubmit`
    """
    from logging import LoggerAdapter
    from tempfile import NamedTemporaryFile
    from aiida.orm import load_node, Code, RemoteData

    computer = node.computer

    if not computer.is_enabled():
        return

    codes_info = calc_info.codes_info
    input_codes = [load_node(_.code_uuid, sub_classes=(Code,)) for _ in codes_info]

    logger_extra = get_dblogger_extra(node)
    transport.set_logger_extra(logger_extra)
    logger = LoggerAdapter(logger=execlogger, extra=logger_extra)

    if node.has_cached_links():
        raise ValueError("Cannot submit calculation {} because it has cached input links! If you just want to test the "
                         "submission, use the test_submit() method, otherwise store all links first".format(node.pk))

    folder = node._raw_input_folder

    # NOTE: some logic is partially replicated in the 'test_submit'
    # method of CalcJobNode. If major logic changes are done
    # here, make sure to update also the test_submit routine
    remote_user = transport.whoami()
    # TODO Doc: {username} field
    # TODO: if something is changed here, fix also 'verdi computer test'
    remote_working_directory = computer.get_workdir().format(username=remote_user)
    if not remote_working_directory.strip():
        raise exceptions.ConfigurationError(
            "[submission of calculation {}] No remote_working_directory configured for computer '{}'".format(
                node.pk, computer.name))

    # If it already exists, no exception is raised
    try:
        transport.chdir(remote_working_directory)
    except IOError:
        logger.debug(
            "[submission of calculation {}] Unable to chdir in {}, trying to create it".format(
                node.pk, remote_working_directory))
        try:
            transport.makedirs(remote_working_directory)
            transport.chdir(remote_working_directory)
        except EnvironmentError as exc:
            raise exceptions.ConfigurationError(
                "[submission of calculation {}] "
                "Unable to create the remote directory {} on "
                "computer '{}': {}".format(
                    node.pk, remote_working_directory, computer.name, exc))
    # Store remotely with sharding (here is where we choose
    # the folder structure of remote jobs; then I store this
    # in the calculation properties using _set_remote_dir
    # and I do not have to know the logic, but I just need to
    # read the absolute path from the calculation properties.
    transport.mkdir(calc_info.uuid[:2], ignore_existing=True)
    transport.chdir(calc_info.uuid[:2])
    transport.mkdir(calc_info.uuid[2:4], ignore_existing=True)
    transport.chdir(calc_info.uuid[2:4])

    try:
        # The final directory may already exist, most likely because this function was already executed once, but
        # failed and as a result was rescheduled by the eninge. In this case it would be fine to delete the folder
        # and create it from scratch, except that we cannot be sure that this the actual case. Therefore, to err on
        # the safe side, we move the folder to the lost+found directory before recreating the folder from scratch
        transport.mkdir(calc_info.uuid[4:])
    except OSError:
        # Move the existing directory to lost+found, log a warning and create a clean directory anyway
        path_existing = os.path.join(transport.getcwd(), calc_info.uuid[4:])
        path_lost_found = os.path.join(remote_working_directory, REMOTE_WORK_DIRECTORY_LOST_FOUND)
        path_target = os.path.join(path_lost_found, calc_info.uuid)
        logger.warning('tried to create path {} but it already exists, moving the entire folder to {}'.format(
            path_existing, path_target))

        # Make sure the lost+found directory exists, then copy the existing folder there and delete the original
        transport.mkdir(path_lost_found, ignore_existing=True)
        transport.copytree(path_existing, path_target)
        transport.rmtree(path_existing)

        # Now we can create a clean folder for this calculation
        transport.mkdir(calc_info.uuid[4:])
    finally:
        transport.chdir(calc_info.uuid[4:])

    # I store the workdir of the calculation for later file retrieval
    workdir = transport.getcwd()
    node.set_remote_workdir(workdir)

    # I first create the code files, so that the code can put
    # default files to be overwritten by the plugin itself.
    # Still, beware! The code file itself could be overwritten...
    # But I checked for this earlier.
    for code in input_codes:
        if code.is_local():
            # Note: this will possibly overwrite files
            for f in code.get_folder_list():
                transport.put(code.get_abs_path(f), f)
            transport.chmod(code.get_local_executable(), 0o755)  # rwxr-xr-x

    # copy all files, recursively with folders
    for f in folder.get_content_list():
        logger.debug("[submission of calculation {}] copying file/folder {}...".format(node.pk, f))
        transport.put(folder.get_abs_path(f), f)

    # local_copy_list is a list of tuples,
    # each with (uuid, dest_rel_path)
    # NOTE: validation of these lists are done inside calculation.presubmit()
    local_copy_list = calc_info.local_copy_list
    remote_copy_list = calc_info.remote_copy_list
    remote_symlink_list = calc_info.remote_symlink_list

    if local_copy_list is not None:
        for uuid, filename, target in local_copy_list:
            logger.debug("[submission of calculation {}] copying local file/folder to {}".format(node.pk, target))

            try:
                data_node = load_node(uuid=uuid)
            except exceptions.NotExistent:
                logger.warning('failed to load Node<{}> specified in the `local_copy_list`'.format(uuid))

            # Note, once #2579 is implemented, use the `node.open` method instead of the named temporary file in
            # combination with the new `Transport.put_object_from_filelike`
            with NamedTemporaryFile(mode='w+') as handle:
                handle.write(data_node.get_object_content(filename))
                handle.flush()
                transport.put(handle.name, target)

    if remote_copy_list is not None:
        for (remote_computer_uuid, remote_abs_path, dest_rel_path) in remote_copy_list:
            if remote_computer_uuid == computer.uuid:
                logger.debug("[submission of calculation {}] copying {} remotely, directly on the machine {}".format(
                    node.pk, dest_rel_path, computer.name))
                try:
                    transport.copy(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    logger.warning("[submission of calculation {}] Unable to copy remote resource from {} to {}! "
                                   "Stopping.".format(node.pk, remote_abs_path, dest_rel_path))
                    raise
            else:
                # TODO: implement copy between two different machines!
                raise NotImplementedError(
                    "[submission of calculation {}] Remote copy between two different machines is "
                    "not implemented yet".format(node.pk))

    if remote_symlink_list is not None:
        for (remote_computer_uuid, remote_abs_path,
             dest_rel_path) in remote_symlink_list:
            if remote_computer_uuid == computer.uuid:
                logger.debug("[submission of calculation {}] copying {} remotely, directly on the machine {}".format(
                    node.pk, dest_rel_path, computer.name))
                try:
                    transport.symlink(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    logger.warning("[submission of calculation {}] Unable to create remote symlink from {} to {}! "
                                   "Stopping.".format(node.pk, remote_abs_path, dest_rel_path))
                    raise
            else:
                raise IOError("It is not possible to create a symlink between two different machines for "
                              "calculation {}".format(node.pk))

    remotedata = RemoteData(computer=computer, remote_path=workdir)
    remotedata.add_incoming(node, link_type=LinkType.CREATE, link_label='remote_folder')
    remotedata.store()

    return calc_info, script_filename


def submit_calculation(calculation, transport, calc_info, script_filename):
    """
    Submit a calculation

    :param calculation: the instance of CalcJobNode to submit.
    :param transport: an already opened transport to use to submit the calculation.
    :param calc_info: the calculation info datastructure returned by `CalcJobNode._presubmit`
    :param script_filename: the job launch script returned by `CalcJobNode._presubmit`
    """
    scheduler = calculation.computer.get_scheduler()
    scheduler.set_transport(transport)

    workdir = calculation.get_remote_workdir()
    job_id = scheduler.submit_from_script(workdir, script_filename)
    calculation.set_job_id(job_id)


def retrieve_calculation(calculation, transport, retrieved_temporary_folder):
    """
    Retrieve all the files of a completed job calculation using the given transport.

    If the job defined anything in the `retrieve_temporary_list`, those entries will be stored in the
    `retrieved_temporary_folder`. The caller is responsible for creating and destroying this folder.

    :param calculation: the instance of CalcJobNode to update.
    :param transport: an already opened transport to use for the retrieval.
    :param retrieved_temporary_folder: the absolute path to a directory in which to store the files
        listed, if any, in the `retrieved_temporary_folder` of the jobs CalcInfo
    """
    logger_extra = get_dblogger_extra(calculation)

    execlogger.debug("Retrieving calc {}".format(calculation.pk), extra=logger_extra)
    workdir = calculation.get_remote_workdir()

    execlogger.debug(
        "[retrieval of calc {}] chdir {}".format(calculation.pk, workdir),
        extra=logger_extra)

    # Create the FolderData node to attach everything to
    retrieved_files = FolderData()
    retrieved_files.add_incoming(calculation, link_type=LinkType.CREATE, link_label=calculation.link_label_retrieved)

    with transport:
        transport.chdir(workdir)

        # First, retrieve the files of folderdata
        retrieve_list = calculation.get_retrieve_list()
        retrieve_temporary_list = calculation.get_retrieve_temporary_list()
        retrieve_singlefile_list = calculation.get_retrieve_singlefile_list()

        with SandboxFolder() as folder:
            retrieve_files_from_list(calculation, transport, folder.abspath, retrieve_list)
            # Here I retrieved everything; now I store them inside the calculation
            retrieved_files.put_object_from_tree(folder.abspath)

        # Second, retrieve the singlefiles
        with SandboxFolder() as folder:
            _retrieve_singlefiles(calculation, transport, folder, retrieve_singlefile_list, logger_extra)

        # Retrieve the temporary files in the retrieved_temporary_folder if any files were
        # specified in the 'retrieve_temporary_list' key
        if retrieve_temporary_list:
            retrieve_files_from_list(calculation, transport, retrieved_temporary_folder, retrieve_temporary_list)

            # Log the files that were retrieved in the temporary folder
            for filename in os.listdir(retrieved_temporary_folder):
                execlogger.debug("[retrieval of calc {}] Retrieved temporary file or folder '{}'".format(
                    calculation.pk, filename), extra=logger_extra)

        # Store everything
        execlogger.debug(
            "[retrieval of calc {}] "
            "Storing retrieved_files={}".format(calculation.pk, retrieved_files.pk),
            extra=logger_extra)
        retrieved_files.store()


def kill_calculation(calculation, transport):
    """
    Kill the calculation through the scheduler

    :param calculation: the instance of CalcJobNode to kill.
    :param transport: an already opened transport to use to address the scheduler
    """
    job_id = calculation.get_job_id()

    # Get the scheduler plugin class and initialize it with the correct transport
    scheduler = calculation.computer.get_scheduler()
    scheduler.set_transport(transport)

    # Call the proper kill method for the job ID of this calculation
    result = scheduler.kill(job_id)

    if result is not True:

        # Failed to kill because the job might have already been completed
        running_jobs = scheduler.get_jobs(jobs=[job_id], as_dict=True)
        job = running_jobs.get(job_id, None)

        # If the job is returned it is still running and the kill really failed, so we raise
        if job is not None and job.job_state != JobState.DONE:
            raise exceptions.RemoteOperationError('scheduler.kill({}) was unsuccessful'.format(job_id))
        else:
            execlogger.warning('scheduler.kill() failed but job<{%s}> no longer seems to be running regardless', job_id)

    return True


def parse_results(process, retrieved_temporary_folder=None):
    """
    Parse the results for a given CalcJobNode (job)

    :returns: integer exit code, where 0 indicates success and non-zero failure
    """
    from aiida.engine import ExitCode

    assert process.node.get_state() == CalcJobState.PARSING, \
        'job should be in the PARSING state when calling this function yet it is {}'.format(process.node.get_state())

    parser_class = process.node.get_parser_class()
    exit_code = ExitCode()
    logger_extra = get_dblogger_extra(process.node)

    if retrieved_temporary_folder:
        files = []
        for root, directories, filenames in os.walk(retrieved_temporary_folder):
            for directory in directories:
                files.append("- [D] {}".format(os.path.join(root, directory)))
            for filename in filenames:
                files.append("- [F] {}".format(os.path.join(root, filename)))

        execlogger.debug("[parsing of calc {}] "
                         "Content of the retrieved_temporary_folder: \n"
                         "{}".format(process.node.pk, "\n".join(files)), extra=logger_extra)
    else:
        execlogger.debug("[parsing of calc {}] "
                         "No retrieved_temporary_folder.".format(process.node.pk), extra=logger_extra)

    if parser_class is not None:

        parser = parser_class(process.node)
        parse_kwargs = parser.get_outputs_for_parsing()

        if retrieved_temporary_folder:
            parse_kwargs['retrieved_temporary_folder'] = retrieved_temporary_folder

        exit_code = parser.parse(**parse_kwargs)

        if exit_code is None:
            exit_code = ExitCode(0)

        if not isinstance(exit_code, ExitCode):
            raise ValueError('parse should return an `ExitCode` or None, and not {}'.format(type(exit_code)))

        if exit_code.status:
            parser.logger.error('parser returned exit code<{}>: {}'.format(exit_code.status, exit_code.message))

        for link_label, node in parser.outputs.items():
            node.add_incoming(process.node, link_type=LinkType.CREATE, link_label=link_label)
            node.store()

    return exit_code


def _retrieve_singlefiles(job, transport, folder, retrieve_file_list, logger_extra=None):
    singlefile_list = []
    for (linkname, subclassname, filename) in retrieve_file_list:
        execlogger.debug("[retrieval of calc {}] Trying "
                         "to retrieve remote singlefile '{}'".format(
            job.pk, filename), extra=logger_extra)
        localfilename = os.path.join(folder.abspath, os.path.split(filename)[1])
        transport.get(filename, localfilename, ignore_nonexisting=True)
        singlefile_list.append((linkname, subclassname, localfilename))

    # ignore files that have not been retrieved
    singlefile_list = [i for i in singlefile_list if os.path.exists(i[2])]

    # after retrieving from the cluster, I create the objects
    singlefiles = []
    for (linkname, subclassname, filename) in singlefile_list:
        SinglefileSubclass = DataFactory(subclassname)
        singlefile = SinglefileSubclass()
        singlefile.put_object_from_file(filename)
        singlefile.add_incoming(job, link_type=LinkType.CREATE, link_label=linkname)
        singlefiles.append(singlefile)

    for fil in singlefiles:
        execlogger.debug(
            "[retrieval of calc {}] "
            "Storing retrieved_singlefile={}".format(job.pk, fil.pk),
            extra=logger_extra)
        fil.store()


def retrieve_files_from_list(calculation, transport, folder, retrieve_list):
    """
    Retrieve all the files in the retrieve_list from the remote into the
    local folder instance through the transport. The entries in the retrieve_list
    can be of two types:

        * a string
        * a list

    If it is a string, it represents the remote absolute filepath of the file.
    If the item is a list, the elements will correspond to the following:

        * remotepath
        * localpath
        * depth

    If the remotepath contains file patterns with wildcards, the localpath will be
    treated as the work directory of the folder and the depth integer determines
    upto what level of the original remotepath nesting the files will be copied.

    :param transport: the Transport instance
    :param folder: an absolute path to a folder to copy files in
    :param retrieve_list: the list of files to retrieve
    """
    for item in retrieve_list:
        if isinstance(item, list):
            tmp_rname, tmp_lname, depth = item
            # if there are more than one file I do something differently
            if transport.has_magic(tmp_rname):
                remote_names = transport.glob(tmp_rname)
                local_names = []
                for rem in remote_names:
                    to_append = rem.split(os.path.sep)[-depth:] if depth > 0 else []
                    local_names.append(os.path.sep.join([tmp_lname] + to_append))
            else:
                remote_names = [tmp_rname]
                to_append = remote_names.split(os.path.sep)[-depth:] if depth > 0 else []
                local_names = [os.path.sep.join([tmp_lname] + to_append)]
            if depth > 1:  # create directories in the folder, if needed
                for this_local_file in local_names:
                    new_folder = os.path.join(
                        folder,
                        os.path.split(this_local_file)[0])
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)
        else:  # it is a string
            if transport.has_magic(item):
                remote_names = transport.glob(item)
                local_names = [os.path.split(rem)[1] for rem in remote_names]
            else:
                remote_names = [item]
                local_names = [os.path.split(item)[1]]

        for rem, loc in zip(remote_names, local_names):
            transport.logger.debug(
                "[retrieval of calc {}] Trying to retrieve remote item '{}'".format(calculation.pk, rem))
            transport.get(rem, os.path.join(folder, loc), ignore_nonexisting=True)
