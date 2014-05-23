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
    
    # Files in which the scheduler output and error will be stored.
    # If they are identical, outputs will be joined.
    SCHED_OUTPUT_FILE = '_scheduler-stdout.txt'
    SCHED_ERROR_FILE = '_scheduler-stderr.txt'
    
    # Default values to be set for new nodes
    @classproperty
    def _set_defaults(cls):
        return {"parser_name": cls._default_parser,
                "linkname_retrieved": cls._linkname_retrieved,
          }
    
    # Nodes that can be added as input using the use_* methods
    @classproperty
    def _use_methods(cls):
        """
        Return the list of valid input nodes that can be set using the
        use_* method. 
        
        For each key KEY of the return dictionary, the 'use_KEY' method is
        exposed.
        Each value must be a dictionary, defining the following keys:
        * valid_types: a class, or tuple of classes, that will be used to
          validate the parameter using the isinstance() method
        * additional_parameter: None, if no additional parameters can be passed
          to the use_KEY method beside the node, or the name of the additional
          parameter (a string)
        * linkname: the name of the link to create (a string if
          additional_parameter is None, or a callable if additional_parameter is
          a string. The value of the additional parameter will be passed to the
          callable, and it should return a string.
        * docstring: a docstring for the function
        
        .. note:: in subclasses, always extend the parent class, do not
          substitute it!
        """
        from aiida.orm import Code
        
        return {
            "code": {
               'valid_types': Code,
               'additional_parameter': None,
               'linkname': 'code',
               'docstring': "Choose the code to use",
               },
            }

    def __dir__(self):
        """
        Allow to list all valid attributes, adding also the use_* methods
        """
        return sorted(dir(type(self)) + list(['use_{}'.format(k)
                                 for k in self._use_methods.iterkeys()]))

    def __getattr__(self,name):
        """
        Expand the methods with the use_* calls. Note that this method only 
        gets called if 'name' is not already defined as a method. Returning
        None will then automatically raise the standard AttributeError 
        exception.
        """
        class UseMethod(object):
            """
            Generic class for the use_* methods. To know which use_* methods
            exist, use the ``dir()`` function. To get help on a specific method,
            for instance use_code, use::
              ``print use_code.__doc__``
            """
            
            def __init__(self, node, actual_name, data):
                from aiida.common.exceptions import InternalError
                
                self.node = node
                self.actual_name = actual_name
                self.data = data
                try:
                    self.__doc__ = data['docstring']
                except KeyError:
                    # Forgot to define the docstring! Use the default one
                    pass
                            
            def __call__(self, parent_node, *args, **kwargs):
                import collections
                
                # Not really needed, will be checked in get_linkname
                # But I do anyway in order to raise an exception as soon as
                # possible, with the most intuitive caller function name
                additional_parameter = self.node._parse_single_arg(
                    function_name='use_{}'.format(self.actual_name),
                    additional_parameter=self.data['additional_parameter'],
                    args=args, kwargs=kwargs)
                 
                # Type check   
                if isinstance(self.data['valid_types'], collections.Iterable):
                    valid_types_string = ",".join([_.__name__ for _ in 
                                                   self.data['valid_types']])
                else:
                    valid_types_string = self.data['valid_types'].__name__
                if not isinstance(parent_node, self.data['valid_types']):
                    raise TypeError("The given node is not of the valid type "
                                    "for use_{}. Valid types are: {}, while "
                                    "you provided {}".format(
                                    self.actual_name, valid_types_string,
                                    parent_node.__class__.__name__))
                
                # Get actual link name
                actual_linkname = self.node.get_linkname(actual_name, *args,
                                                         **kwargs)
                # Checks that such an argument exists have already been
                # made inside actual_linkname
                    
                # Here I do the real job
                self.node._replace_link_from(parent_node, actual_linkname)
                
        prefix = 'use_'
        valid_use_methods = list(['{}{}'.format(prefix, k)
                                 for k in self._use_methods.iterkeys()])
        
        if name in valid_use_methods:
            actual_name = name[len(prefix):]
            return UseMethod(node=self, actual_name=actual_name,
                             data=self._use_methods[actual_name])
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                self.__class__.__name__, name))
    
    def store(self, *args, **kwargs):
        """
        Override the store() method to store also the calculation in the NEW
        state as soon as this is stored for the first time.
        """
        super(Calculation, self).store(*args, **kwargs)
        
        # I get here if the calculation was successfully stored.
        self._set_state(calc_states.NEW)
        
        # Important to return self to allow the one-liner
        # c = Calculation().store()
        return self
        
       
    @classmethod 
    def _parse_single_arg(cls, function_name, additional_parameter,
                         args, kwargs):
        """
        Verifies that a single additional argument has been given (or no
        additional argument, if additional_parameter is None). Also
        verifies its name.
        
        :param function_name: the name of the caller function, used for
            the output messages
        :param additional_parameter: None if no additional parameters
            should be passed, or a string with the name of the parameter
            if one additional parameter should be passed.
        
        :return: None, if additional_parameter is None, or the value of 
            the additional parameter
        :raise TypeError: on wrong number of inputs
        """
        # Here all the logic to check if the parameters are correct.
        if additional_parameter is not None:
            if len(args) == 1:                        
                if kwargs:
                    raise TypeError("{}() received too many args".format(
                        function_name))
                additional_parameter_data = args[0]
            elif len(args) == 0:
                kwargs_copy = kwargs.copy()
                try:
                    additional_parameter_data = kwargs_copy.pop(
                        additional_parameter)
                except KeyError:
                    if kwargs_copy:
                        raise TypeError("{}() got an unexpected keyword "
                            "argument '{}'".format(
                            function_name, kwargs_copy.keys()[0]))
                    else:
                        raise TypeError("{}() requires more "
                            "arguments".format(function_name))
                if kwargs_copy:
                    raise TypeError("{}() got an unexpected keyword "
                        "argument '{}'".format(
                        function_name, kwargs_copy.keys()[0]))  
            else:
                raise TypeError("{}() received too many args".format(
                    function_name))
            return additional_parameter_data
        else:
            if kwargs:
                raise TypeError("{}() got an unexpected keyword "
                                "argument '{}'".format(
                                    function_name, kwargs.keys()[0]))
            if len(args) != 0:
                raise TypeError("{}() received too many args".format(
                    function_name))
                
            return None
   
    def get_linkname(self, link, *args, **kwargs):
        """
        Return the linkname used for a given input link

        Pass as parameter "NAME" if you would call the use_NAME method.
        If the use_NAME method requires a further parameter, pass that
        parameter as the second parameter.
        """
        from aiida.common.exceptions import InternalError

        try:
            data = self._use_methods[link]
        except KeyError:
            raise ValueError("No '{}' link is defined for this "
                "calculation".format(link))

        # Raises if the wrong # of parameters is passed
        additional_parameter = self._parse_single_arg(
            function_name='get_linkname',
            additional_parameter=data['additional_parameter'],
            args=args, kwargs=kwargs)
                      
        if data['additional_parameter'] is not None:
            # Call the callable to get the proper linkname
            actual_linkname = data['linkname'](additional_parameter)
        else:
            actual_linkname = data['linkname']
        
        return actual_linkname
        
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
            _ = s.create_job_resource(**self.get_resources(full=True))
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

    def set_environment_variables(self, env_vars_dict):
        """
        Set a dictionary of custom environment variables for this calculation.
        
        Both keys and values must be strings.
        """       
        if not isinstance(env_vars_dict, dict):
            raise ValueError("You have to pass a "
                "dictionary to set_environment_variables")
             
        for k, v in env_vars_dict.iteritems():
            if not isinstance(k, basestring) or not isinstance(v, basestring):
                raise ValueError("Both the keys and the values of the "
                    "dictionary passed to set_environment_variables must be "
                    "strings.")
        
        return self.set_attr('custom_environment_variables',env_vars_dict)
    
    def get_environment_variables(self):
        """
        Return a dictionary of the environment variables that we want to set
        for this calculation. 
        
        Return an empty dictionary if no special environment variables have
        to be set for this calculation.
        """
        return self.get_attr('custom_environment_variables',{})
                
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
    
    def get_resources(self, full=False):
        """
        Returns the dictionary of the job resources set.
        
        :param full: if True, also add the default values, e.g.
            ``default_mpiprocs_per_machine``
        
        :return: a dictionary
        """
        resources_dict = self.get_attr('jobresource_params', {})
    
        if full:
            computer = self.get_computer()
            def_cpus_machine = computer.get_default_mpiprocs_per_machine()
            if def_cpus_machine is not None:
                resources_dict['default_mpiprocs_per_machine'] = def_cpus_machine
        
        return resources_dict

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

    def get_prepend_text(self):
        """
        Set the calculation-specific prepend text
        """
        return self.get_attr("prepend_text", "")

    def set_prepend_text(self,val):
        """
        Set the calculation-specific prepend text
        """
        self.set_attr("prepend_text", unicode(val))

    def get_append_text(self):
        """
        Set the calculation-specific append text
        """
        return self.get_attr("append_text", "")

    def set_custom_scheduler_commands(self, val):
        """
        Set a (possibly multiline) string with the commands that the user
        wants to manually set for the scheduler.
        
        The difference of this method with respect to the set_prepend_text
        is the position in the scheduler submission file where such text is
        inserted: with this method, the string is inserted before any 
        non-scheduler command.
        """
        self.set_attr("custom_scheduler_commands", unicode(val))

    def get_custom_scheduler_commands(self):
        """
        Return a (possibly multiline) string with the commands that the user
        wants to manually set for the scheduler.
        See also the documentation of the corresponding
        ``set_`` method. 

        :return: the custom scheduler command, or an empty string if no 
          custom command was defined.
        """
        return self.get_attr("custom_scheduler_commands", "")

    def get_extra_mpirun_params(self):
        """
        Return a list of strings, that are the extra params to pass to the
        mpirun (or equivalent) command after the one provided in 
        computer.mpirun_command.
        
        Return an empty list if no parameters have been defined.
        """
        return self.get_attr("extra_mpirun_params", [])

    def set_extra_mpirun_params(self, extra_params):
        """
        Set the extra params to pass to the
        mpirun (or equivalent) command after the one provided in 
        computer.mpirun_command.
        
        :param extra_params: must be a list of strings, one for each
            extra parameter
        """
        if extra_params is None:
            try:
                self.del_attr("extra_mpirun_params")
            except AttributeError:
                # it was not saved, yet
                pass
            return
        
        if not isinstance(extra_params, (list, tuple)):
            raise ValueError("You must pass a list of strings to "
                             "set_extra_mpirun_params")
        for param in extra_params:
            if not isinstance(param, basestring):
                raise ValueError("You must pass a list of strings to "
                                 "set_extra_mpirun_params")
        
        
        self.set_attr("extra_mpirun_params", list(extra_params))

    def set_append_text(self,val):
        """
        Set the calculation-specific append text
        """
        self.set_attr("append_text", unicode(val))
    
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
        Add a link with a code as destination. Only possible if the calculation
        is in state NEW.
        
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
                "Can add an input link to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(Calculation,self)._add_link_from(src, label)

    def _replace_link_from(self,src,label):
        '''
        Replace a link. Only possible if the calculation is in state NEW.
        
        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link. 
        '''
        
        from aiida.orm.data import Data
        from aiida.orm.code import Code
        
        if not isinstance(src,(Data, Code)):
            raise ValueError("Nodes entering in calculation can only be of "
                             "type data or code")
        
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can replace an input link to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(Calculation,self)._replace_link_from(src, label)

    def _remove_link_from(self,label):
        '''
        Remove a link. Only possible if the calculation is in state NEW.
        
        :param str label: Name of the link to remove. 
        '''        
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can remove an input link to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(Calculation,self)._remove_link_from(label)


    def _set_state(self, state):
        """
        Set the state of the calculation.
        
        Set it in the DbCalcState to have also the uniqueness check.
        Moreover (except for the IMPORTED state) also store in the 'state'
        attribute, useful to know it also after importing, and for faster
        querying.
        
        .. todo:: Add further checks to enforce that the states are set
           in order?
        
        :param state: a string with the state. This must be a valid string,
          from ``aiida.common.datastructures.calc_states``.
        :raise: UniquenessError if the given state was already set.
        """
        from django.db import transaction, IntegrityError

        from aiida.djsite.db.models import DbCalcState
        from aiida.common.exceptions import UniquenessError
        
        if self._to_be_stored:
            raise ModificationNotAllowed("Cannot set the calculation state "
                                         "before storing")
        
        if state not in calc_states:
            raise ValueError(
                "'{}' is not a valid calculation status".format(state))
        
        try:
            with transaction.commit_on_success():
                new_state = DbCalcState(dbnode=self.dbnode, state=state).save()
        except IntegrityError:
            raise UniquenessError("Calculation pk={} already transited through "
                                  "the state {}".format(self.pk, state))

        # For non-imported states, also set in the attribute (so that, if we
        # export, we can still see the original state the calculation had.
        if state != calc_states.IMPORTED:
            self.set_attr('state', state)

    def get_state(self, from_attribute=False):
        """
        Get the state of the calculation.
        
        .. note:: this method returns the UNDETERMINED state if no state
          is found in the DB.
        
        .. todo:: Understand if the state returned when no state entry is found
          in the DB is the best choice.
        
        .. todo:: Understand if it is ok to return the most recently modified
          state, or we should implement some state ordering logic.
        
        :param from_attribute: if set to True, read it from the attributes 
          (the attribute is also set with set_state, unless the state is set
          to IMPORTED; in this way we can also see the state before storing).
        
        :return: a string. If from_attribute is True and no attribute is found,
          return None. If from_attribute is False and no entry is found in the
          DB, return the "UNDETERMINED" state.
        """
        from aiida.djsite.db.models import DbCalcState
        
        if from_attribute:
            return self.get_attr('state', None)
        else:
            if self._to_be_stored:
                return calc_states.NEW
            else:
                this_calc_states = DbCalcState.objects.filter(
                    dbnode=self).order_by('-time').values_list('state', flat=True)
                if not this_calc_states:
                    return calc_states.UNDETERMINED
                most_recent_state = this_calc_states[0]
                return most_recent_state

    def get_state_string(self):
        """
        Return a string, that is correct also when the state is imported 
        (in this case, the string will be in the format IMPORTED/ORIGSTATE
        where ORIGSTATE is the original state from the node attributes).
        """
        state = self.get_state(from_attribute=False)
        if state == calc_states.IMPORTED:
            attribute_state = self.get_state(from_attribute=True)
            if attribute_state is None:
                attribute_state = "UNDETERMINED"
            return 'IMPORTED/{}'.format(attribute_state)
        else:
            return state


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
        
        self.set_attr('last_jobinfo', last_jobinfo.serialize())

    def get_last_jobinfo(self):
        """
        Get the last information asked to the scheduler about the status of the job.
        
        :return: a JobInfo object (that closely resembles a dictionary) or None.
        """
        import pickle
        from aiida.scheduler.datastructures import JobInfo
        
        last_jobinfo_serialized = self.get_attr('last_jobinfo',None)
        if last_jobinfo_serialized is not None:
            jobinfo = JobInfo()
            jobinfo.load_from_serialized(last_jobinfo_serialized)
            return jobinfo
        else:
            return None
    
    @classmethod
    def list_calculations(cls,states=None, past_days=None, group=None, 
                            all_users=False, pks=[]):
        """
        This function return a string with a description of the AiiDA calculations.

        .. todo:: does not support the query for the IMPORTED state (since it
          checks the state in the Attributes, not in the DbCalcState table).
          Decide which is the correct logi and implement the correct query.
        
        :param states: a list of string with states. If set, print only the 
            calculations in the states "states", otherwise shows all. Default = None.
        :param past_days: If specified, show only calculations that were created in
            the given number of past days.
        :param group: If specified, show only calculations belonging to a
            user-defined group with the given name.
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
        from aiida.djsite.db.models import DbNode
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.tasks import get_last_daemon_timestamp
        from aiida.common.utils import str_timedelta
        from aiida.orm.node import from_type_to_pluginclassname
        
        now = timezone.now()
        
        if pks:
            q_object = Q(pk__in=pks)
        else:
            q_object = Q()
            
            if not all_users:
                q_object.add(Q(user=get_automatic_user()), Q.AND)
                
            if states is not None:
#                q_object.add(~Q(dbattributes__key='state',
#                                dbattributes__tval=only_state,), Q.AND)
                q_object.add( Q(dbattributes__key='state',
                                dbattributes__tval__in=states,), Q.AND)
            if past_days is not None:
                now = timezone.now()
                n_days_ago = now - datetime.timedelta(days=past_days)
                q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

            if group is not None:
                q_object.add(Q(dbgroups__name=group, dbgroups__type=""), Q.AND)

        calc_list = cls.query(q_object).distinct().order_by('ctime')
        
        from aiida.djsite.db.models import DbAttribute
        scheduler_states = dict(DbAttribute.objects.filter(dbnode__in=calc_list,
                                                   key='scheduler_state').values_list(
            'dbnode__pk', 'tval'))
        
        states = {c.pk: c.get_state_string() for c in calc_list}
        
        scheduler_lastcheck = dict(DbAttribute.objects.filter(
            dbnode__in=calc_list,
            key='scheduler_lastchecktime').values_list('dbnode__pk', 'dval'))
        
        calc_list_data = calc_list.values('pk', 'dbcomputer__name', 'ctime', 'type')
        
        ## Get the last daemon check
        try:
            last_daemon_check = get_last_daemon_timestamp('updater', when='stop')
        except ValueError:
            last_check_string = ("# Last daemon state_updater check: "
                                 "(Error while retrieving the information)")
        else:
            if last_daemon_check is None:
                last_check_string = "# Last daemon state_updater check: (Never)"
            else:
                last_check_string = ("# Last daemon state_updater check: "
                    "{} ({})".format(
                    str_timedelta(now-last_daemon_check, negative_to_zero=True),
                    timezone.localtime(last_daemon_check).strftime("at %H:%M:%S on %Y-%m-%d")))
        
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
                                when_string = " {}".format(
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
                    timezone.localtime(calcdata['ctime']).isoformat().split('T')[0],
                    timezone.localtime(calcdata['ctime']).isoformat().split('T')[1].split('.')[0],
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
        :param user: a Django entry (or its pk) of a user in the DbUser table;
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

    def get_code(self):
        """
        Return the code for this calculation, or None if the code
        was not set.
        """
        from aiida.orm import Code
        
        return dict(self.get_inputs(type=Code, also_labels=True)).get(
            self._use_methods['code']['linkname'], None)
                
    def _prepare_for_submission(self,tempfolder,inputdict):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.
            inputdict: A dictionary where
                each key is an input link name and each value an AiiDA
                node, as it would be returned by the
                self.get_inputdata_dict() method (without the Code!).
                The advantage of having this explicitly passed is that this
                allows to choose outside which nodes to use, and whether to
                use also unstored nodes, e.g. in a test_submit phase.

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
        
        current_state = self.get_state()
        if current_state != calc_states.NEW:
            raise InvalidOperation("Cannot submit a calculation not in {} "
                                   "state (the current state is {})"
                                   .format(calc_states.NEW, current_state) )

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
        
    def get_retrieved_node(self):
        """
        Return the retrieved data folder, if present.

        :return: the retrieved data folder object, or None if no such output
            node is found.
        
        :raise MultipleObjectsError: if more than one output node is found.
        """
        from aiida.common.exceptions import MultipleObjectsError
        from aiida.orm.data.folder import FolderData
        
        outputs = self.get_outputs(also_labels = True)
        
        retrieved_node = None
        retrieved_linkname = self.get_linkname_retrieved()
        
        for label, node in outputs:
            if label == retrieved_linkname:
                if retrieved_node is None:
                    retrieved_node = node
                else:
                    raise MultipleObjectsError("More than one output node "
                        "with label '{}' for calc with pk={}".format(
                            retrieved_linkname, self.pk))
        
        if retrieved_node is None:
            return None
        
        if not isinstance(retrieved_node, FolderData):
            raise TypeError("The retrieved node of calc with pk={} is not of "
                            "type FolderData".format(self.pk))
        
        return retrieved_node
        
    def kill(self):
        """
        Kill a calculation on the cluster.
        
        Can only be called if the calculation is in status WITHSCHEDULER.
        
        The command tries to run the kill command as provided by the scheduler,
        and raises an exception is something goes wrong. 
        No changes of calculation status are done (they will be done later by
        the calculation manager).
        
        .. todo: if the status is TOSUBMIT, check with some lock that it is not
            actually being submitted at the same time in another thread.
        """
        #TODO: Check if we want to add a status "KILLED" or something similar.
        from aiida.djsite.utils import get_dblogger_extra
        from aiida.common.exceptions import InvalidOperation, RemoteOperationError
        
        logger_extra = get_dblogger_extra(self)    
        
        if (self.get_state() == calc_states.NEW or 
                self.get_state() == calc_states.TOSUBMIT):
            self.logger.warning("Calculation {} killed by the user "
                                "(it was in {} state)".format(
                                self.pk, self.get_state()), extra=logger_extra)
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
        else:
            self._set_state(calc_states.FAILED)
            self.logger.warning("Calculation {} killed by the user "
                                "(it was WITHSCHEDULER)".format(self.pk),
                                extra=logger_extra)
            
        
    def presubmit(self, folder, use_unstored_links=False):
        import os
        import StringIO
        import json

        from aiida.common.exceptions import (NotExistent,
            PluginInternalError, ValidationError)
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.orm import Computer

        computer = self.get_computer()

        code = self.get_code()
        if use_unstored_links:
            inputdict = self.get_inputdata_dict(only_in_db=False)
        else:
            inputdict = self.get_inputdata_dict(only_in_db=False)

        calcinfo = self._prepare_for_submission(folder, inputdict)
        s = computer.get_scheduler()

        if code.is_local():
            if code.get_local_executable() in folder.get_content_list():
                raise PluginInternalError(
                      "The plugin created a file {} that is also "
                      "the executable name!".format(
                      code.get_local_executable()))

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        ## TODO: in the future, allow to customize the following variables
        job_tmpl.submit_as_hold = False
        job_tmpl.rerunnable = False
        job_tmpl.job_environment = {}
        #'email', 'email_on_started', 'email_on_terminated',
        job_tmpl.job_name = 'aiida-{}'.format(self.pk) 
        job_tmpl.sched_output_path = self.SCHED_OUTPUT_FILE
        if self.SCHED_ERROR_FILE == self.SCHED_OUTPUT_FILE:
            job_tmpl.sched_join_files = True
        else:
            job_tmpl.sched_error_path = self.SCHED_ERROR_FILE
            job_tmpl.sched_join_files = False

        # Set retrieve path, add also scheduler STDOUT and STDERR
        retrieve_list = (calcinfo.retrieve_list
                         if calcinfo.retrieve_list is not None
                         else [])
        if (job_tmpl.sched_output_path is not None and 
            job_tmpl.sched_output_path not in retrieve_list):
            retrieve_list.append(job_tmpl.sched_output_path)
        if not job_tmpl.sched_join_files:
            if (job_tmpl.sched_error_path is not None and 
            job_tmpl.sched_error_path not in retrieve_list):
                retrieve_list.append(job_tmpl.sched_error_path)
        self._set_retrieve_list(retrieve_list)

        # the if is done so that if the method returns None, this is 
        # not added. This has two advantages:
        # - it does not add too many \n\n if most of the prepend_text are empty
        # - most importantly, skips the cases in which one of the methods 
        #   would return None, in which case the join method would raise
        #   an exception
        job_tmpl.prepend_text = "\n\n".join(_ for _ in 
            [computer.get_prepend_text(), 
             code.get_prepend_text(),
             calcinfo.prepend_text,
             self.get_prepend_text()] if _)
        
        job_tmpl.append_text = "\n\n".join(_ for _ in 
            [self.get_append_text(),
             calcinfo.append_text,
             code.get_append_text(),
             computer.get_prepend_text()] if _)

        # Set resources, also with get_default_mpiprocs_per_machine
        resources_dict = self.get_resources(full=True)
        job_tmpl.job_resource = s.create_job_resource(**resources_dict)

        subst_dict = {'tot_num_mpiprocs': 
                      job_tmpl.job_resource.get_tot_num_mpiprocs()}
        
        for k,v in job_tmpl.job_resource.iteritems():
            subst_dict[k] = v
        mpi_args = [arg.format(**subst_dict) for arg in
                    computer.get_mpirun_command()]
        extra_mpirun_params = self.get_extra_mpirun_params()
        if self.get_withmpi():
            job_tmpl.argv = (mpi_args + extra_mpirun_params + 
                [code.get_execname()] + 
                (calcinfo.cmdline_params if 
                    calcinfo.cmdline_params is not None else []))
        else:
            job_tmpl.argv = [code.get_execname()] + (
                calcinfo.cmdline_params if 
                    calcinfo.cmdline_params is not None else [])

        job_tmpl.stdin_name = calcinfo.stdin_name
        job_tmpl.stdout_name = calcinfo.stdout_name
        job_tmpl.stderr_name = calcinfo.stderr_name
        job_tmpl.join_files = calcinfo.join_files
        
        custom_sched_commands = self.get_custom_scheduler_commands()
        if custom_sched_commands:        
            job_tmpl.custom_scheduler_commands = custom_sched_commands
        
        job_tmpl.import_sys_environment = self.get_import_sys_environment()
        
        job_tmpl.job_environment = self.get_environment_variables()
        
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

    def submit_test(self, folder=None, subfolder_name = None):
        """
        Test submission, creating the files in a local folder.
        
        :note: this submit_test function does not require any node
            (neither the calculation nor the input links) to be stored yet.
        
        :param folder: A Folder object, within which each calculation files 
            are created; if not passed, a subfolder 'submit_test' of the current
            folder is used.
        :param subfolder_name: the name of the subfolder to use for this
            calculation (within Folder). If not passed, a unique string 
            starting with the date and time in the format ``yymmdd-HHMMSS-``
            is used.
        """
        import os
        from django.utils import timezone
        import tempfile

        from aiida.transport.plugins.local import LocalTransport
        from aiida.orm import Computer
        from aiida.common.folders import Folder
        
        if folder is None:
            folder = Folder(os.path.abspath('submit_test'))
        
        # In case it is not created yet
        folder.create()
        
        if subfolder_name is None:
            subfolder_basename = timezone.now().strftime('%Y%m%d-%H%M%S-')
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
                subfolder, use_unstored_links=True)
        
            code = self.get_code()
        
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

    def get_scheduler_output(self):
        """
        Return the output of the scheduler output (a string) if the calculation
        has finished, and output node is present, and the output of the
        scheduler was retrieved.
        
        Return None otherwise.
        """       
        from aiida.common.exceptions import NotExistent
        
        # Shortcut if no error file is set
        if self.SCHED_OUTPUT_FILE is None:
            return None
        
        retrieved_node = self.get_retrieved_node()
        if retrieved_node is None:
            return None

        try:
            outfile_content = retrieved_node.get_file_content(
                self.SCHED_OUTPUT_FILE)
        except (NotExistent):
            # Return None if no file is found
            return None

        return outfile_content

    def get_scheduler_error(self):
        """
        Return the output of the scheduler error (a string) if the calculation
        has finished, and output node is present, and the output of the
        scheduler was retrieved.
        
        Return None otherwise.
        """
        from aiida.common.exceptions import NotExistent

        # Shortcut if no error file is set
        if self.SCHED_ERROR_FILE is None:
            return None

        retrieved_node = self.get_retrieved_node()
        if retrieved_node is None:
            return None

        try:
            errfile_content = retrieved_node.get_file_content(
                self.SCHED_ERROR_FILE)
        except (NotExistent):
            # Return None if no file is found
            return None
        
        return errfile_content

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
        if ParserClass is None:
            raise AttributeError("No output parser is attached to the calculation")
        else:
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

