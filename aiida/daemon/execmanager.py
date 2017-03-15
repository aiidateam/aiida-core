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
from aiida.common.datastructures import calc_states
from aiida.scheduler.datastructures import job_states
from aiida.common.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ModificationNotAllowed,
)
from aiida.common import aiidalogger
from aiida.common.links import LinkType
from aiida.orm import load_node



execlogger = aiidalogger.getChild('execmanager')


def update_running_calcs_status(authinfo):
    """
    Update the states of calculations in WITHSCHEDULER status belonging
    to user and machine as defined in the 'dbauthinfo' table.
    """
    from aiida.orm import JobCalculation, Computer
    from aiida.scheduler.datastructures import JobInfo
    from aiida.utils.logger import get_dblogger_extra
    from aiida.backends.utils import QueryFactory
    
    if not authinfo.enabled:
        return

    execlogger.debug("Updating running calc status for user {} "
                     "and machine {}".format(
        authinfo.aiidauser.email, authinfo.dbcomputer.name))

    qmanager = QueryFactory()()
    calcs_to_inquire = qmanager.query_jobcalculations_by_computer_user_state(
        state=calc_states.WITHSCHEDULER,
        computer=authinfo.dbcomputer,
        user=authinfo.aiidauser
    )

    #~ calcs_to_inquire = list(JobCalculation._get_all_with_state(
        #~ state=calc_states.WITHSCHEDULER,
        #~ computer=authinfo.dbcomputer,
        #~ user=authinfo.aiidauser)
    #~ )

    # NOTE: no further check is done that machine and
    # aiidauser are correct for each calc in calcs
    s = Computer(dbcomputer=authinfo.dbcomputer).get_scheduler()
    t = authinfo.get_transport()

    computed = []

    # I avoid to open an ssh connection if there are
    # no calcs with state WITHSCHEDULER
    if len(calcs_to_inquire):
        jobids_to_inquire = [str(c.get_job_id()) for c in calcs_to_inquire]

        # Open connection
        with t:
            s.set_transport(t)
            # TODO: Check if we are ok with filtering by job (to make this work,
            # I had to remove the check on the retval for getJobs,
            # because if the job has computed and is not in the output of
            # qstat, it gives a nonzero retval)

            # TODO: catch SchedulerError exception and do something
            # sensible (at least, skip this computer but continue with
            # following ones, and set a counter; set calculations to
            # UNKNOWN after a while?
            if s.get_feature('can_query_by_user'):
                found_jobs = s.getJobs(user="$USER", as_dict=True)
            else:
                found_jobs = s.getJobs(jobs=jobids_to_inquire, as_dict=True)

            # I update the status of jobs

            for c in calcs_to_inquire:
                try:
                    logger_extra = get_dblogger_extra(c)
                    t._set_logger_extra(logger_extra)

                    jobid = c.get_job_id()
                    if jobid is None:
                        execlogger.error("JobCalculation {} is WITHSCHEDULER "
                                         "but no job id was found!".format(
                            c.pk), extra=logger_extra)
                        continue

                    # I check if the calculation to be checked (c)
                    # is in the output of qstat
                    if jobid in found_jobs:
                        # jobinfo: the information returned by
                        # qstat for this job
                        jobinfo = found_jobs[jobid]
                        execlogger.debug("Inquirying calculation {} (jobid "
                                         "{}): it has job_state={}".format(
                            c.pk, jobid, jobinfo.job_state), extra=logger_extra)
                        # For the moment, FAILED is not defined
                        if jobinfo.job_state in [job_states.DONE]:  # , job_states.FAILED]:
                            computed.append(c)
                            try:
                                c._set_state(calc_states.COMPUTED)
                            except ModificationNotAllowed:
                                # Someone already set it, just skip
                                pass

                        ## Do not set the WITHSCHEDULER state multiple times,
                        ## this would raise a ModificationNotAllowed
                        # else:
                        # c._set_state(calc_states.WITHSCHEDULER)

                        c._set_scheduler_state(jobinfo.job_state)

                        c._set_last_jobinfo(jobinfo)
                    else:
                        execlogger.debug("Inquirying calculation {} (jobid "
                                         "{}): not found, assuming "
                                         "job_state={}".format(
                            c.pk, jobid, job_states.DONE), extra=logger_extra)

                        # calculation c is not found in the output of qstat
                        computed.append(c)
                        c._set_scheduler_state(job_states.DONE)
                except Exception as e:
                    # TODO: implement a counter, after N retrials
                    # set it to a status that
                    # requires the user intervention
                    execlogger.warning(
                        "There was an exception for "
                        "calculation {} ({}): {}".format(
                            c.pk, e.__class__.__name__, e.message
                        ), extra=logger_extra)
                    continue

            for c in computed:
                try:
                    logger_extra = get_dblogger_extra(c)
                    try:
                        detailed_jobinfo = s.get_detailed_jobinfo(
                            jobid=c.get_job_id())
                    except NotImplementedError:
                        detailed_jobinfo = (
                            u"AiiDA MESSAGE: This scheduler does not implement "
                            u"the routine get_detailed_jobinfo to retrieve "
                            u"the information on "
                            u"a job after it has finished.")
                    last_jobinfo = c._get_last_jobinfo()
                    if last_jobinfo is None:
                        last_jobinfo = JobInfo()
                        last_jobinfo.job_id = c.get_job_id()
                        last_jobinfo.job_state = job_states.DONE
                    last_jobinfo.detailedJobinfo = detailed_jobinfo
                    c._set_last_jobinfo(last_jobinfo)
                except Exception as e:
                    execlogger.warning("There was an exception while "
                                       "retrieving the detailed jobinfo "
                                       "for calculation {} ({}): {}".format(
                        c.pk, e.__class__.__name__, e.message),
                                       extra=logger_extra)
                    continue
                finally:
                    # Set the state to COMPUTED as the very last thing
                    # of this routine; no further change should be done after
                    # this, so that in general the retriever can just
                    # poll for this state, if we want to.
                    try:
                        c._set_state(calc_states.COMPUTED)
                    except ModificationNotAllowed:
                        # Someone already set it, just skip
                        pass

    return computed


