from aiida.orm import Node
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import ModificationNotAllowed

#TODO: set the following as properties of the Calculation
#        'email',
#        'email_on_started',
#        'email_on_terminated',
#        'rerunnable',
#        'resourceLimits',

_input_subfolder = 'raw_input'

class Calculation(Node):
    _updatable_attributes = ('state', 'job_id', 'scheduler_state',
                             'last_jobinfo', 'remote_workdir', 'retrieve_list')
    
    # By default, no output parser
    _default_parser = None
    # Set default for the link to the retrieved folder (after calc is done)
    _linkname_retrieved = 'retrieved' 
    
    def __init__(self,*args,**kwargs):
        """
        Possible arguments:
        computer, resources
        """
        super(Calculation,self).__init__(*args, **kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            # if I am loading an existing calc: stop here
            return

        # For new calculations
        self._set_state(calc_states.NEW)
        self.label = "Calculation {}".format(self.uuid)

        computer = kwargs.pop('computer', None)
        if computer is not None:
            self.set_computer(computer)

        # Default value: True
        # If True, adds the machine-dependent mpirun command in front of the
        # executable name.
        withmpi = kwargs.pop('withmpi', True)
        self.set_withmpi(withmpi)

        resources = kwargs.pop('resources',None)
        if resources is not None:
            self.set_resources(**resources)

        parser = kwargs.pop('parser', self._default_parser)
        self.set_parser(parser)
        
        # hard code the output folder to be a single one
        self.set_linkname_retrieved(self._linkname_retrieved)

        if kwargs:
            raise ValueError("Invalid parameters found in the __init__: "
                             "{}".format(kwargs.keys()))

    def store(self):
        
        super(Calculation, self).store()
        
        return self
            
    def validate(self):
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
            _ = s.create_job_resource(**self.get_jobresource_params())
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

        Args:
            folder_path: the path to the folder from which the content
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
        from aiida.common.exceptions import NotExistent

        return_folder = self.current_folder.get_subfolder(_input_subfolder)
        if return_folder.exists():
            return return_folder
        else:
            raise NotExistent("raw_input_folder not created yet")

    def set_queue_name(self,val):
        self.set_attr('queue_name',unicode(val))

    def set_import_sys_environment(self,val):
        self.set_attr('import_sys_environment',bool(val))

    def get_import_sys_environment(self):
        return self.get_attr('import_sys_environment',True)
                
    def set_priority(self,val):
        self.set_attr('priority',unicode(val))
    
    def set_max_memory_kb(self,val):
        self.set_attr('max_memory_kb',int(val))

    def set_max_wallclock_seconds(self,val):    
        self.set_attr('max_wallclock_seconds',int(val))

    def set_resources(self, **kwargs):
        self.set_attr('jobresource_params', kwargs)
    
    def set_withmpi(self,val):        
        self.set_attr('withmpi',val)

    def get_withmpi(self):        
        return self.get_attr('withmpi',True)
    
    def get_jobresource_params(self):
        return self.get_attr('jobresource_params', {})

    def get_queue_name(self):
        return self.get_attr('queue_name', None)

    def get_priority(self):
        return self.get_attr('priority', None)
    
    def get_max_memory_kb(self):
        return self.get_attr('max_memory_kb', None)

    def get_max_wallclock_seconds(self):	
        return self.get_attr('max_wallclock_seconds', None)
        
    def add_link_from(self,src,label=None):
        '''
        Add a link with a code as destination.
        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.
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

        return super(Calculation,self).add_link_from(src, label)

    def set_computer(self,computer):
        """
        TODO: probably this method should be in the base class, and
        check for the type
        """
        from aiida.djsite.db.models import DbComputer

        if self._to_be_stored:
            self.dbnode.computer = DbComputer.get_dbcomputer(computer)
        else:
            self.logger.error("Trying to change the computer of an already "
                              "saved node: {}".format(self.uuid))
            raise ModificationNotAllowed(
                "Node with uuid={} was already stored".format(self.uuid))

    def get_computer(self):
        from aiida.orm import Computer
        if self.dbnode.computer is None:
            return None
        else:
            return Computer(dbcomputer=self.dbnode.computer)

    def _set_state(self, state):
        if state not in calc_states:
            raise ValueError(
                "'{}' is not a valid calculation status".format(state))
        self.set_attr('state', state)

    def get_state(self):
        return self.get_attr('state', None)

    def is_new(self):
        return self.get_state() in [self.NEW]

    def is_running(self):
        return self.get_state() in [
            self.TOSUBMIT, self.SUBMITTING, self.WITHSCHEDULER,
            self.COMPUTED, self.RETRIEVING, self.PARSING]

    def has_finished_ok(self):
        return self.get_state() in [self.FINISHED]

    def has_failed(self):
        return self.get_state() in [self.UNDETERMINED, self.SUBMISSIONFAILED,
            self.RETRIEVALFAILED, self.PARSINGFAILED, self.FAILED]

    def _set_remote_workdir(self, remote_workdir):
        if self.get_state() != calc_states.SUBMITTING:   
            raise ModificationNotAllowed(
                "Cannot set the remote workdir if you are not "
			    "submitting the calculation (current state is "
				"{})".format(self.get_state()))
        self.set_attr('remote_workdir', remote_workdir)

    def get_remote_workdir(self):
        return self.get_attr('remote_workdir', None)

    def _set_retrieve_list(self, retrieve_list):
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed(
                "Cannot set the retrieve_list if you are not "
				"submitting the calculation (current state is "
		        "{})".format(self.get_state()))

        if (not(isinstance(retrieve_list,(tuple,list))) or
	           not(all(isinstance(i,basestring) for i in retrieve_list))):
            raise ValueError("You have to pass a list (or tuple) of strings "
                             "as retrieve_list")
        self.set_attr('retrieve_list', retrieve_list)

    def get_retrieve_list(self):
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
        return self.get_attr('job_id', None)
        
    def _set_scheduler_state(self,state):
        # I don't do any test here on the possible valid values,
        # I just convert it to a string
        self.set_attr('scheduler_state', unicode(state))
                
    def get_scheduler_state(self):
        return self.get_attr('scheduler_state', None)

    def _set_last_jobinfo(self,last_jobinfo):
        import pickle
        
        self.set_attr('last_jobinfo', pickle.dumps(last_jobinfo))

    def get_last_jobinfo(self):
        import pickle
        
        last_jobinfo_pickled = self.get_attr('last_jobinfo',None)
        if last_jobinfo_pickled is not None:
            return pickle.loads(last_jobinfo_pickled)
        else:
            return None
    

    @classmethod
    def get_all_with_state(cls, state, computer=None, user=None, 
                           only_computer_user_pairs = False):
        """
        Filter all calculations with a given state.

        Issue a warning if the state is not in the list of valid states.

        Args:
            state: The state to be used to filter (should be a string among 
                those defined in aiida.common.datastructures.calc_states)
            computer: a Django DbComputer entry, or a Computer object, of a
                computer in the DbComputer table.
                A string for the hostname is also valid.
            user: a Django entry (or its pk) of a user in the User table;
                if present, the results are restricted to calculations of that
                specific user
            only_computer_user_pairs: if False (default) return a queryset 
                where each element is a suitable instance of Node (it should
                be an instance of Calculation, if everything goes right!)
                If True, return only a list of tuples, where each tuple is
                in the format
                ('computer__id', 'user__id')
                [where the IDs are the IDs of the respective tables]
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from attributes__tval to the correct field.
        from aiida.orm import Computer

        if state not in calc_states:
            cls.logger.warning("querying for calculation state='{}', but it "
                "is not a valid calculation state".format(state))

        kwargs = {}
        if computer is not None:
            # I convert it from various type of inputs
            # (string, DbComputer, Computer)
            # to a Computer type
            kwargs['computer'] = Computer.get(computer)
        if user is not None:
            kwargs['user'] = user
        
        queryresults = cls.query(
            attributes__key='_state',
            attributes__tval=state,
            **kwargs)

        if only_computer_user_pairs:
            return queryresults.values_list(
                'computer__id', 'user__id')
        else:
            return queryresults

    def use_code(self, code):
        """
        Set the code for this calculation
        """
        from aiida.orm import Code

        if not isinstance(code, Code):
            raise ValueError("The code must be an instance of the Code class")

        self.replace_link_from(code, self.get_linkname_code())
        
    def get_linkname_code(self):
        """
        The name of the link used for the code
        """
        return "code"
        
    def _prepare_for_submission(self,tempfolder):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.

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
        Return the transport for this calculation
        """
        return self._get_authinfo().get_transport()

    def submit(self):
        """
        Submit the calculation.
        """ 
        from aiida.execmanager import submit_calc
        
        submit_calc(self)

    def set_parser(self, parser):
        """
        Set a string for the output parser
        Can be None if no output plugin is available or needed
        """                
        self.set_attr('parser', parser)

    def get_parser_name(self):
        """
        Return a string for the output parser of this calculation, or None
        if no parser is needed.
        """
        from aiida.parsers import ParserFactory
                
        return self.get_attr('parser')

    def get_parserclass(self):
        """
        Return the output parser object for this calculation, or None
        if no parser is set.
        
        ParserFactory raises MissingPluginError if the plugin is not found.
        """
        from aiida.parsers import ParserFactory
        
        parser_name = self.get_parser_name()
        
        if parser_name is not None:
            return ParserFactory(parser_name)
        else:
            return None

    def set_linkname_retrieved(self,linkname):
        """
        set the linkname of the retrieved data folder object
        """
        self.set_attr('linkname_retrieved',linkname)

    def get_linkname_retrieved(self):
        """
        get the linkname of the retrieved data folder object
        """
        return self.get_attr('linkname_retrieved')
        
    def get_retrieved(self):
        """
        return the retrieved data folder, if present.
        Note: we are assuming only one retrieved folder exists
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
        
        ..todo:: Check if we want to add a status "KILLED" or something similar.
        """
        from aiida.common.exceptions import InvalidOperation, RemoteOperationError
        
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
        

    @property
    def res(self):
        """
        Returns an instance of the CalculationResultManager.
        It is used to access the parsed parameters directly from the calculation
        """
        return CalculationResultManager(self)

class CalculationResultManager(object):
    def __init__(self, calc):
        # Possibly add checks here
        self._calc = calc
        ParserClass = calc.get_parserclass()
        self._parser = ParserClass(calc)
        
    def __getattr__(self,name):
        """
        interface to get to the parser results.
        """
        try:
            return self._parser.get_results(name)
        except AttributeError:
            raise AttributeError("Parser '{}' didn't provide a result '{}'"
                                 .format(self._parser.__class__, name))

