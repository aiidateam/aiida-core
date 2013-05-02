from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from aida.common.datastructures import calcStates
from aida.scheduler.datastructures import jobStates
from aida.djsite.db.models import DbComputer, AuthInfo
from aida.common.exceptions import ConfigurationError, AuthenticationError
from aida.common import aidalogger
from aida.djsite.utils import get_automatic_user
    
execlogger = aidalogger.getChild('execmanager')

def update_running_calcs_status(authinfo):
    """
    Update the states of calculations in WITHSCHEDULER status belonging to user and machine
    as defined in the 'authinfo' table.
    """
    from aida.orm import Calculation, Computer
    from aida.scheduler.datastructures import JobInfo

    execlogger.debug("Updating running calc status for user {} and machine {}".format(
        authinfo.aidauser.username, authinfo.computer.hostname))

    # This returns an iterator over aida Calculation objects
    calcs_to_inquire = Calculation.get_all_with_state(
        state=calcStates.WITHSCHEDULER,
        computer=authinfo.computer,
        user=authinfo.aidauser)
    
    # NOTE: no further check is done that machine and aidauser are correct for each calc in calcs
    s = Computer(dbcomputer=authinfo.computer).get_scheduler()
    t = authinfo.get_transport()

    finished = []

    # I avoid to open an ssh connection if there are no calcs with state WITHSCHEDULER
    if len(calcs_to_inquire):
        jobids_to_inquire = [str(c.get_job_id()) for c in calcs_to_inquire]

        # Open connection
        with t:
            s.set_transport(t)
            # TODO: Check if we are ok with filtering by job (to make this work,
            # I had to remove the check on the retval for getJobs, because if the
            # job has finished and is not in the output of qstat, it gives a nonzero
            # retval)
            found_jobs = s.getJobs(jobs=jobids_to_inquire, as_dict = True)
    
            # I update the status of jobs

            for c in calcs_to_inquire:
                try:
                    jobid = c.get_job_id()
                    if jobid is None:
                        execlogger.error("Calculation {} is WITHSCHEDULER but no job id was found!".format(
                            c.uuid))
                        continue
                    
                    # I check if the calculation to be checked (c) is in the output of qstat
                    if jobid in found_jobs:
                        # jobinfo: the information returned by qstat for this job
                        jobinfo = found_jobs[jobid]
                        execlogger.debug("Inquirying calculation {} ({}): it has jobState={}".format(
                            c.uuid, jobid, jobinfo.jobState))
                        if jobinfo.jobState in [jobStates.DONE, jobStates.FAILED]:
                            finished.append(c)
                            c._set_state(calcStates.FINISHED)
                        elif jobinfo.jobState == jobStates.UNDETERMINED:
                            c._set_state(calcStates.UNDETERMINED)
                            self.logger.error("There is an undetermined calc with uuid {}".format(
                                c.calc.uuid))
                        else:
                            c._set_state(calcStates.WITHSCHEDULER)
    
                        c._set_scheduler_state(jobinfo.jobState)
    
                        c._set_last_jobinfo(jobinfo)
                    else:
                        execlogger.debug("Inquirying calculation {} ({}): not found, assuming "
                                         "jobState={}".format(
                            c.uuid, jobid, jobStates.DONE))

                        # calculation c is not found in the output of qstat
                        finished.append(c)
                        c._set_state(calcStates.FINISHED)
                        c._set_scheduler_state(jobStates.DONE)
                except Exception as e:
                    # TODO: implement a counter, after N retrials set it to a status that
                    # requires the user intervention
                    execlogger.warning("There was an exception for calculation {} ({}): {}".format(
                        c.uuid, e.__class__.__name__, e.message))
                    continue
    
            for c in finished:
                try:
                    detailed_jobinfo = s.get_detailed_jobinfo(jobid=c.get_job_id())
                    last_jobinfo = c.get_last_jobinfo()
                    if last_jobinfo is None:    
                        last_jobinfo = JobInfo()
                        last_jobinfo.jobId = c.get_job_id()
                        last_jobinfo.jobState = jobStates.FINISHED
                    last_jobinfo.detailedJobinfo = detailed_jobinfo
                    c._set_last_jobinfo(last_jobinfo)
                except Exception as e:
                    execlogger.warning("There was an exception while retrieving the detailed jobinfo "
                                       "for calculation {} ({}): {}".format(
                                       c.uuid, e.__class__.__name__, e.message))
                    continue
            
    return finished

