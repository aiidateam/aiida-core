import os
import importlib

import aiida.common
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from aiida.common.exceptions import (InternalError, ModificationNotAllowed, NotExistent, ValidationError, AiidaException )
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.datastructures import wf_states, wf_exit_call

from aiida.djsite.utils import get_automatic_user

# Name to be used for the section
_section_name = 'workflow'
WF_STEP_EXIT = 'exit'

class Workflow(object):
    
    """
    Base class to represent a workflow. This is the superclass of any workflow implementations,
    and provides all the methods necessary to interact with the database.
    
    The typical use case are workflow stored in the aiida.workflow packages, that are initiated
    either by the user in the shell or by some scripts, and that are monitored by the aiida daemon.

    Workflow can have steps, and each step must contain some calculations to be executed. At the
    end of the step's calculations the workflow is reloaded in memory and the next methods is called.

    """
    
    _logger       = aiida.common.aiidalogger.getChild('workflow')
    
    def __init__(self,**kwargs):
        
            """
            If initialized with an uuid the Workflow is loaded from the DB, if not a new
            workflow is generated and added to the DB following the stack frameworks.
            
            This means that only modules inside aiida.worflows are allowed to implements
            the workflow super calls and be stored. The caller names, modules and files are
            retrieved from the stack.
            """
            from aiida.djsite.utils import get_automatic_user
            from aiida.djsite.db.models import DbWorkflow
            
            self._to_be_stored = True

            uuid = kwargs.pop('uuid', None)
            
            if uuid is not None:
                if kwargs:
                        raise ValueError("If you pass a UUID, you cannot pass any further parameter")
                
                try:
                        self.dbworkflowinstance    = DbWorkflow.objects.get(uuid=uuid)
                        self.params                = self.get_parameters()
                        self._to_be_stored         = False
                        
                        #self.logger.info("Workflow found in the database, now retrieved")
                        
                except ObjectDoesNotExist:
                        raise NotExistent("No entry with the UUID {} found".format(uuid))
                    
            else:
                
                # ATTENTION: Do not move this code outside or encapsulate it in a function
                
                import inspect
                stack = inspect.stack()
                
                
                #cur_fr  = inspect.currentframe()
                #call_fr = inspect.getouterframes(cur_fr, 2)
                
                # Get all the caller data
                caller_frame        = stack[1][0]
                caller_file         = stack[1][1]
                caller_funct        = stack[1][3]
                
                caller_module       = inspect.getmodule(caller_frame)
                caller_module_class = caller_frame.f_locals.get('self', None).__class__
                
                if not caller_funct=="__init__":
                    raise SystemError("A workflow must implement the __init__ class explicitly")
                
                # Test if the launcher is another workflow
                
#                 print "caller_module", caller_module
#                 print "caller_module_class", caller_module_class
#                 print "caller_file", caller_file
#                 print "caller_funct", caller_funct
                  
                # Accept only the aiida.workflows packages
                if caller_module == None or not caller_module.__name__.startswith("aiida.workflows"):
                        raise SystemError("The superclass can't be called directly")
                
                self.caller_module = caller_module.__name__
                self.caller_module_class  = caller_module_class.__name__
                self.caller_file   = caller_file
                self.caller_funct  = caller_funct
                
                self.store()
                
                # Test is this is a sub-workflow
                sub_stack_frame  = stack[2][0]
                sub_caller_funct = stack[2][3]
                sub_module_class = sub_stack_frame.f_locals.get('self', None).__class__
                
#                 print "sub_module_class", sub_module_class
#                 print "sub_caller_funct", sub_caller_funct
                
                if inspect.getclasstree([sub_module_class])[0][0]==Workflow:
                    wf_parent_uuid = sub_stack_frame.f_locals.get("self",None).uuid()
                    sub_stack_frame.f_locals.get("self",None).get_step(sub_caller_funct).add_sub_workflow(self.dbworkflowinstance)
