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
from __future__ import absolute_import
import os

from six.moves import zip

from aiida.common import aiidalogger
from aiida.common import exceptions
from aiida.common.datastructures import calc_states
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.common.log import get_dblogger_extra
from aiida.orm import DataFactory
from aiida.orm.data.folder import FolderData
from aiida.scheduler.datastructures import JOB_STATES

REMOTE_WORK_DIRECTORY_LOST_FOUND = 'lost+found'

execlogger = aiidalogger.getChild('execmanager')


def upload_calculation(calculation, transport, calc_info, script_filename):
    """
    Upload a calculation

    :param calculation: the instance of JobCalculation to submit.
    :param transport: an already opened transport to use to submit the calculation.
    :param calc_info: the calculation info datastructure returned by `JobCalculation._presubmit`
    :param script_filename: the job launch script returned by `JobCalculation._presubmit`
    """
    from aiida.orm import load_node, Code
    from aiida.orm.data.remote import RemoteData

    computer = calculation.get_computer()

    if not computer.is_enabled():
        return

    codes_info = calc_info.codes_info
    input_codes = [load_node(_.code_uuid, sub_class=Code) for _ in codes_info]

    logger_extra = get_dblogger_extra(calculation)
    transport._set_logger_extra(logger_extra)

    if calculation._has_cached_links():
        raise ValueError("Cannot submit calculation {} because it has "
                         "cached input links! If you "
                         "just want to test the submission, use the "
                         "test_submit() method, otherwise store all links"
                         "first".format(calculation.pk))

    folder = calculation._raw_input_folder

    # NOTE: some logic is partially replicated in the 'test_submit'
    # method of JobCalculation. If major logic changes are done
    # here, make sure to update also the test_submit routine
    remote_user = transport.whoami()
    # TODO Doc: {username} field
    # TODO: if something is changed here, fix also 'verdi computer test'
    remote_working_directory = computer.get_workdir().format(
        username=remote_user)
    if not remote_working_directory.strip():
        raise exceptions.ConfigurationError(
            "[submission of calculation {}] "
            "No remote_working_directory configured for computer "
            "'{}'".format(calculation.pk, computer.name))

    # If it already exists, no exception is raised
    try:
        transport.chdir(remote_working_directory)
    except IOError:
        execlogger.debug(
            "[submission of calculation {}] Unable to chdir in {}, trying to create it".format(
                calculation.pk, remote_working_directory), extra=logger_extra)
        try:
            transport.makedirs(remote_working_directory)
            transport.chdir(remote_working_directory)
        except EnvironmentError as exc:
            raise exceptions.ConfigurationError(
                "[submission of calculation {}] "
                "Unable to create the remote directory {} on "
                "computer '{}': {}".format(
                    calculation.pk, remote_working_directory, computer.name, exc))
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
        execlogger.warning('tried to create path {} but it already exists, moving the entire folder to {}'.format(
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
    calculation._set_remote_workdir(workdir)

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
        execlogger.debug("[submission of calculation {}] "
                         "copying file/folder {}...".format(calculation.pk, f),
                         extra=logger_extra)
        transport.put(folder.get_abs_path(f), f)

    # local_copy_list is a list of tuples,
    # each with (src_abs_path, dest_rel_path)
    # NOTE: validation of these lists are done
    # inside calculation._presubmit()
    local_copy_list = calc_info.local_copy_list
    remote_copy_list = calc_info.remote_copy_list
    remote_symlink_list = calc_info.remote_symlink_list

    if local_copy_list is not None:
        for src_abs_path, dest_rel_path in local_copy_list:
            execlogger.debug("[submission of calculation {}] "
                             "copying local file/folder to {}".format(
                calculation.pk, dest_rel_path),
                extra=logger_extra)
            transport.put(src_abs_path, dest_rel_path)

    if remote_copy_list is not None:
        for (remote_computer_uuid, remote_abs_path,
             dest_rel_path) in remote_copy_list:
            if remote_computer_uuid == computer.uuid:
                execlogger.debug("[submission of calculation {}] "
                                 "copying {} remotely, directly on the machine "
                                 "{}".format(calculation.pk, dest_rel_path, computer.name))
                try:
                    transport.copy(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    execlogger.warning("[submission of calculation {}] "
                                       "Unable to copy remote resource from {} to {}! "
                                       "Stopping.".format(calculation.pk,
                                                          remote_abs_path, dest_rel_path),
                                       extra=logger_extra)
                    raise
            else:
                # TODO: implement copy between two different
                # machines!
                raise NotImplementedError(
                    "[presubmission of calculation {}] "
                    "Remote copy between two different machines is "
                    "not implemented yet".format(calculation.pk))

    if remote_symlink_list is not None:
        for (remote_computer_uuid, remote_abs_path,
             dest_rel_path) in remote_symlink_list:
            if remote_computer_uuid == computer.uuid:
                execlogger.debug("[submission of calculation {}] "
                                 "copying {} remotely, directly on the machine "
                                 "{}".format(calculation.pk, dest_rel_path, computer.name))
                try:
                    transport.symlink(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    execlogger.warning("[submission of calculation {}] "
                                       "Unable to create remote symlink from {} to {}! "
                                       "Stopping.".format(calculation.pk,
                                                          remote_abs_path, dest_rel_path),
                                       extra=logger_extra)
                    raise
            else:
                raise IOError("It is not possible to create a symlink "
                              "between two different machines for "
                              "calculation {}".format(calculation.pk))

    remotedata = RemoteData(computer=computer, remote_path=workdir)
    remotedata.add_link_from(calculation, label='remote_folder', link_type=LinkType.CREATE)
    remotedata.store()

    return calc_info, script_filename


def submit_calculation(calculation, transport, calc_info, script_filename):
    """
    Submit a calculation

    :param calculation: the instance of JobCalculation to submit.
    :param transport: an already opened transport to use to submit the calculation.
    :param calc_info: the calculation info datastructure returned by `JobCalculation._presubmit`
    :param script_filename: the job launch script returned by `JobCalculation._presubmit`
    """
    scheduler = calculation.get_computer().get_scheduler()
    scheduler.set_transport(transport)

    workdir = calculation._get_remote_workdir()
    job_id = scheduler.submit_from_script(workdir, script_filename)
    calculation._set_job_id(job_id)


def update_calculation(calculation, transport):
    """
    Update the scheduler state of a calculation

    :param calculation: the instance of JobCalculation to update.
    :param transport: an already opened transport to use to query the scheduler
    """
    scheduler = calculation.get_computer().get_scheduler()
    scheduler.set_transport(transport)

    job_id = calculation.get_job_id()

    kwargs = {'as_dict': True}

    if scheduler.get_feature('can_query_by_user'):
        kwargs['user'] = "$USER"
    else:
        # In general schedulers can either query by user or by jobs, but not both
        # (see also docs of the Scheduler class)
        kwargs['jobs'] = [job_id]

    found_jobs = scheduler.getJobs(**kwargs)
    job_info = found_jobs.get(job_id, None)

    if job_info is None:
        # If the job is computed or not found assume it's done
        job_done = True
        calculation._set_scheduler_state(JOB_STATES.DONE)
    else:
        job_done = job_info.job_state == JOB_STATES.DONE
        update_job_calc_from_job_info(calculation, job_info)

    if job_done:
        try:
            detailed_job_info = scheduler.get_detailed_jobinfo(job_id)
        except exceptions.FeatureNotAvailable:
            detailed_job_info = ('This scheduler does not implement get_detailed_jobinfo')

        update_job_calc_from_detailed_job_info(calculation, detailed_job_info)

    return job_done


def retrieve_calculation(calculation, transport, retrieved_temporary_folder):
    """
    Retrieve all the files of a completed job calculation using the given transport.

    If the job defined anything in the `retrieve_temporary_list`, those entries will be stored in the
    `retrieved_temporary_folder`. The caller is responsible for creating and destroying this folder.

    :param calculation: the instance of JobCalculation to update.
    :param transport: an already opened transport to use for the retrieval.
    :param retrieved_temporary_folder: the absolute path to a directory in which to store the files
        listed, if any, in the `retrieved_temporary_folder` of the jobs CalcInfo
    """
    logger_extra = get_dblogger_extra(calculation)

    execlogger.debug("Retrieving calc {}".format(calculation.pk), extra=logger_extra)
    workdir = calculation._get_remote_workdir()

    execlogger.debug(
        "[retrieval of calc {}] chdir {}".format(calculation.pk, workdir),
        extra=logger_extra)

    # Create the FolderData node to attach everything to
    retrieved_files = FolderData()
    retrieved_files.add_link_from(
        calculation, label=calculation._get_linkname_retrieved(),
        link_type=LinkType.CREATE)

    with transport:
        transport.chdir(workdir)

        # First, retrieve the files of folderdata
        retrieve_list = calculation._get_retrieve_list()
        retrieve_temporary_list = calculation._get_retrieve_temporary_list()
        retrieve_singlefile_list = calculation._get_retrieve_singlefile_list()

        with SandboxFolder() as folder:
            retrieve_files_from_list(calculation, transport, folder.abspath, retrieve_list)
            # Here I retrieved everything; now I store them inside the calculation
            retrieved_files.replace_with_folder(folder.abspath, overwrite=True)

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
            "Storing retrieved_files={}".format(calculation.pk, retrieved_files.dbnode.pk),
            extra=logger_extra)
        retrieved_files.store()


def kill_calculation(calculation, transport):
    """
    Kill the calculation through the scheduler

    :param calculation: the instance of JobCalculation to kill.
    :param transport: an already opened transport to use to address the scheduler
    """
    job_id = calculation.get_job_id()

    # Get the scheduler plugin class and initialize it with the correct transport
    scheduler = calculation.get_computer().get_scheduler()
    scheduler.set_transport(transport)

    # Call the proper kill method for the job ID of this calculation
    result = scheduler.kill(job_id)

    if result is not True:

        # Failed to kill because the job might have already been completed
        running_jobs = scheduler.getJobs(jobs=[job_id], as_dict=True)
        job = running_jobs.get(job_id, None)

        # If the job is returned it is still running and the kill really failed, so we raise
        if job is not None and job.job_state != JOB_STATES.DONE:
            raise exceptions.RemoteOperationError('scheduler.kill({}) was unsuccessful'.format(job_id))
        else:
            execlogger.warning('scheduler.kill() failed but job<{%s}> no longer seems to be running regardless', job_id)

    return True


def update_job_calc_from_job_info(calc, job_info):
    """
    Updates the job info for a JobCalculation using job information
    as obtained from the scheduler.

    :param calc: The job calculation
    :param job_info: the information returned by the scheduler for this job
    :return: True if the job state is DONE, False otherwise
    :rtype: bool
    """
    calc._set_scheduler_state(job_info.job_state)
    calc._set_last_jobinfo(job_info)

    return job_info.job_state in JOB_STATES.DONE


def update_job_calc_from_detailed_job_info(calc, detailed_job_info):
    """
    Updates the detailed job info for a JobCalculation as obtained from
    the scheduler

    :param calc: The job calculation
    :param detailed_job_info: the detailed information as returned by the
        scheduler for this job
    """
    from aiida.scheduler.datastructures import JobInfo

    last_jobinfo = calc._get_last_jobinfo()
    if last_jobinfo is None:
        last_jobinfo = JobInfo()
        last_jobinfo.job_id = calc.get_job_id()
        last_jobinfo.job_state = JOB_STATES.DONE

    last_jobinfo.detailedJobinfo = detailed_job_info
    calc._set_last_jobinfo(last_jobinfo)


def parse_results(job, retrieved_temporary_folder=None):
    """
    Parse the results for a given JobCalculation (job)

    :returns: integer exit code, where 0 indicates success and non-zero failure
    """
    from aiida.orm.calculation.job import JobCalculationExitStatus
    from aiida.work import ExitCode

    logger_extra = get_dblogger_extra(job)

    job._set_state(calc_states.PARSING)

    Parser = job.get_parserclass()
    exit_code = ExitCode()

    if retrieved_temporary_folder:
        files = []
        for root, directories, filenames in os.walk(retrieved_temporary_folder):
            for directory in directories:
                files.append("- [D] {}".format(os.path.join(root, directory)))
            for filename in filenames:
                files.append("- [F] {}".format(os.path.join(root, filename)))

        execlogger.debug("[parsing of calc {}] "
            "Content of the retrieved_temporary_folder: \n"
            "{}".format(job.pk, "\n".join(files)), extra=logger_extra)
    else:
        execlogger.debug("[parsing of calc {}] "
            "No retrieved_temporary_folder.".format(job.pk), extra=logger_extra)

    if Parser is not None:

        parser = Parser(job)
        exit_code, new_nodes_tuple = parser.parse_from_calc(retrieved_temporary_folder)

        # Some implementations of parse_from_calc may still return a plain boolean or integer for the exit_code.
        # In the case of a boolean: True should be mapped to the default ExitCode which corresponds to an exit
        # status of 0. False values are mapped to the value that is mapped onto the FAILED calculation state
        # throught the JobCalculationExitStatus. Plain integers are directly used to construct an ExitCode tuple
        if isinstance(exit_code, bool) and exit_code is True:
            exit_code = ExitCode(0)
        elif isinstance(exit_code, bool) and exit_code is False:
            exit_code = ExitCode(JobCalculationExitStatus[calc_states.FAILED].value)
        elif isinstance(exit_code, int):
            exit_code = ExitCode(exit_code)
        elif isinstance(exit_code, ExitCode):
            pass
        else:
            raise ValueError("parse_from_calc returned an 'exit_code' of invalid_type: {}. It should "
                "return a boolean, integer or ExitCode instance".format(type(exit_code)))

        for label, n in new_nodes_tuple:
            n.add_link_from(job, label=label, link_type=LinkType.CREATE)
            n.store()

    try:
        if exit_code.status == 0:
            job._set_state(calc_states.FINISHED)
        else:
            job._set_state(calc_states.FAILED)
    except exceptions.ModificationNotAllowed:
        # I should have been the only one to set it, but
        # in order to avoid useless error messages, I just ignore
        pass

    if exit_code.status is not 0:
        execlogger.error("[parsing of calc {}] "
                         "The parser returned an error, but it should have "
                         "created an output node with some partial results "
                         "and warnings. Check there for more information on "
                         "the problem".format(job.pk), extra=logger_extra)

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
        singlefile.set_file(filename)
        singlefile.add_link_from(job, label=linkname, link_type=LinkType.CREATE)
        singlefiles.append(singlefile)

    for fil in singlefiles:
        execlogger.debug(
            "[retrieval of calc {}] "
            "Storing retrieved_singlefile={}".format(job.pk, fil.dbnode.pk),
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
            transport.logger.debug("[retrieval of calc {}] Trying to retrieve remote item '{}'".format(calculation.pk, rem))
            transport.get(rem, os.path.join(folder, loc), ignore_nonexisting=True)
