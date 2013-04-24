from django.exceptions import DoesNotExist
from django.contrib.auth.models import User as AidaUser 

from aida.common.datastructures import calcStates
from aida.scheduler.datastructures import jobStates
from aida.djsite.main.models import Computer, AuthInfo, RunningJob
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


class Computer(NameClass):
    """Table of computers or clusters.

    Attributes:
        hostname: Full hostname of the host
        workdir: Full path of the aida folder on the host. It can contain
            the string {username} that will be substituted by the username
            of the user on that machine.
            The actual workdir is then obtained as
            workdir.format(username=THE_ACTUAL_USERNAME)
            Example: 
            workdir = "/scratch/{username}/aida/"
        transport_type: a string with a valid transport type
    """
    hostname = m.CharField(max_length=255, unique=True)
    workdir = m.CharField(max_length=255)
    transport_type = m.CharField(max_length=64)
    scheduler_type = m.CharField(max_length=64)
    transport_params = m.TextField(default="{}") # Will store a json

    def get_transport_params(self):
        import json
        try:
            return json.loads(self.transport_params)
        except ValueError:
            raise DBContentError(
                "Error while reading transport_params for computer {}".format(
                    self.hostname))
        
    def get_scheduler(self):
        import aida.scheduler
        from aida.common.pluginloader import load_plugin

        try:
            ThisPlugin = load_plugin(aida.scheduler.Scheduler, 'aida.scheduler.plugins',
                               self.scheduler_type)
            # I call the init without any parameter
            return ThisPlugin()
        except ImportError as e:
            raise ConfigurationError('No scheduler found for {} [type {}], message: {}'.format(
                self.hostname, self.scheduler_type, e.message))

class RunningJob(m.Model):
    calc = m.OneToOneField(Node) # OneToOneField implicitly sets unique=True
    state = m.CharField(max_length=64)
    job_id = m.CharField(max_length=255)
    scheduler_state = m.CharField(max_length=64)
    last_jobinfo = m.TextField(default='{}')  # Will store a json

class AuthInfo(m.Model):
    """
    Table that pairs aida users and computers, with all required authentication
    information.
    """
    aidauser = m.ForeignKey(User)
    computer = m.ForeignKey(Computer)
    remoteuser = m.CharField(max_length=255) # merge with following field?
    auth_params = m.TextField(default='{}')  # Will store a json

    class Meta:
        unique_together = (("aidauser", "computer"),)

    def update_running_table(self):
        import aida
        aida.execmanager.update_running_table(self)

    def get_auth_params(self):
        import json
        try:
            return json.loads(self.auth_params)
        except ValueError:
            raise DBContentError(
                "Error while reading auth_params for authinfo, aidauser={}, computer={}".format(
                    self.aidauser, self.computer))

    # a method of AuthInfo
    def get_transport(self):
        """
        Given a computer and an aida user (as entries of the DB) return a configured
        transport to connect to the computer.
        """    
        from aida.common.pluginloader import load_plugin

        try:
            ThisTransport = load_plugin(aida.transport.Transport, 'aida.transport.plugins',
                                        self.computer.transport_type)
        except ImportError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.computer.hostname, self.computer.transport_type, e.message))

        params = self.computer.get_transport_params() + self.get_auth_params()
        return ThisTransport(machine=computer.hostname,**params)
