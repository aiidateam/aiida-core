"""
This file contains the main routines to submit, check and retrieve calculation
results. These are general and contain only the main logic; where appropriate, 
the routines make reference to the suitable plugins for all 
plugin-specific operations.
"""
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from aiida.common.datastructures import calc_states
from aiida.scheduler.datastructures import job_states
from aiida.common.exceptions import (
    AuthenticationError,
    ConfigurationError,
    PluginInternalError,
    )
from aiida.common import aiidalogger
    
execlogger = aiidalogger.getChild('execmanager')

def update_running_calcs_status(authinfo):
    """
    Update the states of calculations in WITHSCHEDULER status belonging 
    to user and machine as defined in the 'dbauthinfo' table.
    """
    from aiida.orm import Calculation, Computer
    from aiida.scheduler.datastructures import JobInfo

    execlogger.debug("Updating running calc status for user {} "
                     "and machine {}".format(
        authinfo.aiidauser.username, authinfo.dbcomputer.name))

    # This returns an iterator over aiida Calculation objects
    calcs_to_inquire = Calculation.get_all_with_state(
        state=calc_states.WITHSCHEDULER,
        computer=authinfo.dbcomputer,
        user=authinfo.aiidauser)
    
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
                found_jobs = s.getJobs(user="$USER", as_dict = True)
            else:
                found_jobs = s.getJobs(jobs=jobids_to_inquire, as_dict = True)
    
            # I update the status of jobs

            for c in calcs_to_inquire:
                try:
                    jobid = c.get_job_id()
                    if jobid is None:
                        execlogger.error("Calculation {} is WITHSCHEDULER "
                                         "but no job id was found!".format(
                            c.pk))
                        continue
                    
                    # I check if the calculation to be checked (c)
                    # is in the output of qstat
                    if jobid in found_jobs:
                        # jobinfo: the information returned by
                        # qstat for this job
                        jobinfo = found_jobs[jobid]
                        execlogger.debug("Inquirying calculation {} (jobid "
                                         "{}): it has job_state={}".format(
                            c.pk, jobid, jobinfo.job_state))
                        # For the moment, FAILED is not defined
                        if jobinfo.job_state in [job_states.DONE]: #, job_states.FAILED]:
                            computed.append(c)
                            c._set_state(calc_states.COMPUTED)
                        elif jobinfo.job_state == job_states.UNDETERMINED:
                            c._set_state(calc_states.UNDETERMINED)
                            execlogger.error("There is an undetermined calc "
                                             "with pk {}".format(
                                c.pk))
                        else:
                            c._set_state(calc_states.WITHSCHEDULER)
    
                        c._set_scheduler_state(jobinfo.job_state)
    
                        c._set_last_jobinfo(jobinfo)
                    else:
                        execlogger.debug("Inquirying calculation {} (jobid "
                                         "{}): not found, assuming "
                                         "job_state={}".format(
                            c.pk, jobid, job_states.DONE))

                        # calculation c is not found in the output of qstat
                        computed.append(c)
                        c._set_scheduler_state(job_states.DONE)
                except Exception as e:
                    # TODO: implement a counter, after N retrials
                    # set it to a status that
                    # requires the user intervention
                    execlogger.warning("There was an exception for "
                        "calculation {} ({}): {}".format(
                        c.pk, e.__class__.__name__, e.message))
                    continue
    
            for c in computed:
                try:
                    try:
                        detailed_jobinfo = s.get_detailed_jobinfo(
                            jobid=c.get_job_id())
                    except NotImplementedError:
                        detailed_jobinfo = (
                            u"AiiDA MESSAGE: This scheduler does not implement "
                            u"the routine get_detailed_jobinfo to retrieve "
                            u"the information on "
                            u"a job after it has finished.")
                    last_jobinfo = c.get_last_jobinfo()
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
                                       c.pk, e.__class__.__name__, e.message))
                    continue
                finally:
                    # Set the state to COMPUTED as the very last thing
                    # of this routine; no further change should be done after
                    # this, so that in general the retriever can just 
                    # poll for this state, if we want to.
                    c._set_state(calc_states.COMPUTED)

            
    return computed

