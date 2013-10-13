import os
import importlib

import aiida.common
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from aiida.common.exceptions import (InternalError, ModificationNotAllowed, NotExistent, ValidationError, AiidaException )
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.datastructures import wf_states, wf_exit_call

from aiida.djsite.utils import get_automatic_user
from aiida.common import aiidalogger

logger = aiidalogger.getChild('Workflow')

# Name to be used for the section
_section_name = 'workflow'

class Workflow(object):
    
    """
    Base class to represent a workflow. This is the superclass of any workflow implementations,
    and provides all the methods necessary to interact with the database.
    
    The typical use case are workflow stored in the aiida.workflow packages, that are initiated
    either by the user in the shell or by some scripts, and that are monitored by the aiida daemon.

    Workflow can have steps, and each step must contain some calculations to be executed. At the
    end of the step's calculations the workflow is reloaded in memory and the next methods is called.

    """
    
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
                                
                # Test if there are parameters as input
                params = kwargs.pop('params', None)
                
                if params is not None:
                    if type(params) is dict:
                        self._set_parameters(params)
                
            
            self.attach_calc_lazy_storage  = {}
            self.attach_subwf_lazy_storage = {}
            
#     def __getattribute__(self,name):
#         
#         try:
#             attr = object.__getattribute__(self, name)
#         except:
#             raise AttributeError()
#         
#         if hasattr(attr, '__call__') and name=="start":
#             
#             self.logger.debug("Start attributes: {0}".format(attr.__dict__))
#             
#             if self.get_status() == wf_states.INITIALIZED:
#                 self.set_status(wf_states.RUNNING)
#                 return attr
#             else:
#                raise AiidaException("Cannot start an already started workflow")   
#         else:
#             return attr
        
    @classmethod
    def query(cls,*args,**kwargs):
        """
        Map to the aiidaobjects manager of the DbWorkflow, that returns
        Workflow objects instead of DbWorkflow entities.
        
        """
        from aiida.djsite.db.models import DbWorkflow
        return DbWorkflow.aiidaobjects.filter(*args,**kwargs)
         
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
        self._to_be_stored      = False

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
    
    # --------------------------------------------
    #         Parameters, attribute, results
    # --------------------------------------------
    
    def _set_parameters(self, params, force=False):
        
        """
        Adds parameters to the workflow that are both stored and used every time
        the workflow engine re-initialize the specific workflow to launch the new methods.  
        """
        
        #self.params = params
        self.dbworkflowinstance.add_parameters(params, force=force)
    
    def get_parameters(self):
        return self.dbworkflowinstance.get_parameters()
    
    def get_parameter(self, _name):
        return self.dbworkflowinstance.get_parameter(_name)
    
    # ----------------------------
    
    def get_attributes(self):
        return self.dbworkflowinstance.get_attributes()
    
    def get_attribute(self, _name):
        return self.dbworkflowinstance.get_attribute(_name)
    
    def add_attributes(self, _params):
        self.dbworkflowinstance.add_attributes(_params)
    
    def add_attribute(self, _name, _value):
        self.dbworkflowinstance.add_attribute(_name, _value)
    
    # ----------------------------
    
    def get_results(self):
        return self.dbworkflowinstance.get_results()
    
    def get_result(self, _name):
        return self.dbworkflowinstance.get_result(_name)
    
    def add_results(self, _params):
        self.dbworkflowinstance.add_results(_params)
    
    def add_result(self, _name, _value):
        self.dbworkflowinstance.add_result(_name, _value)
    
        
    # ----------------------------
    #         Parameters
    # ----------------------------

    def get_status(self):
        
        return self.dbworkflowinstance.status
    
    def set_status(self, status):
        
        self.dbworkflowinstance.set_status(status)
    
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
        
        if (method_name==wf_exit_call):
            raise InternalError("Cannot query a step with name {}, reserved string".format(method_name))            
        
        try:
            step = self.dbworkflowinstance.steps.get(name=method_name, user=get_automatic_user())
            return step
        except ObjectDoesNotExist:
            return None

    def get_steps(self, state = None):
        
        if state == None:
            return self.dbworkflowinstance.steps.all()#.values_list('name',flat=True)
        else:
            return self.dbworkflowinstance.steps.filter(status=state)    
    
    def has_step(self,method):
        
        return not self.get_step(method)==None
    
    # ----------------------------
    #         Next
    # ----------------------------
    
    @classmethod
    def step(cls, fun):
        from aiida.common.datastructures import wf_start_call, wf_states, wf_exit_call
        
        caller_method = fun.__name__
        
        # This function gets called only if the method is launched with the execution brakets ()
        # Otherwise, when the methid is addressed in a next() call this never gets called and only the 
        # attributes are added
        def wrapper(cls, *args, **kwargs):
            
            """
            """
            if len(args)>0:
                raise AiidaException("A step method cannot have any argument, use add_attribute to the workflow")
            
            # If a methos is lauched and the step is RUNNING or INITIALIZED we should stop
            if cls.has_step(caller_method) and not cls.get_step(caller_method).status == wf_states.ERROR:
                raise AiidaException("The method {0} has already been initialized !".format(caller_method))
            
            # If a methos is lauched and the steo is halted for ERROR, then clean the step and relaunch
            if cls.has_step(caller_method) and cls.get_step(caller_method).status == wf_states.ERROR:
                
                for w in cls.get_steps(caller_method).get_sub_workflows():
                    w.kill()
                cls.get_steps(caller_method).remove_sub_workflows()
                
                for c in cls.get_steps(caller_method).get_calculations():
                    #c.kill()
                    logger.error("TODO - Implement kill function in calculation")
                cls.get_steps(caller_method).remove_calculations()
                
                #self.get_steps(caller_method).set_nextcall(wf_exit_call)
            
            method_step, created = cls.dbworkflowinstance.steps.get_or_create(name=caller_method, user=get_automatic_user())    
            
            if not created:
                method_step.set_status(wf_states.INITIALIZED)
            
            try:
                fun(cls)
            except:
                
                import sys, os
                exc_type, exc_value, exc_traceback = sys.exc_info()                
                cls.append_to_report("ERROR ! This workflow got and error in the {0} method, we report down the stack trace".format(caller_method))
                cls.append_to_report("filename: {0}".format(exc_traceback.tb_frame.f_code.co_filename))
                cls.append_to_report("lineno: {0}".format(exc_traceback.tb_lineno))
                cls.append_to_report("name: {0}".format(exc_traceback.tb_frame.f_code.co_name))
                cls.append_to_report("type: {0}".format(exc_type.__name__))
                cls.append_to_report("message: {0}".format(exc_value.message))
                
                method_step.set_status(wf_states.ERROR)
            
            return None 
        
        
        out = wrapper
        
        wrapper.is_wf_step = True
        wrapper.wf_step_name = fun.__name__
        
        return wrapper
        
        
    def next(self, next_method):
        
        """
        Add to the database the next step to be called after the completion of the calculation.
        The source step is retrieved from the stack frameworks and the object can be either a string
        or a method.
        """
        
        import inspect
        from aiida.common.datastructures import wf_start_call, wf_states, wf_exit_call
 
        # ATTENTION: Do not move this code outside or encapsulate it in a function
        curframe      = inspect.currentframe()
        calframe      = inspect.getouterframes(curframe, 2)
        caller_method = calframe[1][3]
        
        if not self.has_step(caller_method):
            raise AiidaException("Che caller method is either not a steo or has not been registered as one")
        
        is_wf_exit = next_method.__name__==wf_exit_call
        
        if not is_wf_exit:
            try:
                is_wf_step = getattr(next_method,"is_wf_step")
            except AttributeError:
                raise AiidaException("Cannot add as next call a method not decorated as Workflow method")
        
        if (is_wf_exit):
            next_method_name = wf_exit_call
        else:
            next_method_name = next_method.wf_step_name
        
        method_step      = self.dbworkflowinstance.steps.get(name=caller_method, user=get_automatic_user())
        
        # Attach calculations
        if caller_method in self.attach_calc_lazy_storage:
            for c in self.attach_calc_lazy_storage[caller_method]:
                method_step.add_calculation(c)
        
        # Attach sub-workflows
        if caller_method in self.attach_subwf_lazy_storage:
            for w in self.attach_subwf_lazy_storage[caller_method]:
                method_step.add_sub_workflow(w)
        
        # Start the workflow if this is the start method
        if (self.dbworkflowinstance.status==wf_states.INITIALIZED):
            self.dbworkflowinstance.set_status(wf_states.RUNNING)

        method_step.set_nextcall(next_method_name)
        
        #method_step.set_status(wf_states.RUNNING)
        
    # ----------------------------
    #         Attachments
    # ----------------------------
    
    def attach_calculation(self, calc):
        
        
        """
        Adds a calculation to the caller step in the database. For a step to be completed all
        the calculations have to be RETRIVED, after which the next methid gets called.
        The source step is retrieved from the stack frameworks.
        """
        
        from aiida.orm import Calculation
        from celery.task import task
        from aiida.djsite.db import tasks

        import inspect

        if (not issubclass(calc.__class__,Calculation) and not isinstance(calc, Calculation)):
            raise AiidaException("Cannot add a calculation not of type Calculation")                        

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]
        
        if not caller_funct in self.attach_calc_lazy_storage:
            self.attach_calc_lazy_storage[caller_funct] = []
        self.attach_calc_lazy_storage[caller_funct].append(calc)
        
    def attach_workflow(self, sub_wf):
        
        from aiida.orm import Calculation
        from celery.task import task
        from aiida.djsite.db import tasks

        import inspect

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]
        
        if not caller_funct in self.attach_subwf_lazy_storage:
            self.attach_subwf_lazy_storage[caller_funct] = []
        self.attach_subwf_lazy_storage[caller_funct].append(sub_wf)
        
    
    # ----------------------------
    #      Subworkflows
    # ----------------------------


    def get_step_calculations(self, step_method, calc_state = None):
        
        """
        Retrieve the calculations connected to a specific step in the database. If the step
        is not existent it returns None, useful for simpler grammatic in the worflow definition.
        """
       
        if not getattr(step_method,"is_wf_step"):
            raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")
        
        step_method_name = step_method.wf_step_name
        
        try:
            stp = self.get_step(step_method_name)
            return stp.get_calculations(state = calc_state)
        except:
            raise AiidaException("Cannot retrieve step's calculations")
        

    def kill_step_calculations(self, step):
        
        from aiida.common.datastructures import calc_states
            
        for c in step.get_calculations():
            c._set_state(calc_states.FINISHED)

    # ----------------------------
    #         Support methods
    # ----------------------------


    def kill(self):
         
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
         
        for s in self.get_steps(state=wf_states.RUNNING):
            self.kill_step_calculations(s)
            
            for w in s.get_sub_workflows():
                w.kill()
        
        self.dbworkflowinstance.set_status(wf_states.FINISHED)
    
    
    # ------------------------------------------------------
    #         Report
    # ------------------------------------------------------
    
    def get_report(self):
        
        if len(self.dbworkflowinstance.parent_workflow_step.all())==0:
            return self.dbworkflowinstance.report.splitlines()
        else:
            return Workflow(uuid=self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).get_report()
    
    def clear_report(self):
        
        if len(self.dbworkflowinstance.parent_workflow_step.all())==0:
            self.dbworkflowinstance.clear_report()
        else:
            Workflow(uuid=self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).clear_report()
            
    
    def append_to_report(self, text):
        
        if len(self.dbworkflowinstance.parent_workflow_step.all())==0:
            self.dbworkflowinstance.append_to_report(text)
        else:
            Workflow(uuid=self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).append_to_report(text)
        
    # ------------------------------------------------------
    #         Retrieval
    # ------------------------------------------------------
    
    @classmethod
    def get_subclass_from_dbnode(cls,wf_db):
        
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
                return getattr(wf_mod,elem_name)(uuid=wf_db.uuid)
                           
    @classmethod      
    def get_subclass_from_uuid(cls,uuid):
        
        """
        Simple method to use retrieve starting from uuid
        """
        
        from aiida.djsite.db.models import DbWorkflow
        
        try:
            
            dbworkflowinstance    = DbWorkflow.objects.get(uuid=uuid)
            return cls.get_subclass_from_dbnode(dbworkflowinstance)
                  
        except ObjectDoesNotExist:
            raise NotExistent("No entry with the UUID {} found".format(uuid))
    
    @classmethod 
    def kill_by_uuid(cls,uuid):
    
        cls.retrieve_by_uuid(uuid).kill()
    
    def exit(self):
        pass
    
    def revive(self):
        
        self.set_status(wf_states.RUNNING)
    