def get_authinfo(computer, aidauser):
    from aida.djsite.db.models import DbComputer
    try:
        authinfo = AuthInfo.objects.get(computer=DbComputer.get_dbcomputer(computer),aidauser=aidauser)
    except ObjectDoesNotExist:
        raise AuthenticationError(
            "The aida user {} is not configured to use computer {}".format(
                aidauser.username, computer.hostname))
    except MultipleObjectsReturned:
        raise ConfigurationError(
            "The aida user {} is not configured more than once to use computer {}! "
            "only one configuration is allowed".format(
                aidauser.username, computer.hostname))
    return authinfo

def daemon_main_loop():
    update_jobs()
    retrieve_jobs()

def retrieve_jobs():
    from aida.orm import Calculation
    
    # I create a unique set of pairs (computer, aidauser)
    computers_users_to_check = set(
        Calculation.get_all_with_state(
            state=calcStates.FINISHED,
            only_computer_user_pairs = True)
        )
    
    for dbcomputer_id, aidauser_id in computers_users_to_check:
        dbcomputer = DbComputer.objects.get(id=dbcomputer_id)
        aidauser = User.objects.get(id=aidauser_id)

        execlogger.debug("({},{}) pair to check".format(
            aidauser.username, dbcomputer.hostname))
        try:
            authinfo = get_authinfo(dbcomputer, aidauser)
            retrieve_finished_for_authinfo(authinfo)
        except Exception as e:
            msg = ("Error while retrieving calculation status for aidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aidauser.username,
                       dbcomputer.hostname,
                       e.__class__.__name__, e.message))
            execlogger.error(msg)
            raise

# in daemon
def update_jobs():
    """
    calls an update for each set of pairs (machine, aidauser)
    """
    from aida.orm import Calculation
    
    # I create a unique set of pairs (computer, aidauser)
    computers_users_to_check = set(
        Calculation.get_all_with_state(
            state=calcStates.WITHSCHEDULER,
            only_computer_user_pairs = True)
        )
    
    for dbcomputer_id, aidauser_id in computers_users_to_check:
        dbcomputer = DbComputer.objects.get(id=dbcomputer_id)
        aidauser = User.objects.get(id=aidauser_id)

        execlogger.debug("({},{}) pair to check".format(
            aidauser.username, dbcomputer.hostname))

        try:
            authinfo = get_authinfo(dbcomputer, aidauser)
            finished_calcs = update_running_calcs_status(authinfo)
        except Exception as e:
            msg = ("Error while updating calculation status for aidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aidauser.username,
                       dbcomputer.hostname,
                       e.__class__.__name__, e.message))
            execlogger.error(msg)
            raise