def get_authinfo(computer, aiidauser):
    from aiida.djsite.db.models import DbComputer, DbAuthInfo
    try:
        authinfo = DbAuthInfo.objects.get(
                # converts from name, Computer or DbComputer instance to
                # a DbComputer instance
            dbcomputer=DbComputer.get_dbcomputer(computer),
            aiidauser=aiidauser)
    except ObjectDoesNotExist:
        raise AuthenticationError(
            "The aiida user {} is not configured to use computer {}".format(
                aiidauser.username, computer.name))
    except MultipleObjectsReturned:
        raise ConfigurationError(
            "The aiida user {} is not configured more than once to use "
            "computer {}! Only one configuration is allowed".format(
                aiidauser.username, computer.name))
    return authinfo

def daemon_main_loop():
    update_jobs()
    retrieve_jobs()

def retrieve_jobs():
    from aiida.orm import Calculation
    from django.contrib.auth.models import User
    from aiida.djsite.db.models import DbComputer
    
    # I create a unique set of pairs (computer, aiidauser)
    computers_users_to_check = set(
        Calculation.get_all_with_state(
            state=calc_states.COMPUTED,
            only_computer_user_pairs = True)
        )
    
    for dbcomputer_id, aiidauser_id in computers_users_to_check:
        dbcomputer = DbComputer.objects.get(id=dbcomputer_id)
        aiidauser = User.objects.get(id=aiidauser_id)

        execlogger.debug("({},{}) pair to check".format(
            aiidauser.username, dbcomputer.name))
        try:
            authinfo = get_authinfo(dbcomputer, aiidauser)
            retrieve_computed_for_authinfo(authinfo)
        except Exception as e:
            msg = ("Error while retrieving calculation status for "
                   "aiidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aiidauser.username,
                       dbcomputer.name,
                       e.__class__.__name__, e.message))
            execlogger.error(msg)
            raise

# in daemon
def update_jobs():
    """
    calls an update for each set of pairs (machine, aiidauser)
    """
    from aiida.orm import Calculation
    from django.contrib.auth.models import User
    from aiida.djsite.db.models import DbComputer

    # I create a unique set of pairs (computer, aiidauser)
    computers_users_to_check = set(
        Calculation.get_all_with_state(
            state=calc_states.WITHSCHEDULER,
            only_computer_user_pairs = True)
        )
    
    for dbcomputer_id, aiidauser_id in computers_users_to_check:
        dbcomputer = DbComputer.objects.get(id=dbcomputer_id)
        aiidauser = User.objects.get(id=aiidauser_id)

        execlogger.debug("({},{}) pair to check".format(
            aiidauser.username, dbcomputer.name))

        try:
            authinfo = get_authinfo(dbcomputer, aiidauser)
            computed_calcs = update_running_calcs_status(authinfo)
        except Exception as e:
            msg = ("Error while updating calculation status "
                   "for aiidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aiidauser.username,
                       dbcomputer.name,
                       e.__class__.__name__, e.message))
            execlogger.error(msg)
            raise