# ------------------------------------------------------
#         Module functions for monitor and control
# ------------------------------------------------------

accumulated_tab = 0
tab_size = 2
    
def list_workflows(ext=False,expired=False):
    
    """
    Simple printer witht all the workflow status, to remove when REST APIs will be ready.
    """
    
    from aiida.djsite.utils import get_automatic_user
    from aiida.djsite.db.models import DbWorkflow
    from django.db.models import Q
    import datetime
    from django.utils.timezone import utc
    import ntpath
    
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    
    
    def str_timedelta(dt):
        
        s = dt.seconds
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '%sh :%sm :%ss' % (hours, minutes, seconds)
    
    def get_separator(accumulated_tab,tab_size, title=None):
        
        if title:
            out = "+"
            for i in range(accumulated_tab):
                out+='-'*(tab_size)
            return out
        
        else:
            
            out = "|"+' '*(tab_size)
            for i in range(accumulated_tab-1):
                out+=' '*tab_size
            return out
        
    def print_workflow(w,ext=False):
        
        global accumulated_tab, tab_size
        
        print get_separator(accumulated_tab,tab_size, title=True)+" Workflow {0} ({1}) is {2} [{3}]".format(w.module_class, w.uuid, w.status, str_timedelta(now-w.time))
            
#         if expired:
#             steps = w.steps.all()
#         else:
#             steps = w.steps.filter(status=wf_states.RUNNING)
        steps = w.steps.all()

        accumulated_tab+=1
        for s in steps:
            
            print get_separator(accumulated_tab,tab_size)+" Step: {0} is {1}".format(s.name,s.status)
            
            ## Calculations
            calcs  = s.get_calculations().filter(attributes__key="_state").values_list("uuid", "ctime", "attributes__tval")
            
            accumulated_tab+=1
            for c in calcs:
                print get_separator(accumulated_tab,tab_size)+" Calculation ({0}) is {1}".format(c[0], c[2])
            accumulated_tab-=1
        
            ## SubWorkflows
            wflows = s.get_sub_workflows()
            
            accumulated_tab+=1
            for sw in wflows:
                print_workflow(sw.dbworkflowinstance, ext=ext)
            accumulated_tab-=1
            
        accumulated_tab-=1
    
    q_object = Q(user=get_automatic_user())
    
    if expired:
        w_list = DbWorkflow.objects.filter(q_object)
    else:
        
        q_object.add(~Q(status=wf_states.FINISHED), Q.AND)
        w_list = DbWorkflow.objects.filter(q_object)
    
    
    for w in w_list:
        
        accumulated_tab = 0
        print ""
        
        if len(w.parent_workflow_step.all())==0:
            print_workflow(w, ext=ext)
        
                
    