def retrieve_jobs():
    from aiida.orm import JobCalculation, Computer
    from aiida.backends.utils import get_authinfo, QueryFactory

    qmanager = QueryFactory()()
    # I create a unique set of pairs (computer, aiidauser)
    computers_users_to_check = qmanager.query_jobcalculations_by_computer_user_state(
            state=calc_states.COMPUTED,
            only_computer_user_pairs=True,
            only_enabled=True
        )

    # I create a unique set of pairs (computer, aiidauser)
    #~ computers_users_to_check = list(
        #~ JobCalculation._get_all_with_state(
            #~ state=calc_states.COMPUTED,
            #~ only_computer_user_pairs=True,
            #~ only_enabled=True)
    #~ )

    for computer, aiidauser in computers_users_to_check:
        execlogger.debug("({},{}) pair to check".format(
            aiidauser.email, computer.name))
        try:
            authinfo = get_authinfo(computer.dbcomputer, aiidauser._dbuser)
            retrieve_computed_for_authinfo(authinfo)
        except Exception as e:
            msg = ("Error while retrieving calculation status for "
                   "aiidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                aiidauser.email,
                computer.name,
                e.__class__.__name__, e.message))
            execlogger.error(msg)
            # Continue with next computer
            continue


# in daemon
def update_jobs():
    """
    calls an update for each set of pairs (machine, aiidauser)
    """
    from aiida.orm import JobCalculation, Computer, User
    from aiida.backends.utils import get_authinfo, QueryFactory

    qmanager = QueryFactory()()
    # I create a unique set of pairs (computer, aiidauser)
    computers_users_to_check = qmanager.query_jobcalculations_by_computer_user_state(
            state=calc_states.WITHSCHEDULER,
            only_computer_user_pairs=True,
            only_enabled=True
        )

    for computer, aiidauser in computers_users_to_check:

        execlogger.debug("({},{}) pair to check".format(
            aiidauser.email, computer.name))

        try:
            authinfo = get_authinfo(computer.dbcomputer, aiidauser._dbuser)
            computed_calcs = update_running_calcs_status(authinfo)
        except Exception as e:
            msg = ("Error while updating calculation status "
                   "for aiidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                aiidauser.email,
                computer.name,
                e.__class__.__name__, e.message))
            execlogger.error(msg)
            # Continue with next computer
            continue