def submit_calc(calc):
    """
    Submit a calculation
    :param calc: the calculation to submit
        (an instance of the aiida.orm.Calculation class)
    """
    import StringIO
    import json
    import os
    
    from aiida.orm import Calculation, Code
    from aiida.common.folders import SandboxFolder
    from aiida.common.exceptions import (
        FeatureDisabled, InputValidationError, ValidationError)
    from aiida.scheduler.datastructures import JobTemplate
    from aiida.common.utils import validate_list_of_string_tuples
    from aiida.orm.data.remote import RemoteData
    
    if not isinstance(calc,Calculation):
        raise ValueError("calc must be a Calculation,"
                         "but node {} is not".format(calc.pk))
    
    if calc.get_state() != calc_states.NEW:
        raise ValueError("Can only submit calculations with state=NEW! "
                         "(state of calc {} is {} instead)".format(
                             calc.pk, calc.get_state()))

    computer = calc.computer
    if computer is None:
        raise ValueError("No computer specified for calculation {}".format(
            calc.pk))
    if not computer.is_enabled():
        raise FeatureDisabled("The computer '{}' associated to "
            "calculation {} is disabled: cannot submit".format(
            computer.name, calc.pk))
        

    # TODO: do some sort of blocking call,
    # to be sure that the submit function is not called
    # twice for the same calc?
    # I start to submit the calculation: I set the state
    calc._set_state(calc_states.SUBMITTING)
         
    try:
        authinfo = get_authinfo(calc.get_computer(), calc.get_user())
        s = calc.get_computer().get_scheduler()
        t = authinfo.get_transport()
    
        input_codes = calc.get_inputs(type=Code)
        if len(input_codes) != 1:
            raise InputValidationError("Calculation {} must have "
                "one and only one input code".format(calc.pk))
        code = input_codes[0]
    
        computer = calc.get_computer()

        if not code.can_run_on(computer):
            raise InputValidationError("The selected code {} for calculation "
                "{} cannot run on computer {}".format(
                code.pk, calc.pk, computer.name))
        
        with SandboxFolder() as folder:
            calcinfo = calc._prepare_for_submission(folder)
    
            if code.is_local():
                if code.get_local_executable() in folder.get_content_list():
                    raise PluginInternalError(
                          "The plugin created a file {} that is also "
                          "the executable name!".format(
                          code.get_local_executable()))

            # TODO: support -V option of schedulers!
            
            calc._set_retrieve_list(calcinfo.retrieve_list if
                                    calcinfo.retrieve_list is not None else [])
    
            # I create the job template to pass to the scheduler
            job_tmpl = JobTemplate()
            ## TODO: in the future, allow to customize the following variables
            job_tmpl.submit_as_hold = False
            job_tmpl.rerunnable = False
            job_tmpl.job_environment = {}
            #'email', 'email_on_started', 'email_on_terminated',
            job_tmpl.job_name = 'aiida-{}'.format(calc.pk) 
            job_tmpl.sched_output_path = '_scheduler-stdout.txt'
            job_tmpl.sched_error_path = '_scheduler-stderr.txt'
            job_tmpl.sched_join_files = False
            
            # TODO: add also code from the machine + u'\n\n'
            job_tmpl.prepend_text = (
                ((computer.get_prepend_text() + u"\n\n") if 
                    computer.get_prepend_text() else u"") + 
                ((code.get_prepend_text() + u"\n\n") if 
                    code.get_prepend_text() else u"") + 
                (calcinfo.prepend_text if 
                    calcinfo.prepend_text is not None else u""))
            
            job_tmpl.append_text = (
                (calcinfo.append_text if 
                    calcinfo.append_text is not None else u"") +
                ((code.get_append_text() + u"\n\n") if 
                    code.get_append_text() else u"") +
                ((computer.get_append_text() + u"\n\n") if 
                    computer.get_append_text() else u""))

            job_tmpl.job_resource = s.create_job_resource(
                 **calc.get_jobresource_params())

            subst_dict = {'tot_num_cpus': 
                          job_tmpl.job_resource.get_tot_num_cpus()}
            
            for k,v in job_tmpl.job_resource.iteritems():
                subst_dict[k] = v
            mpi_args = [arg.format(**subst_dict) for arg in
                        computer.get_mpirun_command()]
            if calc.get_withmpi():
                job_tmpl.argv = mpi_args + [code.get_execname()] + (
                    calcinfo.cmdline_params if 
                        calcinfo.cmdline_params is not None else [])
            else:
                job_tmpl.argv = [code.get_execname()] + (
                    calcinfo.cmdline_params if 
                        calcinfo.cmdline_params is not None else [])
    
            job_tmpl.stdin_name = calcinfo.stdin_name
            job_tmpl.stdout_name = calcinfo.stdout_name
            job_tmpl.stderr_name = calcinfo.stderr_name
            job_tmpl.join_files = calcinfo.join_files
            
            job_tmpl.import_sys_environment = calc.get_import_sys_environment()
            
            queue_name = calc.get_queue_name()
            if queue_name is not None:
                job_tmpl.queue_name = queue_name
            priority = calc.get_priority()
            if priority is not None:
                job_tmpl.priority = priority
            max_memory_kb = calc.get_max_memory_kb()
            if max_memory_kb is not None:
                job_tmpl.max_memory_kb = max_memory_kb
            max_wallclock_seconds = calc.get_max_wallclock_seconds()
            if max_wallclock_seconds is not None:
                job_tmpl.max_wallclock_seconds = max_wallclock_seconds
            max_memory_kb = calc.get_max_memory_kb()
            if max_memory_kb is not None:
                job_tmpl.max_memory_kb = max_memory_kb

            # TODO: give possibility to use a different name??
            script_filename = '_aiidasubmit.sh'
            script_content = s.get_submit_script(job_tmpl)
            folder.create_file_from_filelike(
                 StringIO.StringIO(script_content),script_filename)
    
            subfolder = folder.get_subfolder('.aiida',create=True)
            subfolder.create_file_from_filelike(
                StringIO.StringIO(json.dumps(job_tmpl)),'job_tmpl.json')
            subfolder.create_file_from_filelike(
                StringIO.StringIO(json.dumps(calcinfo)),'calcinfo.json')

            # After this call, no modifications to the folder should be done
            calc._store_raw_input_folder(folder.abspath)

            with t:
                s.set_transport(t)
                remote_user = t.whoami()
                computer = calc.get_computer()
                # TODO Doc: {username} field
                remote_working_directory = computer.get_workdir().format(
                    username=remote_user)
                if not remote_working_directory.strip():
                    raise ConfigurationError("[submission of calc {}] "
                        "No remote_working_directory configured for computer "
                        "'{}'".format(calc.pk, computer.name))

                # If it already exists, no exception is raised
                try:
                    t.chdir(remote_working_directory)
                except IOError:
                    execlogger.debug("[submission of calc {}] "
                        "Unable to chdir in {}, trying to create it".format(
                        calc.pk, remote_working_directory))
                    try:
                        t.makedirs(remote_working_directory)
                        t.chdir(remote_working_directory)
                    except (IOError, OSError) as e:
                        raise ConfigurationError("[submission of calc {}] "
                            "Unable to create the remote directory {} on "
                            "computer '{}': {}".format(calc.pk,
                                remote_working_directory, computer.name, 
                                e.message))
                # Store remotely with sharding (here is where we choose
                # the folder structure of remote jobs; then I store this
                # in the calculation properties using _set_remote_dir
                # and I do not have to know the logic, but I just need to
                # read the absolute path from the calculation properties.
                t.mkdir(calcinfo.uuid[:2],ignore_existing=True)
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
                if code.is_local():
                    # Note: this will possibly overwrite files
                    for f in code.get_path_list():
                        t.put(code.get_abs_path(f), f)
                    t.chmod(code.get_local_executable(), 0755) # rwxr-xr-x

                # copy all files, recursively with folders
                for f in folder.get_content_list():
                    execlogger.debug("[submission of calc {}] "
                        "copying file/folder {}...".format(calc.pk,f))
                    t.put(folder.get_abs_path(f), f)

                # local_copy_list is a list of tuples,
                # each with (src_abs_path, dest_rel_path)
                local_copy_list = calcinfo.local_copy_list
                if local_copy_list is None:
                    local_copy_list = []
                try:
                    validate_list_of_string_tuples(local_copy_list,
                                                   tuple_length = 2)
                except ValidationError as e:
                    raise PluginInternalError("[submission of calc {}] "
                        "local_copy_list format problem: {}".format(
                        calc.pk, e.message))

                remote_copy_list = calcinfo.remote_copy_list
                if remote_copy_list is None:
                    remote_copy_list = []
                try:
                    validate_list_of_string_tuples(remote_copy_list,
                                                   tuple_length = 3)
                except ValidationError as e:
                    raise PluginInternalError("[submission of calc {}] "
                        "remote_copy_list format problem: {}".format(
                        calc.pk, e.message))

                for src_abs_path, dest_rel_path in local_copy_list:
                    execlogger.debug("[submission of calc {}] "
                        "copying local file/folder to {}".format(
                        calc.pk, dest_rel_path))
                    t.put(src_abs_path, dest_rel_path)
                
                for (remote_machine, remote_abs_path, 
                     dest_rel_path) in remote_copy_list:
                    if os.path.isabs(dest_rel_path):
                        raise PluginInternalError("[submission of calc {}] "
                            "The destination path of the remote copy "
                            "is absolute! ({})".format(calc.pk, dest_rel_path))

                    if remote_machine == computer.hostname:
                        execlogger.debug("[submission of calc {}] "
                            "copying {} remotely, directly on the machine "
                            "{}".format(calc.pk, dest_rel_path, remote_machine))
                        try:
                            t.copy(remote_abs_path, dest_rel_path)
                        except (IOError,OSError):
                            execlogger.warning("[submission of calc {}] "
                                "Unable to copy remote resource from {} to {}! "
                                "Stopping.".format(calc.pk,
                                    remote_abs_path,dest_rel_path))
                            raise

                    else:
                        # TODO: implement copy between two different machines!
                        raise NotImplementedError("[submission of calc {}] "
                            "Remote copy between two different machines is "
                            "not implemented yet".format(calc.pk))
        
                remotedata = RemoteData(remote_machine = computer.hostname, 
                        remote_path = workdir).store()

                calc._add_link_to(remotedata, label='remote_folder')

                job_id = s.submit_from_script(t.getcwd(),script_filename)
                calc._set_job_id(job_id)
                calc._set_state(calc_states.WITHSCHEDULER)
                ## I do not set the state to queued; in this way, if the
                ## daemon is down, the user sees '(unknown)' as last state
                ## and understands that the daemon is not running.
                #if job_tmpl.submit_as_hold:
                #    calc._set_scheduler_state(job_states.QUEUED_HELD)
                #else:
                #    calc._set_scheduler_state(job_states.QUEUED)
    
                execlogger.debug("submitted calculation {} on {} with "
                    "jobid {}".format(calc.pk, computer.name, job_id))

    except Exception as e:
        import traceback
        calc._set_state(calc_states.SUBMISSIONFAILED)
        execlogger.debug("Submission of calc {} failed, check also the "
                         "log file! Traceback: {}".format(calc.pk, 
            traceback.format_exc()))
        raise
            