def submit_calc(calc):
    """
    Submit a calculation
    Args:
        calc: the calculation to submit (an instance of the aida.orm.Calculation class)
    """
    import StringIO
    import json
    
    from aida.codeplugins.input import InputPlugin
    from aida.orm import Calculation, Code, Data
    from aida.common.pluginloader import load_plugin
    from aida.common.folders import SandboxFolder
    from aida.common.exceptions import MissingPluginError, InputValidationError
    from aida.scheduler.datastructures import JobTemplate

    
    if not isinstance(calc,Calculation):
        raise ValueError("calc must be a Calculation")
    
    if calc.get_state() != calcStates.NEW:
        raise ValueError("Can only submit calculations with state=NEW! "
                         "(state is {} instead)".format(
                             calc.get_state()))

    # TODO: do some sort of blocking call, to be sure that the submit function is not called
    # twice for the same calc?
    # I start to submit the calculation: I set the state
    calc._set_state(calcStates.SUBMITTING)
         
    try:
        authinfo = get_authinfo(calc.get_computer(), calc.get_user())
        s = calc.get_computer().get_scheduler()
        t = authinfo.get_transport()
    
        input_codes = calc.get_inputs(type=Code)
        if len(input_codes) != 1:
            raise InputValidationError("Calculation must have one and only one input code")
        code = input_codes[0]
    
        computer = calc.get_computer()

        if not code.can_run_on(computer):
            raise InputValidationError("The selected code {} cannot run on machine {}".format(
                code.uuid, calc.get_computer().hostname))
    
        # load dynamically the input plugin
        Plugin = load_plugin(InputPlugin, 'aida.codeplugins.input', code.get_input_plugin())
    
        with SandboxFolder() as folder:
            plugin = Plugin()
            calcinfo = plugin.create(calc, calc.get_inputs(type=Data,also_labels=True), folder)
    
            # TODO: support -V option of schedulers!

            calc._set_retrieve_list(calcinfo.retrieve_list if calcinfo.retrieve_list is not None else [])
    
            # I create the job template to pass to the scheduler
            job_tmpl = JobTemplate()
            ## TODO: in the future, allow to customize the following variables
            job_tmpl.submitAsHold = False
            job_tmpl.rerunnable = False
            job_tmpl.jobEnvironment = {}
            #'email', 'emailOnStarted', 'emailOnTerminated',
            job_tmpl.jobName = 'aida-{}'.format(calc.uuid) 
            job_tmpl.schedOutputPath = 'scheduler-stdout.txt'
            job_tmpl.schedErrorPath = 'scheduler-stderr.txt'
            job_tmpl.schedJoinFiles = False
            
            # TODO: add also code from the machine + u'\n\n'
            job_tmpl.prependText = (
                ((computer.get_prepend_text() + u"\n\n") if computer.get_prepend_text() else u"") + 
                ((code.get_prepend_text() + u"\n\n") if code.get_prepend_text() else u"") + 
                (calcinfo.prependText if calcinfo.prependText is not None else u""))
            job_tmpl.appendText = (
                (calcinfo.appendText if calcinfo.appendText is not None else u"") +
                ((code.get_append_text() + u"\n\n") if code.get_append_text() else u"") +
                ((computer.get_append_text() + u"\n\n") if computer.get_append_text() else u""))

            # The Calculation validation should take care of always having a sensible value here
            # so I don't need to check
            num_nodes = calc.get_num_nodes()
            num_cpus_per_node = calc.get_num_cpus_per_node()
            tot_num_cpus = num_nodes * num_cpus_per_node
    
            mpi_args = [arg.format(num_nodes=num_nodes,
                                   num_cpus_per_node=num_cpus_per_node,
                                   tot_num_cpus=tot_num_cpus) for arg in
                        computer.get_mpirun_command()]
            job_tmpl.argv = mpi_args + [code.get_execname()] + (
                calcinfo.cmdlineParams if calcinfo.cmdlineParams is not None else [])
    
            job_tmpl.stdinName = calcinfo.stdinName
            job_tmpl.stdoutName = calcinfo.stdoutName
            job_tmpl.stderrName = calcinfo.stderrName
            job_tmpl.joinFiles = calcinfo.joinFiles

            queue_name = calc.get_queue_name()
            if queue_name is not None:
                job_tmpl.queueName = queue_name
            priority = calc.get_priority()
            if priority is not None:
                job_tmpl.priority = priority
            maxMemoryKb = calc.get_max_memory_kb()
            if maxMemoryKb is not None:
                job_tmpl.maxMemoryKb = maxMemoryKb
            maxWallclockSeconds = calc.get_max_wallclock_seconds()
            if maxWallclockSeconds is not None:
                job_tmpl.maxWallclockSeconds = maxWallclockSeconds
            maxMemoryKb = calc.get_max_memory_kb()
            if maxMemoryKb is not None:
                job_tmpl.maxMemoryKb = maxMemoryKb

            job_tmpl.numNodes = num_nodes
            job_tmpl.numCpusPerNode = num_cpus_per_node
    
            # TODO: give possibility to use a different name??
            script_filename = 'aida.submit'
            script_content = s.get_submit_script(job_tmpl)
            folder.create_file_from_filelike(StringIO.StringIO(script_content),script_filename)
    
            subfolder = folder.get_subfolder('.aida',create=True)
            subfolder.create_file_from_filelike(StringIO.StringIO(json.dumps(job_tmpl)),'job_tmpl.json')
            subfolder.create_file_from_filelike(StringIO.StringIO(json.dumps(calcinfo)),'calcinfo.json')
            
            
            with t:
                s.set_transport(t)
                remote_user = t.whoami()
                # TODO Doc: {username} field
                remote_working_directory = calc.get_computer().get_workdir().format(username=remote_user)
                if not remote_working_directory.strip():
                    raise ConfigurationError("No remote_working_directory configured for the computer")
    
                t.chdir(remote_working_directory)
                # Sharding
                t.mkdir(calcinfo.uuid[:2],ignore_existing=True)
                t.chdir(calcinfo.uuid[:2])
                t.mkdir(calcinfo.uuid[2:])
                t.chdir(calcinfo.uuid[2:])
                # I store the workdir of the calculation for later file retrieval
                calc._set_remote_workdir(t.getcwd())
                
                # copy all files, recursively with folders
                for f, _ in folder.get_content_list():
                    execlogger.debug("copying file {}...".format(f))
                    t.put(folder.get_file_path(f), f)

                # TODO!! copy local resources remotely
                # TODO!! manage remote copy
    
                if code.is_local():
                    # Note: this will possibly overwrite files
                    for f, _ in code.repo_folder.get_content_list():
                        t.put(code.repo_folder.get_file_path(f), f)
                    t.chmod(code.get_local_executable(), 0755) # rwxr-xr-x
    
                job_id = s.submit_from_script(t.getcwd(),script_filename)
                calc._set_job_id(job_id)
                calc._set_state(calcStates.WITHSCHEDULER)
                if job_tmpl.submitAsHold:
                    calc._set_scheduler_state(jobStates.QUEUED_HELD)
                else:
                    calc._set_scheduler_state(jobStates.QUEUED)

    
                execlogger.debug("submitted calculation {} with job id {}".format(
                    calc.uuid, job_id))

                # TODO: decide where to store the whole folder
                #       with the files created by the input plugin
    except:
        calc._set_state(calcStates.SUBMISSIONFAILED)
        raise
            