#                     print "I AM A SUB MODULE !!"
                
                # Test if there are parameters as input
                
                params = kwargs.pop('params', None)
                
                if params is not None:
                    if type(params) is dict:
                        self.set_params(params)
                
   
    @classmethod
    def query(cls,*args,**kwargs):
        """
        Map to the aiidaobjects manager of the DbWorkflow, that returns
        Workflow objects instead of DbWorkflow entities.
        
        """
        from aiida.djsite.db.models import DbWorkflow
        return DbWorkflow.aiidaobjects.filter(*args,**kwargs)
         
    @property
    def logger(self):
        return self._logger
        
    def store(self):
        
        """
        Stores the object data in the database
        """
        
        from aiida.djsite.db.models import DbWorkflow
        import hashlib
        
        
        # This stores the MD5 as well, to test in case the workflow has been modified after the launch 
        self.dbworkflowinstance = DbWorkflow.objects.create(user=get_automatic_user(),
                                                        module = self.caller_module,
                                                        module_class = self.caller_module_class,
                                                        script_path = self.caller_file,
                                                        script_md5 = hashlib.md5(self.caller_file).hexdigest()
                                                        )
        

    def uuid(self):
        return self.dbworkflowinstance.uuid
    
    def info(self):
        
        """
        Returns an array with all the informations
        """
        
        return [self.dbworkflowinstance.module,
            self.dbworkflowinstance.module_class, 
            self.dbworkflowinstance.script_path,
            self.dbworkflowinstance.script_md5,
            self.dbworkflowinstance.time,
            self.dbworkflowinstance.status]
    
    # ----------------------------
    #         Parameters
    # ----------------------------
    
    def set_params(self, params):
        
        """
        Adds parameters to the workflow that are both stored and used every time
        the workflow engine re-initialize the specific workflow to launch the new methods.  
        """
        
        self.params = params
        self.dbworkflowinstance.add_parameters(self.params)
    
    def set_status(self, status):
        
        self.dbworkflowinstance.set_status(status)
        
    def get_parameters(self):
        
        return self.dbworkflowinstance.get_parameters()

    # ----------------------------
    #         Steps
    # ----------------------------

    def get_step(self,method):

        """
        Query the database to return the step object, on which calculations and next step are
        linked. In case no step if found None is returned, useful for loop configuration to
        test whether is the first time the method gets called. 
        """
        
        if isinstance(method, basestring):
            method_name = method
        else:
            method_name = method.__name__
        
        if (method_name==WF_STEP_EXIT):
            raise InternalError("Cannot query a step with name {}, reserved string".format(method_name))            
    
        step, created = self.dbworkflowinstance.steps.get_or_create(name=method_name, user=get_automatic_user())
        return step

    def get_steps(self, state = None):
        
        if state == None:
            return self.dbworkflowinstance.steps.all()#.values_list('name',flat=True)
        else:
            return self.dbworkflowinstance.steps.filter(status=state)    


    def next(self, method):
        
        """
        Add to the database the next step to be called after the completion of the calculation.
        The source step is retrieved from the stack frameworks and the object can be either a string
        or a method.
        """
        
        if isinstance(method, basestring):
            method_name = method
        else:
            method_name = method.__name__
            
        import inspect
        from aiida.common.datastructures import wf_start_call, wf_states, wf_exit_call

        # ATTENTION: Do not move this code outside or encapsulate it in a function
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]
        
        self.get_step(caller_funct).set_nextcall(method_name)
        
        if (caller_funct==wf_start_call):
            self.dbworkflowinstance.set_status(wf_states.RUNNING)


    def start(self,*args,**kwargs):
        pass

    def exit(self):
        pass
#
    # ----------------------------
    #         Calculations
    # ----------------------------
    
    def add_calculation(self, calc):
        
        """
        Adds a calculation to the caller step in the database. For a step to be completed all
        the calculations have to be RETRIVED, after which the next methid gets called.
        The source step is retrieved from the stack frameworks.
        """
        
        from aiida.orm import Calculation
        from celery.task import task
        from aiida.djsite.db import tasks

        import inspect

        if (not isinstance(calc,Calculation)):
            raise AiidaException("Cannot add a calculation not of type Calculation")                        

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]
        
        print "caller_funct", caller_funct
        
        self.get_step(caller_funct).add_calculation(calc)
    
    
    def get_step_calculations(self, step, calc_state = None):
        
        """
        Retrieve the calculations connected to a specific step in the database. If the step
        is not existent it returns None, useful for simpler grammatic in the worflow definition.
        """
        
        if isinstance(step, basestring):
            method_name = step
        else:
            method_name = step.__name__
        
        try:
            stp = self.dbworkflowinstance.steps.get(name=method_name)
            return stp.get_calculations(state = calc_state)
        except ObjectDoesNotExist:
            return None
        except:
            raise AiidaException("Cannot retrive step's calculations")


    # ----------------------------
    #         Support methods
    # ----------------------------

    def kill_step_calculations(self, step):
        
        from aiida.common.datastructures import calc_states
            
        for c in step.get_calculations():
            c._set_state(calc_states.FINISHED)


    def kill(self):
         
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
         
        for s in self.get_steps(state=wf_states.RUNNING):
            self.kill_step_calculations(s)
            
            for w in s.get_sub_workflows():
                w.kill()
        
        self.dbworkflowinstance.set_status(wf_states.FINISHED)
        