def retrieve_computed_for_authinfo(authinfo):
    from aiida.orm import Calculation
    from aiida.common.folders import SandboxFolder
    from aiida.orm.data.folder import FolderData

    import os
    
    calcs_to_retrieve = Calculation.get_all_with_state(
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
                calc._set_state(calc_states.RETRIEVING)
                try:
                    execlogger.debug("Retrieving calc {}".format(calc.pk))
                    workdir = calc.get_remote_workdir()
                    retrieve_list = calc.get_retrieve_list()
                    execlogger.debug("[retrieval of calc {}] "
                                     "chdir {}".format(calc.pk, workdir))
                    t.chdir(workdir)

                    retrieved_files = FolderData()

                    with SandboxFolder() as folder:
                        for item in retrieve_list:
                            execlogger.debug("[retrieval of calc {}] "
                                "Trying to retrieve remote item '{}'".format(
                                calc.pk, item))
                            t.get(item, os.path.join(
                                folder.abspath,os.path.split(item)[1]),
                                ignore_nonexisting=True)
                        # Here I retrieved everything; 
                        # now I store them inside the calculation
                        retrieved_files.replace_with_folder(folder.abspath,
                                                            overwrite=True)

                    execlogger.debug("[retrieval of calc {}] "
                                     "Storing retrieved_files={}".format(
                        calc.pk, retrieved_files.dbnode.pk))
                    retrieved_files.store()
                    calc._add_link_to(retrieved_files,
                                      label=calc.get_linkname_retrieved())

                    calc._set_state(calc_states.PARSING)

                    Parser = calc.get_parserclass()
                    # If no parser is set, the calculation is successful
                    successful = True 
                    if Parser is not None:
                        # TODO: parse here
                        parser = Parser(calc)
                        successful = parser.parse_from_calc()
                        
                    if successful:
                        calc._set_state(calc_states.FINISHED)
                    else:
                        calc._set_state(calc_states.FAILED)
                    retrieved.append(calc)
                except:
                    import traceback
                    import StringIO
                    buf = StringIO.StringIO()
                    traceback.print_exc(file=buf)
                    buf.seek(0)
                    if calc.get_state() == calc_states.PARSING:
                        execlogger.error("Error parsing calc {}. "
                            "Traceback: {}".format(calc.pk, buf.read()))
                        # TODO: add a 'comment' to the calculation
                        calc._set_state(calc_states.PARSINGFAILED)
                    else:
                        execlogger.error("Error retrieving calc {}".format(
                            calc.pk))
                        calc._set_state(calc_states.RETRIEVALFAILED)
                        raise

            
    return retrieved
