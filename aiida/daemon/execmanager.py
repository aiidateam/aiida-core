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
import os

from aiida.common import aiidalogger
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import ConfigurationError, ModificationNotAllowed
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.common.log import get_dblogger_extra
from aiida.orm import load_node, DataFactory
from aiida.orm.data.folder import FolderData
from aiida.scheduler.datastructures import JOB_STATES


execlogger = aiidalogger.getChild('execmanager')


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


def submit_calc(calc, authinfo, transport=None):
    """
    Submit a calculation

    :note: if no transport is passed, a new transport is opened and then
        closed within this function. If you want to use an already opened
        transport, pass it as further parameter. In this case, the transport
        has to be already open, and must coincide with the transport of the
        the computer defined by the authinfo.

    :param calc: the calculation to submit
        (an instance of the aiida.orm.JobCalculation class)
    :param authinfo: the AuthInfo object for this calculation.
    :param transport: if passed, must be an already opened transport. No checks
        are done on the consistency of the given transport with the transport
        of the computer defined in the AuthInfo.
    """
    from aiida.orm import Code, Computer
    from aiida.common.exceptions import InputValidationError
    from aiida.orm.data.remote import RemoteData

    if not authinfo.enabled:
        return

    logger_extra = get_dblogger_extra(calc)

    if transport is None:
        t = authinfo.get_transport()
        must_open_t = True
    else:
        t = transport
        must_open_t = False

    t._set_logger_extra(logger_extra)

    if calc._has_cached_links():
        raise ValueError("Cannot submit calculation {} because it has "
                         "cached input links! If you "
                         "just want to test the submission, use the "
                         "test_submit() method, otherwise store all links"
                         "first".format(calc.pk))

    # Double check, in the case the calculation was 'killed' (and therefore
    # put in the 'FAILED' state) in the meantime
    # Do it as near as possible to the state change below (it would be
    # even better to do it with some sort of transaction)
    if calc.get_state() != calc_states.TOSUBMIT:
        raise ValueError("Can only submit calculations with state=TOSUBMIT! "
                         "(state of calc {} is {} instead)".format(calc.pk,
                                                                   calc.get_state()))
    # I start to submit the calculation: I set the state
    try:
        calc._set_state(calc_states.SUBMITTING)
    except ModificationNotAllowed:
        raise ValueError("The calculation has already been submitted by "
                         "someone else!")

    try:
        if must_open_t:
            t.open()

        s = authinfo.computer.get_scheduler()
        s.set_transport(t)

        computer = calc.get_computer()

        with SandboxFolder() as folder:
            calcinfo, script_filename = calc._presubmit(
                folder, use_unstored_links=False)

            codes_info = calcinfo.codes_info
            input_codes = [load_node(_.code_uuid, sub_class=Code)
                           for _ in codes_info]

            for code in input_codes:
                if not code.can_run_on(computer):
                    raise InputValidationError(
                        "The selected code {} for calculation "
                        "{} cannot run on computer {}".
                            format(code.pk, calc.pk, computer.name))

            # After this call, no modifications to the folder should be done
            calc._store_raw_input_folder(folder.abspath)

            # NOTE: some logic is partially replicated in the 'test_submit'
            # method of JobCalculation. If major logic changes are done
            # here, make sure to update also the test_submit routine
            remote_user = t.whoami()
            # TODO Doc: {username} field
            # TODO: if something is changed here, fix also 'verdi computer test'
            remote_working_directory = authinfo.get_workdir().format(
                username=remote_user)
            if not remote_working_directory.strip():
                raise ConfigurationError(
                    "[submission of calc {}] "
                    "No remote_working_directory configured for computer "
                    "'{}'".format(calc.pk, computer.name))

            # If it already exists, no exception is raised
            try:
                t.chdir(remote_working_directory)
            except IOError:
                execlogger.debug(
                    "[submission of calc {}] "
                    "Unable to chdir in {}, trying to create it".
                        format(calc.pk, remote_working_directory),
                    extra=logger_extra)
                try:
                    t.makedirs(remote_working_directory)
                    t.chdir(remote_working_directory)
                except (IOError, OSError) as e:
                    raise ConfigurationError(
                        "[submission of calc {}] "
                        "Unable to create the remote directory {} on "
                        "computer '{}': {}".
                            format(calc.pk, remote_working_directory, computer.name,
                                   e.message))
            # Store remotely with sharding (here is where we choose
            # the folder structure of remote jobs; then I store this
            # in the calculation properties using _set_remote_dir
            # and I do not have to know the logic, but I just need to
            # read the absolute path from the calculation properties.
            t.mkdir(calcinfo.uuid[:2], ignore_existing=True)
            t.chdir(calcinfo.uuid[:2])
            t.mkdir(calcinfo.uuid[2:4], ignore_existing=True)
            t.chdir(calcinfo.uuid[2:4])
            t.mkdir(calcinfo.uuid[4:])
            t.chdir(calcinfo.uuid[4:])
            workdir = t.getcwd()
            # I store the workdir of the calculation for later file
            # retrieval
            calc._set_remote_workdir(workdir)

            # I first create the code files, so that the code can put
            # default files to be overwritten by the plugin itself.
            # Still, beware! The code file itself could be overwritten...
            # But I checked for this earlier.
            for code in input_codes:
                if code.is_local():
                    # Note: this will possibly overwrite files
                    for f in code.get_folder_list():
                        t.put(code.get_abs_path(f), f)
                    t.chmod(code.get_local_executable(), 0o755)  # rwxr-xr-x

            # copy all files, recursively with folders
            for f in folder.get_content_list():
                execlogger.debug("[submission of calc {}] "
                                 "copying file/folder {}...".format(calc.pk, f),
                                 extra=logger_extra)
                t.put(folder.get_abs_path(f), f)

            # local_copy_list is a list of tuples,
            # each with (src_abs_path, dest_rel_path)
            # NOTE: validation of these lists are done
            # inside calc._presubmit()
            local_copy_list = calcinfo.local_copy_list
            remote_copy_list = calcinfo.remote_copy_list
            remote_symlink_list = calcinfo.remote_symlink_list

            if local_copy_list is not None:
                for src_abs_path, dest_rel_path in local_copy_list:
                    execlogger.debug("[submission of calc {}] "
                                     "copying local file/folder to {}".format(
                        calc.pk, dest_rel_path),
                        extra=logger_extra)
                    t.put(src_abs_path, dest_rel_path)

            if remote_copy_list is not None:
                for (remote_computer_uuid, remote_abs_path,
                     dest_rel_path) in remote_copy_list:
                    if remote_computer_uuid == computer.uuid:
                        execlogger.debug("[submission of calc {}] "
                                         "copying {} remotely, directly on the machine "
                                         "{}".format(calc.pk, dest_rel_path, computer.name))
                        try:
                            t.copy(remote_abs_path, dest_rel_path)
                        except (IOError, OSError):
                            execlogger.warning("[submission of calc {}] "
                                               "Unable to copy remote resource from {} to {}! "
                                               "Stopping.".format(calc.pk,
                                                                  remote_abs_path, dest_rel_path),
                                               extra=logger_extra)
                            raise
                    else:
                        # TODO: implement copy between two different
                        # machines!
                        raise NotImplementedError(
                            "[presubmission of calc {}] "
                            "Remote copy between two different machines is "
                            "not implemented yet".format(calc.pk))

            if remote_symlink_list is not None:
                for (remote_computer_uuid, remote_abs_path,
                     dest_rel_path) in remote_symlink_list:
                    if remote_computer_uuid == computer.uuid:
                        execlogger.debug("[submission of calc {}] "
                                         "copying {} remotely, directly on the machine "
                                         "{}".format(calc.pk, dest_rel_path, computer.name))
                        try:
                            t.symlink(remote_abs_path, dest_rel_path)
                        except (IOError, OSError):
                            execlogger.warning("[submission of calc {}] "
                                               "Unable to create remote symlink from {} to {}! "
                                               "Stopping.".format(calc.pk,
                                                                  remote_abs_path, dest_rel_path),
                                               extra=logger_extra)
                            raise
                    else:
                        raise IOError("It is not possible to create a symlink "
                                      "between two different machines for "
                                      "calculation {}".format(calc.pk))

            remotedata = RemoteData(computer=computer, remote_path=workdir)
            remotedata.add_link_from(calc, label='remote_folder', link_type=LinkType.CREATE)
            remotedata.store()

            job_id = s.submit_from_script(t.getcwd(), script_filename)
            calc._set_job_id(job_id)
            # This should always be possible, because we should be
            # the only ones submitting this calculations,
            # so I do not check the ModificationNotAllowed
            calc._set_state(calc_states.WITHSCHEDULER)

            execlogger.debug("submitted calculation {} on {} with "
                             "jobid {}".format(calc.pk, computer.name, job_id),
                             extra=logger_extra)

    except Exception as e:
        import traceback

        execlogger.error('Submission of calc {} failed, check also the log file! Traceback: {}'.format(
            calc.pk, traceback.format_exc()), extra=logger_extra)

        try:
            calc._set_state(calc_states.SUBMISSIONFAILED)
        except ModificationNotAllowed:
            execlogger.debug('failed to set state of calculation<{}> to SUBMISSIONFAILED'.format(
                calc.pk, calc_states.SUBMISSIONFAILED), extra=logger_extra)
            pass

        raise

    finally:
        # close the transport, but only if it was opened within this function
        if must_open_t:
            t.close()