# ------------------------------------------------------
#         Module functions for monitor and control
# ------------------------------------------------------


def list_workflows(expired=False):
    
    """
    Simple printer witht all the workflow status, to remove when REST APIs will be ready.
    """
    
    from aiida.djsite.utils import get_automatic_user
    from aiida.djsite.db.models import DbWorkflow
    from django.db.models import Q
    
    import ntpath
    
    if expired:
        w_list = DbWorkflow.objects.filter(Q(user=get_automatic_user()))
    else:
        w_list = DbWorkflow.objects.filter(Q(user=get_automatic_user()) & (Q(status=wf_states.RUNNING)))
    
    for w in w_list:
        print ""
        print "Workflow {0}.{1} [uuid: {3}] started at {2} is {4}".format(w.module,w.module_class, w.time, w.uuid, w.status)
        
        if w.parent_workflow_step.all():
            print "[subworkflow of {0} from {1}]".format(w.parent_workflow_step.get().name, w.parent_workflow_step.get().parent.uuid)
            
        if expired:
            steps = w.steps.all()
        else:
            steps = w.steps.filter(status=wf_states.RUNNING)
            
        for s in steps:
            print "- Running step: {0} [{1}] -> {2}".format(s.name,s.status, s.nextcall)
            
            calcs  = s.get_calculations().filter(attributes__key="_state").values_list("uuid", "ctime", "attributes__tval")
            wflows = s.get_sub_workflows().values_list("uuid", "module", "module_class", "status")
            
            for c in calcs:
                print "   Calculation {0} started at {1} is {2}".format(c[0], c[1], c[2])
            
            for w in wflows:
                print "   Workflow {0} from {1} {2} is {3}".format(w[0], w[1], w[2], w[3])


# ------------------------------------------------------
#         Retrieval
# ------------------------------------------------------

def retrieve(wf_db):
    
    """
    Core of the workflow next engine. The workflow is checked against MD5 hash of the stored script, 
    if the match is found the python script is reload in memory with the importlib library, the
    main class is searched and then loaded, parameters are added and the new methid is launched.
    """
    
    from aiida.djsite.db.models import DbWorkflow
    import importlib
    import hashlib
    
    module       = wf_db.module
    module_class = wf_db.module_class
    md5          = wf_db.script_md5
    script_path  = wf_db.script_path
     
    if not md5==hashlib.md5(script_path).hexdigest():
        raise ValidationError("Unable to load the original workflow module {}, MD5 has changed".format(module))
     
    try:
        wf_mod = importlib.import_module(module)
    except ImportError:
        raise InternalError("Unable to load the workflow module {}".format(module))
    
    for elem_name, elem in wf_mod.__dict__.iteritems():
        
        if module_class==elem_name: #and issubclass(elem, Workflow):
            return  getattr(wf_mod,elem_name)(uuid=wf_db.uuid)
                       
            
def retrieve_by_uuid(uuid):
    
    """
    Simple method to use retrieve starting from uuid
    """
    
    from aiida.djsite.db.models import DbWorkflow
    
    try:
        
        dbworkflowinstance    = DbWorkflow.objects.get(uuid=uuid)
        return  retrieve(dbworkflowinstance)
              
    except ObjectDoesNotExist:
        raise NotExistent("No entry with the UUID {} found".format(uuid))
                        
def kill_by_uuid(uuid):
    
    """
    Simple method to use retrieve starting from uuid
    """
    
    wf = retrieve_by_uuid(uuid)
    wf.kill()
    