def submit_jobs():
    """
    Submit all jobs in the TOSUBMIT state.
    """
    from aiida.orm import JobCalculation, Computer, User
    from aiida.utils.logger import get_dblogger_extra
    from aiida.backends.utils import get_authinfo, QueryFactory


    qmanager = QueryFactory()()
    # I create a unique set of pairs (computer, aiidauser)
    computers_users_to_check = qmanager.query_jobcalculations_by_computer_user_state(
            state=calc_states.TOSUBMIT,
            only_computer_user_pairs=True,
            only_enabled=True
        )

    for computer, aiidauser in computers_users_to_check:

        execlogger.debug("({},{}) pair to submit".format(
            aiidauser.email, computer.name))

        try:
            try:
                authinfo = get_authinfo(computer.dbcomputer, aiidauser._dbuser)
            except AuthenticationError:
                # TODO!!
                # Put each calculation in the SUBMISSIONFAILED state because
                # I do not have AuthInfo to submit them
                calcs_to_inquire = qmanager.query_jobcalculations_by_computer_user_state(
                        state=calc_states.TOSUBMIT,
                        computer=computer, user=aiidauser
                    )
                #~ calcs_to_inquire = JobCalculation._get_all_with_state(
                    #~ state=calc_states.TOSUBMIT,
                    #~ computer=computer, user=aiidauser)
                for calc in calcs_to_inquire:
                    try:
                        calc._set_state(calc_states.SUBMISSIONFAILED)
                    except ModificationNotAllowed:
                        # Someone already set it, just skip
                        pass
                    logger_extra = get_dblogger_extra(calc)
                    execlogger.error("Submission of calc {} failed, "
                                     "computer pk= {} ({}) is not configured "
                                     "for aiidauser {}".format(
                        calc.pk, computer.pk, computer.get_name(),
                        aiidauser.email),
                                     extra=logger_extra)
                # Go to the next (dbcomputer,aiidauser) pair
                continue

            submitted_calcs = submit_jobs_with_authinfo(authinfo)
        except Exception as e:
            import traceback

            msg = ("Error while submitting jobs "
                   "for aiidauser={} on computer={}, "
                   "error type is {}, traceback: {}".format(
                aiidauser.email,
                computer.name,
                e.__class__.__name__, traceback.format_exc()))
            print msg
            execlogger.error(msg)
            # Continue with next computer
            continue


