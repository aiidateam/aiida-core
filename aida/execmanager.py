from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from aida.common.datastructures import calcStates
from aida.scheduler.datastructures import jobStates
from aida.djsite.db.models import Computer, AuthInfo
from aida.common.exceptions import DBContentError, ConfigurationError, AuthenticationError
from aida.common import aidalogger
from aida.djsite.utils import get_automatic_user
    
def update_running_calcs_status(authinfo):
    """
    Update the states of calculations in WITHSCHEDULER status belonging to user and machine
    as defined in the 'authinfo' table.
    """
    from aida.orm import Calculation

    aidalogger.info("Updating running calc status for user {} and machine {}".format(
        authinfo.aidauser.username, authinfo.computer.hostname))

    # This returns an iterator over aida Calculation objects
    calcs_to_inquire = Calculation.get_all_with_state(
        state=calcStates.WITHSCHEDULER,
        computer=authinfo.computer,
        user=authinfo.aidauser)
    
    # NOTE: no further check is done that machine and aidauser are correct for each calc in calcs
    s = authinfo.computer.get_scheduler()
    t = authinfo.get_transport()

    finished = []

    # I avoid to open an ssh connection if there are no calcs with state WITHSCHEDULER
    if len(calcs_to_inquire):
        # Open connection
        with t:
            s.set_transport(t)
            # TODO: see if we want to filter already here the jobs only for the given user,
            # or on the list of jobs
            found_jobs = s.getJobs(as_dict = True)
    
            # I update the status of jobs

            for c in calcs_to_inquire:
                jobid = c.get_job_id()
                if jobid is None:
                    aidalogger.error("Calculation {} is WITHSCHEDULER but no job id was found!".format(
                        c.uuid))
                    continue
                
                # I check if the calculation to be checked (c) is in the output of qstat
                if jobid in found_jobs:
                    # jobinfo: the information returned by qstat for this job
                    jobinfo = found_jobs[jobid]
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
                    # calculation c is not found in the output of qstat
                    finished.append(c)
                    c._set_state(calcStates.FINISHED)

            # TODO: implement this part
            # TODO: understand if this second save may cause problems if we have many threads
            for c in finished:
                # c._set_last_jobinfo(json.dumps(>>> GET MORE DETAILED INFO OF FINISHED JOB <<<))
                pass

            ## in daemon
            #def daemon():
            #update_jobs()
            ## Now, finished jobs have a 'finished' status in DB
            ## retrieve_finished() # < WILL LOOK FOR THINGS IN A FINISHED STATUS
            ## parse_results()
            ##...
            
    return finished

def get_authinfo(computer, aidauser):
    try:
        authinfo = AuthInfo.objects.get(computer=computer,aidauser=aidauser)
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
    
    for computer_id, aidauser_id in computers_users_to_check:
        computer = Computer.objects.get(id=computer_id)
        aidauser = User.objects.get(id=aidauser_id)

        aidalogger.info("({},{}) pair to check".format(
            aidauser.username, computer.hostname))

        try:
            authinfo = get_authinfo(computer, aidauser)
            finished_calcs = update_running_calcs_status(authinfo)
            print "*** '{}' for machine '{}' ***".format(aidauser.username, computer.hostname)
            for c in finished_calcs:
                print '-> FINISHED: ', c.uuid, c.get_job_id(), c.get_scheduler_state()
        except Exception as e:
            # TODO: set logger properly
            msg = ("Error while updating calculation status for aidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aidauser.username,
                       computer.hostname,
                       e.__class__.__name__, e.message))
            aidalogger.error(msg)
            raise