def retrieve_finished_for_authinfo(authinfo):
    from aida.orm import Calculation
    from aida.common.folders import SandboxFolder
    import os
    
    calcs_to_retrieve = Calculation.get_all_with_state(
        state=calcStates.FINISHED,
        computer=authinfo.computer,
        user=authinfo.aidauser)
    
    retrieved = []
    
    # I avoid to open an ssh connection if there are no calcs with state FINISHED
    if len(calcs_to_retrieve):

        # Open connection
        with authinfo.get_transport() as t:
            for calc in calcs_to_retrieve:
                try:
                    # TODO: MOVE THE FOLLOWING CODE IN A NEW FUNCTION,
                    # receiving the open transport and the calculation.
                    # TODO: 
                    execlogger.debug("Retrieving calc {} ({})".format(calc.dbnode.pk, calc.uuid))
                    workdir = calc.get_remote_workdir()
                    retrieve_list = calc.get_retrieve_list()
                    execlogger.debug("chdir {}".format(workdir))
                    t.chdir(workdir)
                    # TODO: create remote_output node always
                    # TODO: decide what to do: one node per element in the retrieve_list, or
                    #       one node for everything (problem of overwriting; we can say that we
                    #       write in order, so following things overwrite previous things;
                    #       or change the way in which we store the retrieve list so that it is
                    #       a tuple of two elements, with source and dest.

                    with SandboxFolder() as folder:
                        for item in retrieve_list:
                            t.get(item,
                                  os.path.join(folder.abspath,os.path.split(item)[1]))

                    calc._set_state(calcStates.RETRIEVED)
                    retrieved.append(calc)
                except:
                    execlogger.error("Error retrieving calc {}".format(calc.uuid))
                    calc._set_state(calcStates.RETRIEVALFAILED)
                    raise

            
    return retrieved