def submit_jobs_with_authinfo(authinfo):
    """
    Submit jobs in TOSUBMIT status belonging
    to user and machine as defined in the 'dbauthinfo' table.
    """
    from aiida.orm import JobCalculation
    from aiida.utils.logger import get_dblogger_extra

    from aiida.backends.utils import QueryFactory



    if not authinfo.enabled:
        return

    execlogger.debug("Submitting jobs for user {} "
                     "and machine {}".format(
        authinfo.aiidauser.email, authinfo.dbcomputer.name))

    qmanager = QueryFactory()()
    # I create a unique set of pairs (computer, aiidauser)
    calcs_to_inquire = qmanager.query_jobcalculations_by_computer_user_state(
            state=calc_states.TOSUBMIT,
        computer=authinfo.dbcomputer,
        user=authinfo.aiidauser)


    # I avoid to open an ssh connection if there are
    # no calcs with state WITHSCHEDULER
    if len(calcs_to_inquire):
        # Open connection
        try:
            # I do it here so that the transport is opened only once per computer
            with authinfo.get_transport() as t:
                for c in calcs_to_inquire:
                    logger_extra = get_dblogger_extra(c)
                    t._set_logger_extra(logger_extra)

                    try:
                        submit_calc(calc=c, authinfo=authinfo, transport=t)
                    except Exception as e:
                        # TODO: implement a counter, after N retrials
                        # set it to a status that
                        # requires the user intervention
                        execlogger.warning("There was an exception for "
                                           "calculation {} ({}): {}".format(
                            c.pk, e.__class__.__name__, e.message))
                        # I just proceed to the next calculation
                        continue
        # Catch exceptions also at this level (this happens only if there is
        # a problem opening the transport in the 'with t' statement,
        # because any other exception is caught and skipped above
        except Exception as e:
            import traceback
            from aiida.utils.logger import get_dblogger_extra

            for calc in calcs_to_inquire:
                logger_extra = get_dblogger_extra(calc)
                try:
                    calc._set_state(calc_states.SUBMISSIONFAILED)
                except ModificationNotAllowed:
                    # Someone already set it, just skip
                    pass

                execlogger.error("Submission of calc {} failed, check also the "
                                 "log file! Traceback: {}".format(calc.pk,
                                                                  traceback.format_exc()),
                                 extra=logger_extra)
            raise


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
    :param authinfo: the authinfo for this calculation.
    :param transport: if passed, must be an already opened transport. No checks
        are done on the consistency of the given transport with the transport
        of the computer defined in the authinfo.
    """
    from aiida.orm import Code, Computer
    from aiida.common.folders import SandboxFolder
    from aiida.common.exceptions import (
        InputValidationError)
    from aiida.orm.data.remote import RemoteData
    from aiida.utils.logger import get_dblogger_extra

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

        s = Computer(dbcomputer=authinfo.dbcomputer).get_scheduler()
        s.set_transport(t)

        computer = calc.get_computer()

        with SandboxFolder() as folder:
            calcinfo, script_filename = calc._presubmit(
                folder, use_unstored_links=False)

            codes_info = calcinfo.codes_info
            input_codes = [load_node(_.code_uuid, parent_class=Code)
                           for _ in codes_info ]

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
                    t.chmod(code.get_local_executable(), 0755)  # rwxr-xr-x

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

            remotedata = RemoteData(computer=computer,
                                    remote_path=workdir)
            remotedata.add_link_from(calc, label='remote_folder',
                                     link_type=LinkType.CREATE)
            remotedata.store()

            job_id = s.submit_from_script(t.getcwd(), script_filename)
            calc._set_job_id(job_id)
            # This should always be possible, because we should be
            # the only ones submitting this calculations,
            # so I do not check the ModificationNotAllowed
            calc._set_state(calc_states.WITHSCHEDULER)
            ## I do not set the state to queued; in this way, if the
            ## daemon is down, the user sees '(unknown)' as last state
            ## and understands that the daemon is not running.
            # if job_tmpl.submit_as_hold:
            #    calc._set_scheduler_state(job_states.QUEUED_HELD)
            #else:
            #    calc._set_scheduler_state(job_states.QUEUED)

            execlogger.debug("submitted calculation {} on {} with "
                             "jobid {}".format(calc.pk, computer.name, job_id),
                             extra=logger_extra)

    except Exception as e:
        import traceback

        try:
            calc._set_state(calc_states.SUBMISSIONFAILED)
        except ModificationNotAllowed:
            # Someone already set it, just skip
            pass

        execlogger.error("Submission of calc {} failed, check also the "
                         "log file! Traceback: {}".format(calc.pk,
                                                          traceback.format_exc()),
                         extra=logger_extra)
        raise
    finally:
        # close the transport, but only if it was opened within this function
        if must_open_t:
            t.close()


def retrieve_computed_for_authinfo(authinfo):
    from aiida.orm import JobCalculation
    from aiida.common.folders import SandboxFolder
    from aiida.orm.data.folder import FolderData
    from aiida.utils.logger import get_dblogger_extra
    from aiida.orm import DataFactory

    from aiida.backends.utils import QueryFactory

    import os

    if not authinfo.enabled:
        return

    qmanager = QueryFactory()()
    # I create a unique set of pairs (computer, aiidauser)
    calcs_to_retrieve = qmanager.query_jobcalculations_by_computer_user_state(
            state=calc_states.COMPUTED,
        computer=authinfo.dbcomputer,
        user=authinfo.aiidauser)


    retrieved = []

    # I avoid to open an ssh connection if there are no
    # calcs with state not COMPUTED
    if len(calcs_to_retrieve):

        # Open connection
        with authinfo.get_transport() as t:
            for calc in calcs_to_retrieve:
                logger_extra = get_dblogger_extra(calc)
                t._set_logger_extra(logger_extra)

                try:
                    calc._set_state(calc_states.RETRIEVING)
                except ModificationNotAllowed:
                    # Someone else has already started to retrieve it,
                    # just log and continue
                    execlogger.debug("Attempting to retrieve more than once "
                                     "calculation {}: skipping!".format(calc.pk),
                                     extra=logger_extra)
                    continue  # with the next calculation to retrieve
                try:
                    execlogger.debug("Retrieving calc {}".format(calc.pk),
                                     extra=logger_extra)
                    workdir = calc._get_remote_workdir()
                    retrieve_list = calc._get_retrieve_list()
                    retrieve_singlefile_list = calc._get_retrieve_singlefile_list()
                    execlogger.debug("[retrieval of calc {}] "
                                     "chdir {}".format(calc.pk, workdir),
                                     extra=logger_extra)
                    t.chdir(workdir)

                    retrieved_files = FolderData()
                    retrieved_files.add_link_from(
                        calc, label=calc._get_linkname_retrieved(),
                        link_type=LinkType.CREATE)

                    # First, retrieve the files of folderdata
                    with SandboxFolder() as folder:
                        for item in retrieve_list:
                            # I have two possibilities:
                            # * item is a string
                            # * or is a list
                            # then I have other two possibilities:
                            # * there are file patterns
                            # * or not
                            # First decide the name of the files
                            if isinstance(item, list):
                                tmp_rname, tmp_lname, depth = item
                                # if there are more than one file I do something differently
                                if t.has_magic(tmp_rname):
                                    remote_names = t.glob(tmp_rname)
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
                                            folder.abspath,
                                            os.path.split(this_local_file)[0])
                                        if not os.path.exists(new_folder):
                                            os.makedirs(new_folder)
                            else:  # it is a string
                                if t.has_magic(item):
                                    remote_names = t.glob(item)
                                    local_names = [os.path.split(rem)[1] for rem in remote_names]
                                else:
                                    remote_names = [item]
                                    local_names = [os.path.split(item)[1]]

                            for rem, loc in zip(remote_names, local_names):
                                execlogger.debug("[retrieval of calc {}] "
                                                 "Trying to retrieve remote item '{}'".format(
                                    calc.pk, rem),
                                                 extra=logger_extra)
                                t.get(rem,
                                      os.path.join(folder.abspath, loc),
                                      ignore_nonexisting=True)

                        # Here I retrieved everything;
                        # now I store them inside the calculation
                        retrieved_files.replace_with_folder(folder.abspath,
                                                            overwrite=True)

                    # Second, retrieve the singlefiles
                    with SandboxFolder() as folder:
                        singlefile_list = []
                        for (linkname, subclassname, filename) in retrieve_singlefile_list:
                            execlogger.debug("[retrieval of calc {}] Trying "
                                             "to retrieve remote singlefile '{}'".format(
                                calc.pk, filename),
                                             extra=logger_extra)
                            localfilename = os.path.join(
                                folder.abspath, os.path.split(filename)[1])
                            t.get(filename, localfilename,
                                  ignore_nonexisting=True)
                            singlefile_list.append((linkname, subclassname,
                                                    localfilename))

                        # ignore files that have not been retrieved
                        singlefile_list = [i for i in singlefile_list if
                                           os.path.exists(i[2])]

                        # after retrieving from the cluster, I create the objects
                        singlefiles = []
                        for (linkname, subclassname, filename) in singlefile_list:
                            SinglefileSubclass = DataFactory(subclassname)
                            singlefile = SinglefileSubclass()
                            singlefile.set_file(filename)
                            singlefile.add_link_from(calc, label=linkname,
                                                     link_type=LinkType.CREATE)
                            singlefiles.append(singlefile)

                    # Finally, store
                    execlogger.debug("[retrieval of calc {}] "
                                     "Storing retrieved_files={}".format(
                        calc.pk, retrieved_files.dbnode.pk),
                                     extra=logger_extra)
                    retrieved_files.store()
                    for fil in singlefiles:
                        execlogger.debug("[retrieval of calc {}] "
                                         "Storing retrieved_singlefile={}".format(
                            calc.pk, fil.dbnode.pk),
                                         extra=logger_extra)
                        fil.store()

                    # If I was the one retrieving, I should also be the only
                    # one parsing! I do not check
                    calc._set_state(calc_states.PARSING)

                    Parser = calc.get_parserclass()
                    # If no parser is set, the calculation is successful
                    successful = True
                    if Parser is not None:
                        # TODO: parse here
                        parser = Parser(calc)
                        successful, new_nodes_tuple = parser.parse_from_calc()

                        for label, n in new_nodes_tuple:
                            n.add_link_from(calc, label=label,
                                            link_type=LinkType.CREATE)
                            n.store()

                    if successful:
                        try:
                            calc._set_state(calc_states.FINISHED)
                        except ModificationNotAllowed:
                            # I should have been the only one to set it, but
                            # in order to avoid unuseful error messages, I
                            # just ignore
                            pass
                    else:
                        try:
                            calc._set_state(calc_states.FAILED)
                        except ModificationNotAllowed:
                            # I should have been the only one to set it, but
                            # in order to avoid unuseful error messages, I
                            # just ignore
                            pass
                        execlogger.error("[parsing of calc {}] "
                                         "The parser returned an error, but it should have "
                                         "created an output node with some partial results "
                                         "and warnings. Check there for more information on "
                                         "the problem".format(calc.pk), extra=logger_extra)
                    retrieved.append(calc)
                except Exception:
                    import traceback

                    tb = traceback.format_exc()
                    newextradict = logger_extra.copy()
                    newextradict['full_traceback'] = tb
                    if calc.get_state() == calc_states.PARSING:
                        execlogger.error("Error parsing calc {}. "
                                         "Traceback: {}".format(calc.pk, tb),
                                         extra=newextradict)
                        # TODO: add a 'comment' to the calculation
                        try:
                            calc._set_state(calc_states.PARSINGFAILED)
                        except ModificationNotAllowed:
                            pass
                    else:
                        execlogger.error("Error retrieving calc {}. "
                                         "Traceback: {}".format(calc.pk, tb),
                                         extra=newextradict)
                        try:
                            calc._set_state(calc_states.RETRIEVALFAILED)
                        except ModificationNotAllowed:
                            pass
                        raise

    return retrieved