def retrieve_all(job, transport, retrieved_temporary_folder):
    """
    Retrieve all the files of a completed job calculation using the given transport. If the job defined
    anything in the `retrieve_temporary_list`, those entries will be stored in the `retrieved_temporary_folder`.
    The caller is responsible for creating and destroying this folder.

    :param job: the finished JobCalculation whose files to retrieve
    :param transport: the Transport instance to use for the file retrieval
    :param retrieved_temporary_folder: the absolute path to a directory in which to store the files
        listed, if any, in the `retrieved_temporary_folder` of the jobs CalcInfo
    """
    logger_extra = get_dblogger_extra(job)

    try:
        job._set_state(calc_states.RETRIEVING)
    except ModificationNotAllowed:
        # Someone else has already started to retrieve it,
        # just log and continue
        execlogger.debug(
            "Attempting to retrieve more than once "
            "calculation {}: skipping!".format(job.pk),
            extra=logger_extra
        )
        return

    execlogger.debug("Retrieving calc {}".format(job.pk), extra=logger_extra)
    workdir = job._get_remote_workdir()

    execlogger.debug(
        "[retrieval of calc {}] chdir {}".format(job.pk, workdir),
        extra=logger_extra)

    # Create the FolderData node to attach everything to
    retrieved_files = FolderData()
    retrieved_files.add_link_from(
        job, label=job._get_linkname_retrieved(),
        link_type=LinkType.CREATE)

    with transport:
        transport.chdir(workdir)

        # First, retrieve the files of folderdata
        retrieve_list = job._get_retrieve_list()
        retrieve_temporary_list = job._get_retrieve_temporary_list()
        retrieve_singlefile_list = job._get_retrieve_singlefile_list()

        with SandboxFolder() as folder:
            retrieve_files_from_list(job, transport, folder.abspath, retrieve_list)
            # Here I retrieved everything; now I store them inside the calculation
            retrieved_files.replace_with_folder(folder.abspath, overwrite=True)

        # Second, retrieve the singlefiles
        with SandboxFolder() as folder:
            _retrieve_singlefiles(job, transport, folder, retrieve_singlefile_list, logger_extra)

        # Retrieve the temporary files in the retrieved_temporary_folder if any files were
        # specified in the 'retrieve_temporary_list' key
        if retrieve_temporary_list:
            retrieve_files_from_list(job, transport, retrieved_temporary_folder, retrieve_temporary_list)

            # Log the files that were retrieved in the temporary folder
            for filename in os.listdir(retrieved_temporary_folder):
                execlogger.debug("[retrieval of calc {}] Retrieved temporary file or folder '{}'".format(
                job.pk, filename), extra=logger_extra)

        # Store everything
        execlogger.debug(
            "[retrieval of calc {}] "
            "Storing retrieved_files={}".format(job.pk, retrieved_files.dbnode.pk),
            extra=logger_extra)
        retrieved_files.store()


