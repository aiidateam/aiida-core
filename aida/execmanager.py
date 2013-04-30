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
                jobid = c.get_jobid()
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
        try:
            authinfo = get_authinfo(computer, aidauser)
            finished_calcs = update_running_calcs_status(authinfo)
            print "*** '{}' for machine '{}' ***".format(aidauser.username, computer.hostname)
            for c in finished_calcs:
                print c
        except Exception as e:
            # TODO: set logger properly
            msg = ("Error while updating RunningJob table for aidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aidauser.username,
                       computer.hostname,
                       e.__class__.__name, e.message))
            aidalogger.error(msg)


def submit_calc(calc):
    """
    Submit a calculation
    Args:
        calc: the calculation to submit (an instance of the aida.orm.Calculation class)

    # TODO: check that there is one node for parallelization info, ...
    #       Probably set them as properties of the calculation, before storing it?
    """
    from aida.codeplugins import CodePlugin
    from aida.orm import Calculation, Code
    from aida.common.pluginloader import load_plugin
    
    if not isinstance(calc,Calculation):
        raise ValueError("calc must be a Calculation")
    
    authinfo = get_authinfo(calc.get_computer(), calc.get_user())
    s = authinfo.computer.get_scheduler()
    t = authinfo.get_transport()

    input_codes = list(Code.query(outputs=calc))
    if len(input_codes) != 1:
        raise LinkingError("Calculation must have one and only one input code")
    input_code = input_codes[0]

    # load dynamically the input plugin
    InputPlugin = load_plugin(CodePlugin, 'aida.codeplugins.input', input_code.get_input_plugin())

    
    # call the input plugin create() method, passing a list of input data with label, and
    #    retrieving the calcinfo object
    # get the output folder, and call the method to submit (to be written, if I remember correctly)