def submit_calc(calc):
    """
    Submit a calculation
    Args:
        calc: the calculation to submit (an instance of the aida.orm.Calculation class)

    # TODO: maybe change the calcinfo to contain only the relevant information from the plugin,
    # if everything else is managed within this function! And move the logic to create the job template
    # here, instead that in the scheduler plugin. Adapt also pbspro script.
    """
    import StringIO
    
    from aida.codeplugins.input import InputPlugin
    from aida.orm import Calculation, Code, Data
    from aida.common.pluginloader import load_plugin
    from aida.common.folders import SandboxFolder
    from aida.common.exceptions import MissingPluginError
    from aida.scheduler.datastructures import JobTemplate
    
    if not isinstance(calc,Calculation):
        raise ValueError("calc must be a Calculation")

    if calc.get_state() != calcStates.NEW:
        raise ValueError("Can only submit calculations with state=NEW! (state is {} instead".format(
            calc.get_state()))

    # I start to submit the calculation: I set the state
    calc._set_state(calcStates.SUBMITTING)
    
    authinfo = get_authinfo(calc.get_computer(), calc.get_user())
    s = authinfo.computer.get_scheduler()
    t = authinfo.get_transport()

    input_codes = calc.get_inputs(type=Code)
    if len(input_codes) != 1:
        # TODO: Raise InputValidationError instead? Move it from codeplugins to aida.common.exceptions?
        raise LinkingError("Calculation must have one and only one input code")
    code = input_codes[0]

    if not code.can_run_on(calc.get_computer()):
        raise InputValidationError("The selected code {} cannot run on machine {}".format(
            code.uuid, calc.get_computer().hostname))

    # load dynamically the input plugin
    try:
        Plugin = load_plugin(InputPlugin, 'aida.codeplugins.input', code.get_input_plugin())
    except ImportError as e:
        # TODO: use this exception also elsewhere; actually, raise it directly from within the load_plugin
        # module
        raise MissingPluginError("Missing plugin for code input! {}".format(e.message))

    with SandboxFolder() as folder:
        plugin = Plugin()
        calcinfo = plugin.create(calc, calc.get_inputs(type=Data,also_labels=True), folder)

        # TODO: enrich the calcinfo object with the following properties from the Calculation
        # object
        # 'email', 'emailOnStarted', 'emailOnTerminated', 'rerunnable', 'queueName',
        # 'numNodes', 'priority', 'maxWallclockSeconds', 'maxMemoryKb'

        # TODO: enrich with the list of things to retrieve!

        # TODO: store the list of things to retrieve somewhere!

        # to be put as a property of the machine 'numCpusPerNode'

        # TODO: implement validation for jobtemplate

        
        ####### I create the job template to pass to the scheduler
        ## TODO check for hardcoded values
        job_tmpl = JobTemplate()
        job_tmpl.submitAsHold = False
        job_tmpl.rerunnable = False
        job_tmpl.jobEnvironment = {}
        # TODO: set email, emailOn...
        job_tmpl.jobName = 'aida-{}'.format(calc.uuid) 
        job_tmpl.schedOutputPath = 'scheduler-stdout.txt'
        job_tmpl.schedErrorPath = 'scheduler-stderr.txt'
        job_tmpl.schedJoinFiles = False

        # TODO: add also code from the machine + u'\n\n'
        job_tmpl.prependText = code.get_prepend_text() + u'\n\n' + (
            calcinfo.prependText if calcinfo.prependText is not None else u"")
        job_tmpl.appendText = (calcinfo.prependText if calcinfo.prependText is not None
                               else u"") + u'\n\n' + code.get_append_text()

        # TODO: ADD ALSO THE MPIRUN PART
        job_tmpl.argv = [code.get_execname()] + (
            calcinfo.cmdlineParams if calcinfo.cmdlineParams is not None else [])

        job_tmpl.stdinName = calcinfo.stdinName
        job_tmpl.stdoutName = calcinfo.stdoutName
        job_tmpl.stderrName = calcinfo.stderrName
        job_tmpl.joinFiles = calcinfo.joinFiles
        
        #job_tmpl.queueName = calc_info.queueName
        #job_tmpl.priority = ...
        #job_tmpl.maxMemoryKb = ...
        job_tmpl.maxWallclockSeconds = 12*60 # 12 min
        job_tmpl.numNodes = 1
        job_tmpl.numCpusPerNode = 1

        # TODO: give possibility to use a different name??
        script_filename = 'aida.submit'
        script_content = s.get_submit_script(job_tmpl)
        folder.create_file_from_filelike(StringIO.StringIO(script_content),script_filename)

        # TODO: create a node of type local directory to store the created files
        # TODO: add a .aida folder with a pickle of the calcinfo and job_tmpl objects, for debugging
        #       purposes
        
        with t:
            s.set_transport(t)

            remote_user = t.whoami()
            # TODO Doc: {username} field
            remote_working_directory = calc.get_computer().workdir.format(username=remote_user)
            if not remote_working_directory.strip():
                raise ConfigurationError("No remote_working_directory configured for the computer")

            t.chdir(remote_working_directory)
            # TODO: sharding?
            # TODO: store the folder in the calculation!!
            t.mkdir(calcinfo.uuid[:2])
            t.chdir(calcinfo.uuid[:2])
            t.mkdir(calcinfo.uuid[2:])
            t.chdir(calcinfo.uuid[2:])

            calc._set_remote_workdir(t.getcwd())
            
            # copy all files, recursively with folders
            aidalogger.warning("NO RECURSION IMPLEMENTED HERE!")
            for f, _ in folder.get_content_list():
                aidalogger.info("copying file {}...".format(f))
                t.put(folder.get_file_path(f), f)

            if code.is_local():
                # Maybe do it differently?
                for f, _ in code.repo_folder.get_content_list():
                    aidalogger.info("copying code file {}...".format(f))
                    t.put(code.repo_folder.get_file_path(f), f)
                t.chmod(code.get_local_executable(), 0755) # rwxr-xr-x
                    

            # TODO!! Adapt also the calcInfo class, etc.
            # manage local resources
            # manage remote copy

            job_id = s.submit_from_script(t.getcwd(),script_filename)
            calc._set_job_id(job_id)
            calc._set_state(calcStates.WITHSCHEDULER)

            aidalogger.info("submitted calculation {} with job id {}".format(
                calc.uuid, job_id))

            
