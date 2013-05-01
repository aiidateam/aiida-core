from aida.orm import Node

'''
Each calculation object should be defined by analogy of a function 
with a fixed set of labeled and declared inputs.

mystruc = Struc(...)
myinputparam = InputParam(...)
myjobparam = JobParam(...)
myupfA = UPF(...)
myupfB = UPF(...)

MyCalc = Calc({'struc': Struc(), 'upfA': UPF(),...})
This will define the abstract object with labeled input ports of defined type. 

MyCalc({'struc':mystruc, 'upfA':myupfA, ...})

Calculations can exist in the db as empty entities of state 'Abstract'.
Also Data can exist in the db with 'Abstract' state. This can be used to pre-define a workflow.

Calculation can only be submitted if all the data inputs are filled with concrete data objects.
It then changes status to 'Prepared' and so on.
Note: a calculation is set to 'retrieved' when all output nodes are validated and stored (TBD). 

When dealing with workflows g(f(A,B),C) = h(A,B,C)
however g(f(A,B=5),C) = h(A,C) since B is concrete.

To repeat an existing (static) workflow, take the set of calculation nodes, 
copy them and related data nodes and set everything to abstract. Then run throught the static workflow manager.
User can choose new data inputs.

A dynamic workflow is a script that creates calc and data on the fly. 
The script can be stored as an attribute of a previously generated workflow.
Here each calculation needs to be hashed in order to be reused on restarts.

NOTE: Need to include functionality of an observer method in calc or data plugins, to check the data 
while the calculation is running, to make sure that everything is going as planned, otherwise stop.

TODO: set the following as properties of the Calculation
        #        'email',
        #        'emailOnStarted',
        #        'emailOnTerminated',
        #        'rerunnable',
        #        'queueName', 
        #        'numNodes',
        #        'priority',
        #        'resourceLimits',


'''

class Calculation(Node):
    _plugin_type_string = "calculation"
    _updatable_attributes = ('state', 'job_id', 'scheduler_state', 'last_jobinfo',
			     'remote_workdir')
    
    def __init__(self,*args,**kwargs):
        from aida.common.datastructures import calcStates
        
        self._logger = super(Calculation,self).logger.getChild('calculation')
        super(Calculation,self).__init__(*args, **kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            # if I am loading an existing calc: stop here
            return

        # For new calculations
        self._set_state(calcStates.NEW)

        computer = kwargs.pop('computer', None)
        if computer is not None:
            self.set_computer(computer)

        if kwargs:
            raise ValueError("Invalid parameters found in the __init__: {}".format(kwargs.keys()))

    def validate(self):
        from aida.common.datastructures import calcStates
        from aida.common.exceptions import ValidationError
        
        super(Calculation,self).validate()

        if self.get_computer() is None:
            raise ValidationError("You did not specify any computer")

        if self.get_state() not in calcStates:
            raise ValidationError("Calculation state '{}' is not valid".format(self.get_state()))
        
    def add_link_from(self,src, *args, **kwargs):
        '''
        Add a link with a code as destination.
        You can use the parameters of the base Node class, in particular the label
        parameter to label the link.
        '''
        
        from aida.orm.data import Data
        from aida.orm.code import Code
        
        
        if not isinstance(src,(Data, Code)):
            raise ValueError("Nodes entering in calculation can only be of type data or code")
        
        return super(Calculation,self).add_link_from(src, *args, **kwargs)


    def set_computer(self,computer):
        """
        TODO: probably this method should be in the base class, and check for the type
        """
        from aida.djsite.db.models import Computer
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

        if self._to_be_stored:
            if isinstance(computer, basestring):
                try:
                    computer = Computer.objects.get(hostname=computer)
                except ObjectDoesNotExist:
                    raise ValueError("No computer found in the table of computers with "
                                     "the given name '{}'".format(computer))
                except MultipleObjectsReturned:
                    raise ValueError("There is more than one computer with name '{}', "
                                     "pass a Django Computer instance".format(computer))
            elif isinstance(computer, Computer):
                if computer.pk is None:
                    raise ValueError("The computer instance you are passing has not been stored yet")
            else:
                raise ValueError("Pass either a computer name, or a Computer django instance")
    
            self.dbnode.computer = computer
        else:
            self.logger.error("Trying to change the computer of an already saved node: {}".format(
                self.uuid))
            raise ModificationNotAllowed("Node with uuid={} was already stored".format(self.uuid))

    def get_computer(self):
        return self.dbnode.computer

    def _set_state(self, state):
        from aida.common.datastructures import calcStates
        if state not in calcStates:
            raise ValueError("'{}' is not a valid calculation status".format(state))
        self.set_attr('state', state)

    def get_state(self):
        return self.get_attr('state', None)

    def _set_remote_workdir(self, remote_workdir):
        self.set_attr('remote_workdir', remote_workdir)

    def get_remote_workdir(self):
        return self.get_attr('remote_workdir', None)

    def _set_job_id(self, job_id):
        """
        Always set as a string
        """
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
    def get_all_with_state(cls, state, computer=None, user=None, only_computer_user_pairs = False):
        """
        Filter all calculations with a given state.

        Issue a warning if the state is not in the list of valid states.

        Args:
            state: The state to be used to filter (should be a string among those defined in
                aida.common.datastructures.calcStates)
            computer: a Django entry (or its pk) of a computer in the Computer table;
                if present, the results are restricted to calculations running on that
                specific computer
            user: a Django entry (or its pk) of a user in the User table;
                if present, the results are restricted to calculations of that
                specific user
            only_computer_user_pairs: if False (default) return a queryset where each element
                is a suitable instance of Node (it should be an instance of Calculation, if
                everything goes right!)
                If True, return only a list of tuples, where each tuple is in the format
                ('computer__id', 'user__id') [where the IDs are the IDs of the respective tables]
        """
        # I assume that calcStates are strings. If this changes in the future, update the
        # filter below from attributes__tval to the correct field.
        from aida.common.datastructures import calcStates
        if state not in calcStates:
            cls.logger.warning("querying for calculation state='{}', but it is not a "
                              "valid calculation state".format(state))

        kwargs = {}
        if computer is not None:
            kwargs['computer'] = computer
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
            