def parse_results(job, retrieved_temporary_folder=None):
    """
    Parse the results for a given JobCalculation (job)

    :returns: integer exit code, where 0 indicates success and non-zero failure
    """
    from aiida.orm.calculation.job import JobCalculationFinishStatus

    logger_extra = get_dblogger_extra(job)

    job._set_state(calc_states.PARSING)

    Parser = job.get_parserclass()
    exit_code = None

    if Parser is not None:

        parser = Parser(job)
        exit_code, new_nodes_tuple = parser.parse_from_calc(retrieved_temporary_folder)

        # Some implementations of parse_from_calc may still return a boolean for the exit_code
        # If we get True we convert to 0, for false we simply use the generic value that
        # maps to the calculation state FAILED
        if isinstance(exit_code, bool) and exit_code is True:
            exit_code = 0
        elif isinstance(exit_code, bool) and exit_code is False:
            exit_code = JobCalculationFinishStatus[calc_states.FAILED]

        for label, n in new_nodes_tuple:
            n.add_link_from(job, label=label, link_type=LinkType.CREATE)
            n.store()

    try:
        if exit_code == 0:
            job._set_state(calc_states.FINISHED)
        else:
            job._set_state(calc_states.FAILED)
    except ModificationNotAllowed:
        # I should have been the only one to set it, but
        # in order to avoid useless error messages, I just ignore
        pass

    if exit_code is not 0:
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
