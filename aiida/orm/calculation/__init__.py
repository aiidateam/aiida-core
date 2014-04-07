from aiida.orm import Node
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.utils import classproperty

#TODO: set the following as properties of the Calculation
#        'email',
#        'email_on_started',
#        'email_on_terminated',
#        'rerunnable',
#        'resourceLimits',

_input_subfolder = 'raw_input'

class Calculation(Node):
    """
    This class provides the definition of an AiiDA calculation.
    """
    _updatable_attributes = ('state', 'job_id', 'scheduler_state',
                             'scheduler_lastchecktime',
                             'last_jobinfo', 'remote_workdir', 'retrieve_list')
    
    # By default, no output parser
    _default_parser = None
    # Set default for the link to the retrieved folder (after calc is done)
    _linkname_retrieved = 'retrieved' 
    
    # Default values to be set for new nodes
    @classproperty
    def _set_defaults(cls):
        return {"_state": calc_states.NEW,
                "parser_name": cls._default_parser,
                "linkname_retrieved": cls._linkname_retrieved,
          }
            
    def validate(self):
        """
        Verify if all the input nodes are present and valid.

        :raise: ValidationError: if invalid parameters are found.
        """
        from aiida.common.exceptions import MissingPluginError, ValidationError
        
        super(Calculation,self).validate()

        if self.get_computer() is None:
            raise ValidationError("You did not specify any computer")
        
        if self.get_state() not in calc_states:
            raise ValidationError("Calculation state '{}' is not valid".format(
                self.get_state()))

        try:
            _ = self.get_parserclass()
        except MissingPluginError:
            raise ValidationError("No valid plugin found for the parser '{}'. "
                "Set the parser to None if you do not need an automatic "
                "parser.".format(self.get_parser_name()))

        computer = self.get_computer()        
        s = computer.get_scheduler()
        try:
            _ = s.create_job_resource(**self.get_resources())
        except (TypeError, ValueError) as e:
            raise ValidationError("Invalid resources for the scheduler of the "
                                  "specified computer: {}".format(e.message))

        if not isinstance(self.get_withmpi(), bool):
            raise ValidationError("withmpi property must be boolean! It in instead {}".format(str(type(self.get_withmpi()))))
           

    def can_link_as_output(self,dest):
        """
        An output of a calculation can only be a data, and can only be set 
        when the calculation is in the SUBMITTING or RETRIEVING or
        PARSING state.
        (during SUBMITTING, the execmanager adds a link to the remote folder; 
        all other links are added while in the retrieving phase)

        :param dest: a Data object instance of the database
        :raise: ValueError if a link from self to dest is not allowed.
        """
        from aiida.orm import Data

        valid_states = [
              calc_states.SUBMITTING,
              calc_states.RETRIEVING,
              calc_states.PARSING,
              ]
        
        if not isinstance(dest, Data):
            raise ValueError(
                "The output of a calculation node can only be a data node")

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can add an output node to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(Calculation, self).can_link_as_output(dest)

    def _store_raw_input_folder(self, folder_path):
        """
        Copy the content of the folder internally, in a subfolder called
        'raw_input'

        :param folder_path: the path to the folder from which the content
               should be taken
        """
        # This function can be called only if the state is SUBMITTING
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed(
                "The raw input folder can be stored only if the "
                "state is SUBMITTING, it is instead {}".format(
                    self.get_state()))

        # get subfolder and replace with copy
        raw_input_folder = self.current_folder.get_subfolder(
            _input_subfolder,create=True)
        raw_input_folder.replace_with_folder(
            folder_path, move=False, overwrite=True)

    @property
    def raw_input_folder(self):
        """
        Get the input folder object.
        
        :return: the input folder object.
        :raise: NotExistent: if the raw folder hasn't been created yet
        """
        from aiida.common.exceptions import NotExistent

        return_folder = self.current_folder.get_subfolder(_input_subfolder)
        if return_folder.exists():
            return return_folder
        else:
            raise NotExistent("raw_input_folder not created yet")

    def set_queue_name(self,val):
        """
        Set the name of the queue on the remote computer.
        
        :param str val: the queue name
        """
        if val is None:
            self.set_attr('queue_name',None)
        else:
            self.set_attr('queue_name',unicode(val))

    def set_import_sys_environment(self,val):
        """
        If set to true, the submission script will load the system 
        environment variables.
        
        :param bool val: load the environment if True 
        """
        self.set_attr('import_sys_environment',bool(val))

    def get_import_sys_environment(self):
        """
        To check if it's loading the system environment on the submission script.
        
        :return: a boolean. If True the system environment will be load.
        """
        return self.get_attr('import_sys_environment',True)
                
    def set_priority(self,val):
        """
        Set the priority of the job to be queued.

        :param val: the values of priority as accepted by the cluster scheduler.
        """
        self.set_attr('priority',unicode(val))
    
    def set_max_memory_kb(self,val):
        """
        Set the maximum memory to be asked to the scheduler.
        
        :param val: an integer. Default=None
        """
        self.set_attr('max_memory_kb',int(val))

    def set_max_wallclock_seconds(self,val):    
        """
        Set the wallclock in seconds asked to the scheduler.
        
        :param val: An integer. Default=None
        """
        self.set_attr('max_wallclock_seconds',int(val))

    def set_resources(self, resources_dict):
        """
        Set the dictionary of resources to be used by the scheduler plugin.
        """
        # Note: for the time being, resources are only validated during the
        # 'store' because here we are not sure that a Computer has been set
        # yet (in particular, if both computer and resources are set together
        # using the .set() method).
        self.set_attr('jobresource_params', resources_dict)
    
    def set_withmpi(self,val):
        """
        Set the calculation to use mpi.
        
        :param val: A boolean. Default=True
        """
        self.set_attr('withmpi',val)

    def get_withmpi(self):        
        """
        Get whether the job is set with mpi execution.
        
        :return: a boolean. Default=True.
        """
        return self.get_attr('withmpi',True)
    
    def get_resources(self):
        """
        Returns the dictionary of the job resources set.
        
        :return: a dictionary
        """
        return self.get_attr('jobresource_params', {})

    def get_queue_name(self):
        """
        Get the name of the queue on cluster.
        
        :return: a string or None.
        """
        return self.get_attr('queue_name', None)

    def get_priority(self):
        """
        Get the priority, if set, of the job on the cluster.
        
        :return: a string or None
        """
        return self.get_attr('priority', None)
    
    def get_max_memory_kb(self):
        """
        Get the memory requested to the scheduler.
        
        :return: an integer
        """
        return self.get_attr('max_memory_kb', None)

    def get_max_wallclock_seconds(self):
        """
        Get the max wallclock time requested to the scheduler.
        
        :return: an integer
        """
        return self.get_attr('max_wallclock_seconds', None)
        
    def _add_link_from(self,src,label=None):
        '''
        Add a link with a code as destination.
        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.
        
        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link. Default=None
        '''
        
        from aiida.orm.data import Data
        from aiida.orm.code import Code
        
        
        if not isinstance(src,(Data, Code)):
            raise ValueError("Nodes entering in calculation can only be of "
                             "type data or code")
        
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can add an input node to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(Calculation,self)._add_link_from(src, label)

    def _set_state(self, state):
        if state not in calc_states:
            raise ValueError(
                "'{}' is not a valid calculation status".format(state))
        self.set_attr('state', state)

    def get_state(self):
        """
        Get the state of the calculation.
        
        :return: a string.
        """
        return self.get_attr('state', None)

    def is_new(self):
        """
        Get whether the calculation is in the NEW status.
        
        :return: a boolean
        """
        return self.get_state() in [calc_states.NEW]

    def is_running(self):
        """
        Get whether the calculation is in a running state,
        i.e. one of TOSUBMIT, SUBMITTING, WITHSCHEDULER, 
        COMPUTED, RETRIEVING or PARSING.
        
        :return: a boolean
        """
        return self.get_state() in [
            calc_states.TOSUBMIT, calc_states.SUBMITTING, calc_states.WITHSCHEDULER,
            calc_states.COMPUTED, calc_states.RETRIEVING, calc_states.PARSING]

    def has_finished_ok(self):
        """
        Get whether the calculation is in the FINISHED status.
        
        :return: a boolean
        """
        return self.get_state() in [calc_states.FINISHED]

    def has_failed(self):
        """
        Get whether the calculation is in a failed status,
        i.e. UNDETERMINED, SUBMISSIONFAILED, RETRIEVALFAILED, PARSINGFAILED or FAILED.
        
        :return: a boolean
        """
        return self.get_state() in [calc_states.UNDETERMINED, calc_states.SUBMISSIONFAILED,
            calc_states.RETRIEVALFAILED, calc_states.PARSINGFAILED, calc_states.FAILED]

    def _set_remote_workdir(self, remote_workdir):
        if self.get_state() != calc_states.SUBMITTING:   
            raise ModificationNotAllowed(
                "Cannot set the remote workdir if you are not "
			    "submitting the calculation (current state is "
				"{})".format(self.get_state()))
        self.set_attr('remote_workdir', remote_workdir)

    def get_remote_workdir(self):
        """
        Get the path to the remote (on cluster) scratch folder of the calculation.
        
        :return: a string with the remote path
        """
        return self.get_attr('remote_workdir', None)

    def _set_retrieve_list(self, retrieve_list):
        if self.get_state() not in (calc_states.SUBMITTING,
                                    calc_states.NEW):
            raise ModificationNotAllowed(
                "Cannot set the retrieve_list for a calculation "
				"that is neither NEW nor SUBMITTING (current state is "
		        "{})".format(self.get_state()))

        if (not(isinstance(retrieve_list,(tuple,list))) or
	           not(all(isinstance(i,basestring) for i in retrieve_list))):
            raise ValueError("You have to pass a list (or tuple) of strings "
                             "as retrieve_list")
        self.set_attr('retrieve_list', retrieve_list)

    def get_retrieve_list(self):
        """
        Get the list of files/directories to be retrieved on the cluster.
        Their path is relative to the remote workdirectory path.
        
        :return: a list of strings for file/directory names
        """
        return self.get_attr('retrieve_list', None)

    def _set_job_id(self, job_id):
        """
        Always set as a string
        """
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed("Cannot set the job id if you are not "
					 "submitting the calculation (current state is "
					 "{})".format(self.get_state()))

        return self.set_attr('job_id', unicode(job_id))
    
    def get_job_id(self):
        """
        Get the scheduler job id of the calculation.
        
        :return: a string
        """
        return self.get_attr('job_id', None)
        
    def _set_scheduler_state(self,state):
        # I don't do any test here on the possible valid values,
        # I just convert it to a string
        from django.utils import timezone
        
        self.set_attr('scheduler_state', unicode(state))
        self.set_attr('scheduler_lastchecktime', timezone.now())
                
    def get_scheduler_state(self):
        """
        Return the status of the calculation according to the cluster scheduler.
        
        :return: a string.
        """
        return self.get_attr('scheduler_state', None)

    def get_scheduler_lastchecktime(self):
        """
        Return the time of the last update of the scheduler state by the daemon,
        or None if it was never set.
        
        :return: a datetime object.
        """
        return self.get_attr('scheduler_lastchecktime', None)


    def _set_last_jobinfo(self,last_jobinfo):
        import pickle
        
        self.set_attr('last_jobinfo', pickle.dumps(last_jobinfo))

    def get_last_jobinfo(self):
        """
        Get the last information asked to the scheduler about the status of the job.
        
        :return: a JobInfo object (that closely resembles a dictionary) or None.
        """
        import pickle
        
        last_jobinfo_pickled = self.get_attr('last_jobinfo',None)
        if last_jobinfo_pickled is not None:
            return pickle.loads(last_jobinfo_pickled)
        else:
            return None
    
    @classmethod
    def list_calculations(cls,states=None, past_days=None, pks=[]):
        """
        This function return a string with a description of the AiiDA calculations.
        
        :param states: a list of string with states. If set, print only the 
            calculations in the states "states", otherwise shows all. Default = None.
        :param past_days: If specified, show only calculations that were created in
            the given number of past days.
        :param pks: if specified, must be a list of integers, and only calculations
            within that list are shown. Otherwise, all calculations are shown.
            If specified, sets state to None and ignores the 
            value of the ``past_days`` option.")
        
        :return: a string with description of calculations.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        
        if states:
            for state in states:
                if state not in calc_states:
                    return "Invalid state provided: {}.".format(state)
        
        from django.utils import timezone
        import datetime
        from django.db.models import Q
        from django.core.exceptions import ObjectDoesNotExist
        from aiida.djsite.db.models import DbNode
        from aiida.djsite.utils import get_automatic_user, get_last_daemon_run
        from aiida.common.utils import str_timedelta
        from aiida.djsite.settings.settings import djcelery_tasks
        from aiida.orm.node import from_type_to_pluginclassname
        
        now = timezone.now()
        
        if pks:
            q_object = Q(pk__in=pks)
        else:
            q_object = Q(user=get_automatic_user())
            if states:
#                q_object.add(~Q(dbattributes__key='state',
#                                dbattributes__tval=only_state,), Q.AND)
                q_object.add( Q(dbattributes__key='state',
                                dbattributes__tval__in=states,), Q.AND)
            if past_days:
                now = timezone.now()
                n_days_ago = now - datetime.timedelta(days=past_days)
                q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

        calc_list = cls.query(q_object).distinct().order_by('ctime')
        
        from aiida.djsite.db.models import DbAttribute
        scheduler_states = dict(DbAttribute.objects.filter(dbnode__in=calc_list,
                                                   key='scheduler_state').values_list(
            'dbnode__pk', 'tval'))
        states = dict(DbAttribute.objects.filter(dbnode__in=calc_list,
                                                   key='state').values_list(
            'dbnode__pk', 'tval'))
        scheduler_lastcheck = dict(DbAttribute.objects.filter(dbnode__in=calc_list,
                                                   key='scheduler_lastchecktime').values_list(
            'dbnode__pk', 'dval'))
        
        calc_list_data = calc_list.values('pk', 'dbcomputer__name', 'ctime', 'type')
        
        try:
            last_daemon_check = get_last_daemon_run(
                djcelery_tasks['calculationretrieve'])
        except ObjectDoesNotExist:
            last_check_string = ("# Last daemon check: (Unable to discover, "
                "no such task found)")
        except Exception as e:
            last_check_string = ("# Last daemon check: (Unable to discover, "
                "error: {})".format(type(e).__name__))
        else:
            if last_daemon_check is None:
                last_check_string = "# Last daemon check: (Never)"
            else:
                last_check_string = ("# Last daemon check (approximate): "
                    "{} ago ({})".format(
                    str_timedelta(now-last_daemon_check),
                    last_daemon_check.strftime("%H:%M:%S")))
        
        if not calc_list:
            return last_check_string
        else:
            fmt_string = '{:<10} {:<17} {:>12} {:<10} {:<22} {:<15} {:<15}'
            res_str_list = [last_check_string]
            res_str_list.append(fmt_string.format(
                    'Pk','State','Creation','Time',
                    'Scheduler state','Computer','Type'))
            for calcdata in calc_list_data:
                remote_state = "None"
                
                calc_state = states[calcdata['pk']]
                remote_computer = calcdata['dbcomputer__name']
                try:
                    sched_state = scheduler_states.get(calcdata['pk'], None)
                    if sched_state is None:
                        remote_state = "(unknown)"
                    else:
                        remote_state = '{}'.format(sched_state)
                        if calc_state == calc_states.WITHSCHEDULER:
                            last_check = scheduler_lastcheck.get(calcdata['pk'], None)
                            if last_check is not None:
                                when_string = " {} ago".format(
                                    str_timedelta(now-last_check, short=True,
                                          negative_to_zero = True))
                                verb_string = "was "
                            else:
                                when_string = ""
                                verb_string = ""
                            remote_state = "{}{}{}".format(verb_string,
                                                       sched_state, when_string)
                except ValueError:
                    raise
                
                res_str_list.append(fmt_string.format( calcdata['pk'],
                    states[calcdata['pk']],
                    calcdata['ctime'].isoformat().split('T')[0],
                    calcdata['ctime'].isoformat().split('T')[1].split('.')[0],
                    remote_state,
                    remote_computer,
                    str(from_type_to_pluginclassname(
                        calcdata['type']).split('.')[-1]),
                    ))
            return "\n".join(res_str_list)

    @classmethod
    def get_all_with_state(cls, state, computer=None, user=None, 
                           only_computer_user_pairs = False):
        """
        Filter all calculations with a given state.
        
        Issue a warning if the state is not in the list of valid states.
        
        :param string state: The state to be used to filter (should be a string among 
                those defined in aiida.common.datastructures.calc_states)
        :param computer: a Django DbComputer entry, or a Computer object, of a
                computer in the DbComputer table.
                A string for the hostname is also valid.
        :param user: a Django entry (or its pk) of a user in the User table;
                if present, the results are restricted to calculations of that
                specific user
        :param bool only_computer_user_pairs: if False (default) return a queryset 
                where each element is a suitable instance of Node (it should
                be an instance of Calculation, if everything goes right!)
                If True, return only a list of tuples, where each tuple is
                in the format
                ('dbcomputer__id', 'user__id')
                [where the IDs are the IDs of the respective tables]

        :return: a list of calculation objects matching the filters.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        from aiida.orm import Computer

        if state not in calc_states:
            cls.logger.warning("querying for calculation state='{}', but it "
                "is not a valid calculation state".format(state))

        kwargs = {}
        if computer is not None:
            # I convert it from various type of inputs
            # (string, DbComputer, Computer)
            # to a DbComputer type
            kwargs['dbcomputer'] = Computer.get(computer).dbcomputer
        if user is not None:
            kwargs['user'] = user
        
        queryresults = cls.query(
            dbattributes__key='state',
            dbattributes__tval=state,
            **kwargs)

        if only_computer_user_pairs:
            return queryresults.values_list(
                'dbcomputer__id', 'user__id')
        else:
            return queryresults

    def use_code(self, code):
        """
        Set the code for this calculation.
        
        :param code: the code object to be used by the calculation.
        """
        from aiida.orm import Code

        if not isinstance(code, Code):
            raise ValueError("The code must be an instance of the Code class")

        self._replace_link_from(code, self.get_linkname_code())

    def get_code(self):
        """
        Return the code for this calculation, or None if the code
        was not set.
        """
        from aiida.orm import Code
        
        return dict(self.get_inputs(type=Code, also_labels=True)).get(
            self.get_linkname_code(), None)
        
    def get_linkname_code(self):
        """
        The name of the link used for the code.
        
        :return: a string
        """
        return "code"
        
    def _prepare_for_submission(self,tempfolder,inputdict=None):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.
            inputdict: None, if it has to be calculated automatically
                from the input nodes using the
                self.get_inputdata_dict() method.
                Otherwise, a dictionary where
                each key is an input link name and each value an AiiDA
                node, as it would be returned by the
                self.get_inputdata_dict() method.
                The advantage of having this as a key is that this
                allows to test for submission even before creating 
                the nodes in the DB.

        TODO: document what it has to return (probably a CalcInfo object)
              and what is the behavior on the tempfolder
        """
        raise NotImplementedError

    def _get_authinfo(self):
        import aiida.execmanager
        from aiida.common.exceptions import NotExistent
        
        computer = self.get_computer()
        if computer is None:
            raise  NotExistent("No computer has been set for this calculation")
        
        return aiida.execmanager.get_authinfo(computer=computer,
                                              aiidauser=self.dbnode.user)
    
    def _get_transport(self):
        """
        Return the transport for this calculation.
        """
        return self._get_authinfo().get_transport()

    def submit(self):
        """
        Puts the calculation in the TOSUBMIT status.
        
        Actual submission is performed by the daemon.
        """ 
        from aiida.common.exceptions import InvalidOperation
        
        if self.get_state() != calc_states.NEW:
            raise InvalidOperation("Cannot submit a calculation not in {} state"
                                   .format(calc_states.NEW) )

        self._set_state(calc_states.TOSUBMIT)

    def set_parser_name(self, parser):
        """
        Set a string for the output parser
        Can be None if no output plugin is available or needed.
        
        :param parser: a string identifying the module of the parser. 
              Such module must be located within the folder 'aiida/parsers/plugins'
        """                
        self.set_attr('parser', parser)

    def get_parser_name(self):
        """
        Return a string locating the module that contains 
        the output parser of this calculation, that will be searched
        in the 'aiida/parsers/plugins' directory. None if no parser is needed/set.
        
        :return: a string.
        """
        from aiida.parsers import ParserFactory
                
        return self.get_attr('parser', None)

    def get_parserclass(self):
        """
        Return the output parser object for this calculation, or None
        if no parser is set.
        
        :return: a Parser class.
        :raise: MissingPluginError from ParserFactory no plugin is found.
        """
        from aiida.parsers import ParserFactory
        
        parser_name = self.get_parser_name()
        
        if parser_name is not None:
            return ParserFactory(parser_name)
        else:
            return None

    def set_linkname_retrieved(self,linkname):
        """
        Set the linkname of the retrieved data folder object.
        
        :param linkname: a string.
        """
        self.set_attr('linkname_retrieved',linkname)

    def get_linkname_retrieved(self):
        """
        Get the linkname of the retrieved data folder object.
        
        :return: a string 
        """
        return self.get_attr('linkname_retrieved')
        
    def get_retrieved(self):
        """
        Return the retrieved data folder, if present.

        :return: the retrieved data folder object.
        
        :note: it is assumed that only one retrieved folder exists.
        """
        from aiida.orm import DataFactory
        
        return DataFactory(self.get_linkname_retrieved)
        
    def kill(self):
        """
        Kill a calculation on the cluster.
        
        Can only be called if the calculation is in status WITHSCHEDULER.
        
        The command tries to run the kill command as provided by the scheduler,
        and raises an exception is something goes wrong. 
        No changes of calculation status are done (they will be done later by
        the calculation manager).
        """
        #TODO: Check if we want to add a status "KILLED" or something similar.
        
        from aiida.common.exceptions import InvalidOperation, RemoteOperationError
        
        if self.get_state() == calc_states.NEW:
            self._set_state(calc_states.FAILED)
            return
        
        if self.get_state() != calc_states.WITHSCHEDULER:
            raise InvalidOperation("Cannot kill a calculation not in {} state"
                                   .format(calc_states.WITHSCHEDULER) )
        
        # I get the scheduler plugin class and initialize it with the correct
        # transport
        computer = self.get_computer()
        t = self._get_transport()
        s = computer.get_scheduler()
        s.set_transport(t)
        
        # And I call the proper kill method for the job ID of this calculation
        with t:
            retval = s.kill(self.get_job_id())
        
        # Raise error is something went wrong
        if not retval:
            raise RemoteOperationError("An error occurred while trying to kill "
                                       "calculation {} (jobid {}), see log "
                                       "(maybe the calculation already finished?)"
                                       .format(self.pk, self.get_job_id()))
        
    def presubmit(self, folder, code, inputdict=None):
        import os
        import StringIO
        import json

        from aiida.common.exceptions import (NotExistent,
            PluginInternalError, ValidationError)
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.orm import Computer

        computer = self.get_computer()

        calcinfo = self._prepare_for_submission(folder, inputdict)
        s = computer.get_scheduler()

        if code.is_local():
            if code.get_local_executable() in folder.get_content_list():
                raise PluginInternalError(
                      "The plugin created a file {} that is also "
                      "the executable name!".format(
                      code.get_local_executable()))

        # TODO: support -V option of schedulers!
        
        self._set_retrieve_list(calcinfo.retrieve_list if
                                calcinfo.retrieve_list is not None else [])

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        ## TODO: in the future, allow to customize the following variables
        job_tmpl.submit_as_hold = False
        job_tmpl.rerunnable = False
        job_tmpl.job_environment = {}
        #'email', 'email_on_started', 'email_on_terminated',
        job_tmpl.job_name = 'aiida-{}'.format(self.pk) 
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
             **self.get_resources())

        subst_dict = {'tot_num_cpus': 
                      job_tmpl.job_resource.get_tot_num_cpus()}
        
        for k,v in job_tmpl.job_resource.iteritems():
            subst_dict[k] = v
        mpi_args = [arg.format(**subst_dict) for arg in
                    computer.get_mpirun_command()]
        if self.get_withmpi():
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
        
        job_tmpl.import_sys_environment = self.get_import_sys_environment()
        
        queue_name = self.get_queue_name()
        if queue_name is not None:
            job_tmpl.queue_name = queue_name
        priority = self.get_priority()
        if priority is not None:
            job_tmpl.priority = priority
        max_memory_kb = self.get_max_memory_kb()
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb
        max_wallclock_seconds = self.get_max_wallclock_seconds()
        if max_wallclock_seconds is not None:
            job_tmpl.max_wallclock_seconds = max_wallclock_seconds
        max_memory_kb = self.get_max_memory_kb()
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


        if calcinfo.local_copy_list is None:
            calcinfo.local_copy_list = []
        
        if calcinfo.remote_copy_list is None:
            calcinfo.remote_copy_list = []

        # Some validation
        this_pk = self.pk if self.pk is not None else "[UNSTORED]"
        local_copy_list = calcinfo.local_copy_list
        try:
            validate_list_of_string_tuples(local_copy_list,
                                           tuple_length = 2)
        except ValidationError as e:
            raise PluginInternalError("[presubmission of calc {}] "
                "local_copy_list format problem: {}".format(
                this_pk, e.message))

        remote_copy_list = calcinfo.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list,
                                           tuple_length = 3)
        except ValidationError as e:
            raise PluginInternalError("[presubmission of calc {}] "
                "remote_copy_list format problem: {}".format(
                this_pk, e.message))

        for (remote_computer_uuid, remote_abs_path, 
             dest_rel_path) in remote_copy_list:
            try:
                remote_computer = Computer(uuid=remote_computer_uuid)
            except NotExistent:
                raise PluginInternalError("[presubmission of calc {}] "
                    "The remote copy requires a computer with UUID={}"
                    "but no such computer was found in the "
                    "database".format(this_pk, remote_computer_uuid))                
            if os.path.isabs(dest_rel_path):
                raise PluginInternalError("[presubmission of calc {}] "
                    "The destination path of the remote copy "
                    "is absolute! ({})".format(this_pk, dest_rel_path))

        return calcinfo, script_filename


    @property
    def res(self):
        """
        To be used to get direct access to the parsed parameters.
        
        :return: an instance of the CalculationResultManager.
        
        :note: a practical example on how it is meant to be used: let's say that there is a key 'energy' 
          in the dictionary of the parsed results which contains a list of floats.
          The command `calc.res.energy` will return such a list.
        """
        return CalculationResultManager(self)

    def submit_test(self, folder, code, inputdict, subfolder_name = None):
        import os
        from aiida.transport.plugins.local import LocalTransport
        import datetime
        import tempfile
        from aiida.orm import Computer
        
        # In case it is not created yet
        folder.create()
        
        if subfolder_name is None:
            subfolder_basename = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-')
        else:
            subfolder_basename = subfolder_name
            
        # Find a new subfolder.
        subfolder_path = tempfile.mkdtemp(prefix = subfolder_basename, dir=folder.abspath)
        subfolder = folder.get_subfolder(
            os.path.relpath(subfolder_path,folder.abspath),
            reset_limit=True)
        
        # I use the local transport where possible, to be as similar
        # as possible to a real submission
        t = LocalTransport()
        with t:
            t.chdir(subfolder.abspath)
        
            calcinfo, script_filename = self.presubmit(
                subfolder, code, inputdict)
        
            if code.is_local():
                # Note: this will possibly overwrite files
                for f in code.get_path_list():
                    t.put(code.get_abs_path(f), f)
                t.chmod(code.get_local_executable(), 0755) # rwxr-xr-x

            local_copy_list = calcinfo.local_copy_list
            remote_copy_list = calcinfo.remote_copy_list

            for src_abs_path, dest_rel_path in local_copy_list:
                t.put(src_abs_path, dest_rel_path)
                
            for (remote_computer_uuid, remote_abs_path, 
                  dest_rel_path) in remote_copy_list:
                remote_computer = Computer(uuid=remote_computer_uuid)
                localpath = os.path.join(
                    subfolder.abspath, dest_rel_path)
                # If it ends with a separator, it is a folder
                if localpath.endswith(os.path.sep):
                    localpath = os.path.join(localpath, 'PLACEHOLDER')
                dirpart = os.path.split(localpath)[0]
                if not(os.path.isdir(dirpart)):
                    os.makedirs(dirpart)
                with open(localpath,'w') as f:
                    f.write("PLACEHOLDER FOR REMOTELY COPIED "
                            "FILE FROM {} ({}):{}".format(remote_computer_uuid,
                                                    remote_computer.name,
                                                    remote_abs_path))

        return subfolder, script_filename

class CalculationResultManager(object):
    """
    An object used internally to interface the calculation object with the Parser 
    and consequentially with the ParameterData object result. 
    It shouldn't be used explicitely by a user.
    """
    def __init__(self, calc):
        """
        
        :param calc: the calculation object.
        """
        # Possibly add checks here
        self._calc = calc
        ParserClass = calc.get_parserclass()
        self._parser = ParserClass(calc)

    def __dir__(self):
        """
        Allow to list all valid attributes
        """
        from aiida.common.exceptions import UniquenessError

        try:
            calc_attributes = self._parser.get_result_keys()
        except UniquenessError:
            calc_attributes = []
        
        return sorted(set(list(dir(type(self))) + list(calc_attributes)))
            
    def __iter__(self):
        from aiida.common.exceptions import UniquenessError

        try:
            calc_attributes = self._parser.get_result_keys()
        except UniquenessError:
            calc_attributes = []
        
        for k in calc_attributes:
            yield k
    
    def __getattr__(self,name):
        """
        interface to get to the parser results as an attribute.
        
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._parser.get_result(name)
        except AttributeError:
            raise AttributeError("Parser '{}' did not provide a result '{}'"
                                 .format(self._parser.__class__.__name__, name))

    def __getitem__(self,name):
        """
        interface to get to the parser results as a dictionary.
        
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._parser.get_result(name)
        except AttributeError:
            raise KeyError("Parser '{}' did not provide a result '{}'"
                           .format(self._parser.__class__.__name__, name))

