from django.exceptions import DoesNotExist
from django.contrib.auth.models import User as AidaUser 

from aida.common.datastructures import calcStates
from aida.scheduler.datastructures import jobStates
from aida.djsite.db.models import Computer, AuthInfo, RunningJob
from aida.common.exceptions import DBContentError, ConfigurationError, AuthenticationError
    
def update_running_table(authinfo):
    """
    Update the status in WITHSCHEDULER status belonging to user 'aidauser' and running on
    computer 'computer'.

    Args:
        computer: a Django object for the computer
        aidauser: a Django object for the aida user
    """
    import json
    
    calcs_to_inquire = RunningJob.objects.filter(
        state=calcStates.WITHSCHEDULER,
        calc__computer=authinfo.computer,
        calc__aidauser=authinfo.aidauser)

    # NOTE: no further check is done that machine and aidauser are correct for each calc in calcs
    s = authinfo.computer.get_scheduler()
    t = authinfo.get_transport()

    # I avoid to open an ssh connection if there are no calcs with state WITHSCHEDULER
    if len(calcs_to_inquire):
        # Open connection
        with t:
            s.set_transport(t)
            # TODO: see if we want to filter already here the jobs only for the given user,
            # or on the list of jobs
            jobs = s.getJobs(as_dict = True)
    
            # I update the status of jobs
            finished = []
            for c in calcs_to_inquire:
                # I check if the calculation to be checked (c) is in the output of qstat
                if c.job_id in jobs:
                    # jobinfo: the information returned by qstat for this job
                    jobinfo = jobs[c.job_id]
                    if jobinfo.jobState in [jobStates.DONE, jobStates.FAILED]:
                        finished.append(c)
                        c.state = calcStates.FINISHED
                    elif jobinfo.jobState == jobStates.UNDETERMINED:
                        c.state = calcStates.UNDETERMINED
                        self.logger.error("There is an undetermined calc with uuid {}".format(
                            c.calc.uuid))
                    else:
                        c.state = calcStates.WITHSCHEDULER
                    c.scheduler_state = jobinfo.jobState
                    c.last_jobinfo = json.dumps(jobinfo)
                else:
                    # calculation c is not found in the output of qstat
                    finished.append(c)
                    c.state = calcStates.FINISHED
                c.save()

            # TODO: implement this part
            # TODO: understand if this second save may cause problems if we have many threads
            for c in finished:
                # c.last_jobinfo = json.dumps(>>> GET MORE DETAILED INFO OF FINISHED JOB <<<)
                # c.save()
                pass

# in daemon
def daemon():
    update_jobs()
    # Now, finished jobs have a 'finished' status in DB
    # here, do tricks to 
    retrieve_finished()
    parse_results()
    ...

# in daemon
def retrieve_finished():
    computers_users_to_check = set(
        RunningJob.objects.filter(state=calcStates.WITHSCHEDULER).values_list(
            'calc__computer__id', 'calc__aidauser__id'))

# in daemon
def update_jobs():
    """
    calls an update for each set of pairs (machine, aidauser)
    """
    # I create a unique set of pairs (computer, aidauser)
    computers_users_to_check = set(
        RunningJob.objects.filter(state=calcStates.WITHSCHEDULER).values_list(
            'calc__computer__id', 'calc__aidauser__id'))

    for computer_id, aidauser_id in computers_users_to_check:
        computer = Computer.objects.get(id=computer_id)
        aidauser = AidaUser.objects.get(id=aidauser_id)
        try:
            try:
                authinfo = AuthInfo.objects.get(computer=computer,aidauser=aidauser)
            except DoesNotExist:
                # I do not check for MultipleObjectsReturned thanks to
                # the unique_together constraint
                raise AuthenticationError(
                    "The aida user {} is not configured to use computer {}".format(
                        aidauser.username, computer.hostname))
            authinfo.update_running_table()
        except Exception as e:
            # TODO: set logger properly
            msg = ("Error while updating RunningJob table for aidauser={} on computer={}, "
                   "error type is {}, error message: {}".format(
                       aidauser.username,
                       computer.hostname,
                       e.__class__.__name, e.message))
            logger.error(msg)


