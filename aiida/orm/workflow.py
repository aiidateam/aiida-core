# -*- coding: utf-8 -*-
import os
import importlib

from django.core.exceptions import ObjectDoesNotExist
from aiida.common.exceptions import (InternalError, ModificationNotAllowed, 
                                  NotExistent, ValidationError, AiidaException )
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.datastructures import wf_states, wf_exit_call

from aiida.djsite.utils import get_automatic_user
from aiida.common import aiidalogger

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

logger = aiidalogger.getChild('Workflow')

class Workflow(object):    
    """
    Base class to represent a workflow. This is the superclass of any workflow implementations,
    and provides all the methods necessary to interact with the database.
    
    The typical use case are workflow stored in the aiida.workflow packages, that are initiated
    either by the user in the shell or by some scripts, and that are monitored by the aiida daemon.

    Workflow can have steps, and each step must contain some calculations to be executed. At the
    end of the step's calculations the workflow is reloaded in memory and the next methods is called.


    .. todo: verify if there are other places (beside label and description) where
      the _increment_version_number_db routine needs to be called to increase
      the nodeversion after storing 
    """

    # Name to be used for the repository section
    _section_name = 'workflow'
    
    # The name of the subfolder in which to put the files/directories added with add_path
    _path_subfolder_name = 'path'

    
    def __init__(self,**kwargs):
        
            """
            Initializes the Workflow super class, store the instance in the DB and in case
            stores the starting parameters.
            
            If initialized with an uuid the Workflow is loaded from the DB, if not a new
            workflow is generated and added to the DB following the stack frameworks. This 
            means that only modules inside aiida.workflows are allowed to implements
            the workflow super calls and be stored. The caller names, modules and files are
            retrieved from the stack.
            
            :param uuid: a string with the uuid of the object to be loaded.
            :param params: a dictionary of storable objects to initialize the specific workflow
            :raise: NotExistent: if there is no entry of the desired workflow kind with 
                                 the given uuid.
            """
            from aiida.djsite.db.models import DbWorkflow
            import hashlib
            
            self._to_be_stored = True
            
            uuid = kwargs.pop('uuid', None)
            
            if uuid is not None:
                self._to_be_stored = False
                if kwargs:
                        raise ValueError("If you pass a UUID, you cannot pass any further parameter")
                
                try:
                        self._dbworkflowinstance   = DbWorkflow.objects.get(uuid=uuid)
                        
                        #self.logger.info("Workflow found in the database, now retrieved")
                        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)
                        
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
                
                self._temp_folder = SandboxFolder()
                self.current_folder.insert_path(self.caller_file, self.caller_module_class)
                # self.store()
                                
                # Test if there are parameters as input
                params = kwargs.pop('params', None)
                
                if params is not None:
                    if type(params) is dict:
                        self.set_params(params)

                # This stores the MD5 as well, to test in case the workflow has been modified after the launch 
                self._dbworkflowinstance = DbWorkflow(user=get_automatic_user(),
                    module = self.caller_module,
                    module_class = self.caller_module_class,
                    script_path = self.caller_file,
                    script_md5 = hashlib.md5(self.caller_file).hexdigest())

                
            
            self.attach_calc_lazy_storage  = {}
            self.attach_subwf_lazy_storage = {}

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))
                
    def __str__(self):
        if self._to_be_stored:
            return "uuid: {} (unstored)".format(self.uuid)
        else:
            return "uuid: {} (pk: {})".format(self.uuid, self.pk)
    
    ## --------------------------------------
    ##    DB Instance
    ## --------------------------------------

    @property
    def dbworkflowinstance(self):
        """
        Get the DbWorkflow object stored in the super class.
        
        :return: DbWorkflow object from the database
        """

        from aiida.djsite.db.models import DbWorkflow
        
        if self._dbworkflowinstance.pk is None:
            return self._dbworkflowinstance
        else:
            self._dbworkflowinstance = DbWorkflow.objects.get(pk=self._dbworkflowinstance.pk)
            return self._dbworkflowinstance
    
    def _get_dbworkflowinstance(self):
        return self.dbworkflowinstance

    @property
    def label(self):
        """
        Get the label of the workflow.
        
        :return: a string
        """
        return self.dbworkflowinstance.label

    @label.setter
    def label(self,label):
        """
        Set the label of the workflow.
        
        :param label: a string
        """
        self._update_db_label_field(label)
            
    def _update_db_label_field(self, field_value):
        """
        Safety method to store the label of the workflow
        
        :return: a string
        """
        from django.db import transaction        

        self.dbworkflowinstance.label = field_value
        if not self._to_be_stored:
            with transaction.commit_on_success():
                self._dbworkflowinstance.save()
                self._increment_version_number_db()
            
    @property
    def description(self):
        """
        Get the description of the workflow.
        
        :return: a string
        """
        return self.dbworkflowinstance.description

    @description.setter
    def description(self,desc):
        """
        Set the description of the workflow
        
        :param desc: a string
        """
        self._update_db_description_field(desc)

    def _update_db_description_field(self, field_value):
        """
        Safety method to store the description of the workflow
        
        :return: a string
        """
        
        from django.db import transaction        

        self.dbworkflowinstance.description = field_value
        if not self._to_be_stored:
            with transaction.commit_on_success():
                self._dbworkflowinstance.save()
                self._increment_version_number_db()


    def _increment_version_number_db(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version (e.g. on adding a
        extra or attribute). 
        """
        from django.db.models import F
        from aiida.djsite.db.models import DbWorkflow

        # I increment the node number using a filter (this should be the right way of doing it;
        # dbnode.nodeversion  = F('nodeversion') + 1
        # will do weird stuff, returning Django Objects instead of numbers, and incrementing at
        # every save; moreover in this way I should do the right thing for concurrent writings
        # I use self._dbnode because this will not do a query to update the node; here I only
        # need to get its pk
        DbWorkflow.objects.filter(pk=self.pk).update(nodeversion = F('nodeversion') + 1)
        
        # This reload internally the node of self._dbworkflowinstance
        _ = self.dbworkflowinstance
        # Note: I have to reload the ojbect. I don't do it here because it is done at every call
        # to self.dbnode
        #self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)

    ## --------------------------------------
    ##    Folder
    ## --------------------------------------
    
    @property
    def repo_folder(self):
        """
        Get the permanent repository folder.
        Use preferentially the current_folder method.
        
        :return: the permanent RepositoryFolder object
        """
        
        return self._repo_folder

    @property
    def current_folder(self):
        """
        Get the current repository folder, 
        whether the temporary or the permanent.
        
        :return: the RepositoryFolder object.
        """
        
        if self._to_be_stored:
            return self.get_temp_folder()
        else:
            return self.repo_folder

    @property
    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.
        
        :return: a Folder object.
        """
        
        return self.current_folder.get_subfolder(
            self._path_subfolder_name,reset_limit=True)
        
    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.
        
        :param str,optional subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        
        return self._get_folder_pathsubfolder.get_subfolder(subfolder).get_content_list()

    def get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.
        
        :return: a SandboxFolder object mapping the node in the repository.
        """
        
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def remove_path(self,path):
        """
        Remove a file or directory from the repository directory.

        Can be called only before storing.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot delete a path after storing the node")
        
        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path must be a relative path")
        self._get_folder_pathsubfolder.remove_path(path)

    def add_path(self,src_abs,dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.
        src_abs: the absolute path of the file to copy.
        dst_filename: the (relative) path on which to copy.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot insert a path after storing the node")
        
        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs,dst_path)


    def get_abs_path(self,path,section=None):
        """
        TODO: For the moment works only for one kind of files, 'path' (internal files)
        """
        if section is None:
            section = self._path_subfolder_name
        
        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.current_folder.get_subfolder(section,reset_limit=True).get_abs_path(path,check_existence=True)
    
    ## --------------------------------------
    ##    Store and infos
    ## --------------------------------------

    
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
        Stores the DbWorkflow object data in the database
        """
        if not self._to_be_stored:
            self.logger.error("Trying to store an already saved workflow: "
                              "pk= {}".format(self.pk))
            raise ModificationNotAllowed(
                "Workflow with pk= {} was already stored".format(self.pk))
        
        self._dbworkflowinstance.save()
        
        if hasattr(self, '_params'):
            self.dbworkflowinstance.add_parameters(self._params, force=False)
        
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)
        self.repo_folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)
        
        self._temp_folder       = None  
        self._to_be_stored      = False
    
        # Important to allow to do w = WorkflowSubClass().store()
        return self
    
    @property
    def uuid(self):
        """
        Returns the DbWorkflow uuid
        """
        return self.dbworkflowinstance.uuid

    @property
    def pk(self):
        """
        Returns the DbWorkflow pk
        """
        return self.dbworkflowinstance.pk
    
    def info(self):
        """
        Returns an array with all the informations about the modules, file, class to locate
        the workflow source code
        """
        
        return [self.dbworkflowinstance.module,
            self.dbworkflowinstance.module_class, 
            self.dbworkflowinstance.script_path,
            self.dbworkflowinstance.script_md5,
            self.dbworkflowinstance.ctime,
            self.dbworkflowinstance.state]
    
    # --------------------------------------------
    #         Parameters, attribute, results
    # --------------------------------------------
    
    def set_params(self, params, force=False):
        """
        Adds parameters to the Workflow that are both stored and used every time
        the workflow engine re-initialize the specific workflow to launch the new methods.  
        """
        def par_validate(params):
            the_params = {}
            for k,v in params.itervalues():
                if any( [isinstance(v,int),
                         isinstance(v,bool),
                         isinstance(v,float),
                         isinstance(v,str)] ):
                    the_params[k] = v
                else:
                    raise ValidationError("Cannot store in the DB a parameter "
                                "which is not of type int, bool, float or str.")
            return the_params
        
        if self._to_be_stored:
            self._params = params
        else:
            the_params = par_validate(params)
            self.dbworkflowinstance.add_parameters(the_params, force=force)
    
    def get_parameters(self):
        """
        Get the Workflow paramenters
        :return: a dictionary of storable objects 
        """
        if self._to_be_stored:
            return self._params
        else:
            return self.dbworkflowinstance.get_parameters()
    
    def get_parameter(self, _name):
        """
        Get one Workflow paramenter
        :param name: a string with the parameters name to retrieve
        :return: a dictionary of storable objects 
        """
        if self._to_be_stored:
            return self._params(_name)
        else:
            return self.dbworkflowinstance.get_parameter(_name)
    
    # ----------------------------
    
    def get_attributes(self):
        """
        Get the Workflow attributes
        :return: a dictionary of storable objects 
        """
        return self.dbworkflowinstance.get_attributes()
    
    def get_attribute(self, _name):
        """
        Get one Workflow attribute
        :param name: a string with the attribute name to retrieve
        :return: a dictionary of storable objects 
        """
        return self.dbworkflowinstance.get_attribute(_name)
    
    def add_attributes(self, _params):
        """
        Add a set of attributes to the Workflow. If another attribute is present with the same name it will
        be overwritten.
        :param name: a string with the attribute name to store
        :param value: a storable object to store
        """
        if self._to_be_stored:
            raise ModificationNotAllowed("You cannot add attributes before storing")
        self.dbworkflowinstance.add_attributes(_params)
    
    def add_attribute(self, _name, _value):
        """
        Add one attributes to the Workflow. If another attribute is present with the same name it will
        be overwritten.
        :param name: a string with the attribute name to store
        :param value: a storable object to store
        """
        if self._to_be_stored:
            raise ModificationNotAllowed("You cannot add attributes before storing")
        self.dbworkflowinstance.add_attribute(_name, _value)
    
    # ----------------------------
    
    def get_results(self):
        """
        Get the Workflow results
        :return: a dictionary of storable objects 
        """
        return self.dbworkflowinstance.get_results()
    
    def get_result(self, _name):
        """
        Get one Workflow result
        :param name: a string with the result name to retrieve
        :return: a dictionary of storable objects 
        """
        return self.dbworkflowinstance.get_result(_name)
    
    def add_results(self, _params):
        """
        Add a set of results to the Workflow. If another result is present with the same name it will
        be overwritten.
        :param name: a string with the result name to store
        :param value: a storable object to store
        """
        self.dbworkflowinstance.add_results(_params)
    
    def add_result(self, _name, _value):
        """
        Add one result to the Workflow. If another result is present with the same name it will
        be overwritten.
        :param name: a string with the result name to store
        :param value: a storable object to store
        """
        self.dbworkflowinstance.add_result(_name, _value)
    
        
    # ----------------------------
    #         Statuses
    # ----------------------------

    def get_status(self):
        """
        Get the Workflow's status
        :return: a state from wf_states in aiida.common.datastructures 
        """
        return self.dbworkflowinstance.state
    
    def set_status(self, status):
        """
        Set the Workflow's status
        :param name: a state from wf_states in aiida.common.datastructures 
        """
        self.dbworkflowinstance.set_status(status)
    
    def is_new(self):
        """
        Returns True is the Workflow's status is CREATED
        """
        return self.dbworkflowinstance.state == wf_states.CREATED
    
    def is_running(self):
        """
        Returns True is the Workflow's status is RUNNING
        """
        return self.dbworkflowinstance.state == wf_states.RUNNING
    
    def has_finished_ok(self):
        """
        Returns True is the Workflow's status is FINISHED
        """
        return self.dbworkflowinstance.state in [wf_states.FINISHED,wf_states.SLEEP] 
    
    def has_failed(self):
        """
        Returns True is the Workflow's status is ERROR
        """
        return self.dbworkflowinstance.state == wf_states.ERROR
    
    def is_subworkflow(self):
        """
        Return True is this is a subworkflow (i.e., if it has a parent), 
        False otherwise.
        """
        return self.dbworkflowinstance.is_subworkflow()
    
    # ----------------------------
    #         Steps
    # ----------------------------

    def get_step(self,step_method):

        """
        Retrieves by name a step from the Workflow.  
        :param step_method: a string with the name of the step to retrieve or a method
        :raise: ObjectDoesNotExist: if there is no step with the specific name. 
        :return: a DbWorkflowStep object.
        """
        
        if isinstance(step_method, basestring):
            step_method_name = step_method
        else:
            
            if not getattr(step_method,"is_wf_step"):
                raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")
        
            step_method_name = step_method.wf_step_name
        
        if (step_method_name==wf_exit_call):
            raise InternalError("Cannot query a step with name {0}, reserved string".format(step_method_name))            
        
        try:
            step = self.dbworkflowinstance.steps.get(name=step_method_name, user=get_automatic_user())
            return step
        except ObjectDoesNotExist:
            return None

    def get_steps(self, state = None):
        
        """
        Retrieves all the steps from a specific workflow Workflow with the possibility to limit the list
        to a specific step's state.
        :param state: a state from wf_states in aiida.common.datastructures
        :return: a list of DbWorkflowStep objects.
        """
        
        if state is None:
            return self.dbworkflowinstance.steps.all().order_by('time')#.values_list('name',flat=True)
        else:
            return self.dbworkflowinstance.steps.filter(state=state).order_by('time')
    
    def has_step(self,step_method):
        """
        Return if the Workflow has a step with a specific name.  
        :param step_method: a string with the name of the step to retrieve or a method
        """
        
        return not self.get_step(step_method)==None
    
    # ----------------------------
    #         Next
    # ----------------------------
    
    @classmethod
    def step(cls, fun):
        """
        This method is used as a decorator for workflow steps, and handles the method's execution, 
        the status updates and the eventual errors.
        
        The decorator generates a wrapper around the input function to execute, adding with the correct 
        step name and a utility variable to make it distinguishable from non-step methods. 
        
        When a step is launched, the wrapper tries to run the function in case of error the status of 
        the workflow is moved to ERROR and the traceback is stored in the report. In general the input 
        method is a step obtained from the Workflow object, and the decorator simply handles a controlled 
        execution of the step allowing the code not to break in case of error in the step's source code.
          
        The wrapper also tests not to run two times the same step, unless a Workflow is in ERROR state, in this
        case all the calculations and subworkflows of the step are killed and a new execution is allowed.
        
        :param fun: a methods to wrap, making it a Workflow step
        :raise: AiidaException: in case the workflow status doesn't allow the execution 
        :return: the wrapped methods, 
        """
        
        
        from aiida.common.datastructures import wf_default_call
        
        wrapped_method = fun.__name__
        
        # This function gets called only if the method is launched with the execution brackets ()
        # Otherwise, when the method is addressed in a next() call this never gets called and only the 
        # attributes are added
        def wrapper(cls, *args, **kwargs):
            
            """
            """
            
            # Store the workflow at the first step executed
            if cls._to_be_stored:
                cls.store()
            
            if len(args)>0:
                raise AiidaException("A step method cannot have any argument, use add_attribute to the workflow")
            
            # If a method is launched and the step is RUNNING or INITIALIZED we should stop
            if cls.has_step(wrapped_method) and \
               not (cls.get_step(wrapped_method).state == wf_states.ERROR or \
                    cls.get_step(wrapped_method).state == wf_states.SLEEP or \
                    cls.get_step(wrapped_method).nextcall == wf_default_call or \
                    cls.get_step(wrapped_method).nextcall == wrapped_method \
                    #cls.has_step(wrapped_method) \
                    ):
                raise AiidaException("The step {0} has already been initialized, cannot change this outside the parent workflow !".format(wrapped_method))
            
            # If a method is launched and the step is halted for ERROR, then clean the step and re-launch
            if cls.has_step(wrapped_method) and \
               ( cls.get_step(wrapped_method).state == wf_states.ERROR or\
                 cls.get_step(wrapped_method).state == wf_states.SLEEP ):
                
                for w in cls.get_step(wrapped_method).get_sub_workflows(): w.kill()
                cls.get_step(wrapped_method).remove_sub_workflows()
                
                for c in cls.get_step(wrapped_method).get_calculations(): c.kill()
                cls.get_step(wrapped_method).remove_calculations()
                
                #self.get_steps(wrapped_method).set_nextcall(wf_exit_call)
            
            method_step, created = cls.dbworkflowinstance.steps.get_or_create(name=wrapped_method, user=get_automatic_user())    
            
            try:
                fun(cls)
            except:
                import sys, traceback
                exc_type, exc_value, exc_traceback = sys.exc_info()                
                cls.append_to_report("ERROR ! This workflow got an error in the {0} method, we report down the stack trace".format(wrapped_method))
                cls.append_to_report("full traceback: {0}".format(traceback.format_exc()))
                method_step.set_status(wf_states.ERROR)
            return None 
        
        out = wrapper
        
        wrapper.is_wf_step = True
        wrapper.wf_step_name = fun.__name__
        
        return wrapper
        
        
    def next(self, next_method):
        """
        Adds the a new step to be called after the completion of the caller method's calculations and subworkflows.
        
        This method must be called inside a Workflow step, otherwise an error is thrown. The
        code finds the caller method and stores in the database the input next_method as the next
        method to be called. At this point no execution in made, only configuration updates in the database. 
        
        If during the execution of the caller method the user launched calculations or subworkflows, this 
        method will add them to the database, making them available to the workflow manager to be launched.
        In fact all the calculation and subworkflow submissions are lazy method, really executed by this call. 
        
        :param next_method: a Workflow step method to execute after the caller method
        :raise: AiidaException: in case the caller method cannot be found or validated  
        :return: the wrapped methods, decorated with the correct step name
        """
        import inspect
        import hashlib
        md5          = self.dbworkflowinstance.script_md5
        script_path  = self.dbworkflowinstance.script_path
        
        if not md5==hashlib.md5(script_path).hexdigest():
            raise ValidationError("Unable to load the original workflow module from {}, MD5 has changed".format(script_path))
 
        # ATTENTION: Do not move this code outside or encapsulate it in a function
        curframe      = inspect.currentframe()
        calframe      = inspect.getouterframes(curframe, 2)
        caller_method = calframe[1][3]
        
#         logger.info("We are in next call of {0} in {1}".format(caller_method, self.uuid()))
        
        if next_method is None:
            raise AiidaException("The next method is None, probably you passed a method with parenthesis ??")
             
        if not self.has_step(caller_method):
            raise AiidaException("The caller method is either not a step or has not been registered as one")
        
        if not next_method.__name__== wf_exit_call:
            try:
                is_wf_step = getattr(next_method,"is_wf_step", None)
            except AttributeError:
                raise AiidaException("Cannot add as next call a method not decorated as Workflow method")
#        else:
#            print "Next is an end call of {0} in {1}".format(caller_method, self.uuid)
            
        # Retrieve the caller method
        method_step = self.dbworkflowinstance.steps.get(name=caller_method, user=get_automatic_user())
        
        # Attach calculations
        if caller_method in self.attach_calc_lazy_storage:
            for c in self.attach_calc_lazy_storage[caller_method]:
                method_step.add_calculation(c)
        
        # Attach sub-workflows
        if caller_method in self.attach_subwf_lazy_storage:
            for w in self.attach_subwf_lazy_storage[caller_method]:
                method_step.add_sub_workflow(w)
        
        # Set the next method
        if not next_method.__name__== wf_exit_call:
            next_method_name = next_method.wf_step_name
        else:
            next_method_name = wf_exit_call
            
        #logger.info("Adding step {0} after {1} in {2}".format(next_method_name, caller_method, self.uuid))
        method_step.set_nextcall(next_method_name)
        
        # 
        self._get_dbworkflowinstance().set_status(wf_states.RUNNING)
        method_step.set_status(wf_states.RUNNING)
        
            
    # ----------------------------
    #         Attachments
    # ----------------------------
    
    def attach_calculation(self, calc):
        """
        Adds a calculation to the caller step in the database. This is a lazy call, no
        calculations will be launched until the ``next`` method gets called. For a step to be 
        completed all the calculations linked have to be in RETRIEVED state, after which the next 
        method gets called from the workflow manager.
        :param calc: a JobCalculation object
        :raise: AiidaException: in case the input is not of JobCalculation type
        """
        from aiida.orm import JobCalculation
        import inspect

        if (not issubclass(calc.__class__,JobCalculation) and not isinstance(calc, JobCalculation)):
            raise AiidaException("Cannot add a calculation not of type JobCalculation")

        for node in calc.get_inputs():
            if node.pk == None:
                raise AiidaException("Cannot add a calculation with "
                                     "unstored inputs")

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]
        
        if not caller_funct in self.attach_calc_lazy_storage:
            self.attach_calc_lazy_storage[caller_funct] = []
        self.attach_calc_lazy_storage[caller_funct].append(calc)
        
    def attach_workflow(self, sub_wf):
        """
        Adds a workflow to the caller step in the database. This is a lazy call, no
        workflow will be started until the ``next`` method gets called. For a step to be 
        completed all the workflows linked have to be in FINISHED state, after which the next 
        method gets called from the workflow manager.
        :param next_method: a Workflow object
        """
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
        Retrieves all the calculations connected to a specific step in the database. If the step
        is not existent it returns None, useful for simpler grammatic in the workflow definition.
        :param next_method: a Workflow step (decorated) method
        :param calc_state: a specific state to filter the calculations to retrieve
        :return: a list of JobCalculations objects
        """
       
        if not getattr(step_method,"is_wf_step"):
            raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")
        
        step_method_name = step_method.wf_step_name
        
        try:
            stp = self.get_step(step_method_name)
            return stp.get_calculations(state = calc_state)
        except:
            raise AiidaException("Cannot retrieve step's calculations")

    def get_step_workflows(self, step_method):
        """
        Retrieves all the workflows connected to a specific step in the database. If the step
        is not existent it returns None, useful for simpler grammatic in the workflow definition.
        :param next_method: a Workflow step (decorated) method
        """
       
        if not getattr(step_method,"is_wf_step"):
            raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")
        
        step_method_name = step_method.wf_step_name
        
        stp = self.get_step(step_method_name)
        return stp.get_sub_workflows()
        

    def kill_step_calculations(self, step):
        """
        Calls the ``kill`` method for each Calculation linked to the step method passed as argument.
        :param step: a Workflow step (decorated) method
        """
            
        for c in step.get_calculations():
            if c._is_new() or c._is_running():
                c.kill()
    
    # ----------------------------
    #         Support methods
    # ----------------------------

    def kill(self):
        """
        Stop the Workflow execution and change its state to FINISHED.
        
        This method Calls the ``kill`` method for each Calculation and each subworkflow 
        linked to each RUNNING step.
        """
        for s in self.get_steps(state=wf_states.RUNNING):
            self.kill_step_calculations(s)
            
            for w in s.get_sub_workflows():
                print "Killing {0}".format(w.uuid)
                w.kill()
        
        self.dbworkflowinstance.set_status(wf_states.FINISHED)
    
    def sleep(self):
        """
        Changes the workflow status to SLEEP, only possible to call from a Workflow step decorated method.
        """
        import inspect
        
        # ATTENTION: Do not move this code outside or encapsulate it in a function
        curframe      = inspect.currentframe()
        calframe      = inspect.getouterframes(curframe, 2)
        caller_method = calframe[1][3]
        
        if not self.has_step(caller_method):
            raise AiidaException("The caller method is either not a step or has not been registered as one")
 
        self.get_step(caller_method).set_status(wf_states.SLEEP)
        
    # ------------------------------------------------------
    #         Report
    # ------------------------------------------------------
    
    def get_report(self):
        """
        Return the Workflow report. 
        
        :note: once, in case the workflow is a subworkflow of any other Workflow this method
          calls the parent ``get_report`` method.
          This is not the case anymore.
        :return: a list of strings 
        """       
#        if len(self.dbworkflowinstance.parent_workflow_step.all())==0:
        return self.dbworkflowinstance.report.splitlines()
#        else:
#            return Workflow.get_subclass_from_uuid(self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).get_report()
    
    def clear_report(self):
        """
        Wipe the Workflow report. In case the workflow is a subworflow of any other Workflow this method
        calls the parent ``clear_report`` method.
        """
        
        if len(self.dbworkflowinstance.parent_workflow_step.all())==0:
            self.dbworkflowinstance.clear_report()
        else:
            Workflow(uuid=self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).clear_report()
            
    
    def append_to_report(self, text):
        """
        Adds text to the Workflow report. 
        
        :note: Once, in case the workflow is a subworkflow of any other Workflow this method
         calls the parent ``append_to_report`` method; now instead this is not the 
         case anymore
        """
        
#        if len(self.dbworkflowinstance.parent_workflow_step.all())==0:
        self.dbworkflowinstance.append_to_report(text)
#        else:
#            Workflow(uuid=self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).append_to_report(text)
        
    # ------------------------------------------------------
    #         Retrieval
    # ------------------------------------------------------
    
    @classmethod
    def get_subclass_from_dbnode(cls, wf_db):
        """
        Loads the workflow object and reaoads the python script in memory with the importlib library, the
        main class is searched and then loaded.
        :param wf_db: a specific DbWorkflowNode object representing the Workflow
        :return: a Workflow subclass from the specific source code
        """
        
        module       = wf_db.module
        module_class = wf_db.module_class
         
        try:
            wf_mod = importlib.import_module(module)
        except ImportError:
            raise InternalError("Unable to load the workflow module {}".format(module))
        
        for elem_name, elem in wf_mod.__dict__.iteritems():
            
            if module_class==elem_name: #and issubclass(elem, Workflow):
                return getattr(wf_mod,elem_name)(uuid=wf_db.uuid)
    
    @classmethod      
    def get_subclass_from_pk(cls,pk):
        """
        Calls the ``get_subclass_from_dbnode`` selecting the DbWorkflowNode from
        the input pk.
        :param pk: a primary key index for the DbWorkflowNode
        :return: a Workflow subclass from the specific source code
        """
        
        from aiida.djsite.db.models import DbWorkflow
        
        try:
            
            dbworkflowinstance    = DbWorkflow.objects.get(pk=pk)
            return cls.get_subclass_from_dbnode(dbworkflowinstance)
                  
        except ObjectDoesNotExist:
            raise NotExistent("No entry with pk= {} found".format(pk))
                           
    @classmethod      
    def get_subclass_from_uuid(cls,uuid):
        """
        Calls the ``get_subclass_from_dbnode`` selecting the DbWorkflowNode from
        the input uuid.
        :param uuid: a uuid for the DbWorkflowNode
        :return: a Workflow subclass from the specific source code
        """
        
        from aiida.djsite.db.models import DbWorkflow
        
        try:
            
            dbworkflowinstance    = DbWorkflow.objects.get(uuid=uuid)
            return cls.get_subclass_from_dbnode(dbworkflowinstance)
                  
        except ObjectDoesNotExist:
            raise NotExistent("No entry with the UUID {} found".format(uuid))
    
    def exit(self):
        """
        This is the method to call in  ``next`` to finish the Workflow. When exit is the next method,
        and no errors are found, the Workflow is set to FINISHED and removed from the execution manager
        duties. 
        """
        pass
    
#     def revive(self):
#         
#         import hashlib
#         md5          = self.dbworkflowinstance.script_md5
#         script_path  = self.dbworkflowinstance.script_path
#         
#         md5_check    = hashlib.md5(script_path).hexdigest()
#         
#         # MD5 Check before revive
#         if not md5==md5_check:
#             logger.info("The script has changed, MD5 is now updated")
#             self.dbworkflowinstance.set_script_md5(md5_check)
#         
#         # Clear all the erroneous steps
#         err_steps    = self.get_steps(state=wf_states.ERROR)
#         for s in err_steps:
#             
#             for w in s.get_sub_workflows(): w.kill()
#             s.remove_sub_workflows()
#             
#             for c in s.get_calculations(): c.kill()
#             s.remove_calculations()
#             
#             s.set_status(wf_states.INITIALIZED)
#             
#         self.set_status(wf_states.RUNNING)
    
# ------------------------------------------------------
#         Module functions for monitor and control
# ------------------------------------------------------

def kill_from_pk(pk):
    """
    Kills a workflow without loading the class, useful when there was a problem
    and the workflow definition module was changed/deleted (and the workflow
    cannot be reloaded).
    
    :param pk: the principal key (id) of the workflow to kill
    """
    try:    
        Workflow.query(pk=pk)[0].kill()
    except IndexError:
        raise NotExistent("No workflow with pk= {} found.".format(pk))
    
def kill_from_uuid(uuid):
    """
    Kills a workflow without loading the class, useful when there was a problem
    and the workflow definition module was changed/deleted (and the workflow
    cannot be reloaded).
    
    :param uuid: the UUID of the workflow to kill
    """
    try:    
        Workflow.query(uuid=uuid)[0].kill()
    except IndexError:
        raise NotExistent("No workflow with uuid={} found.".format(uuid))
    
def kill_all():
    """
    Kills all the workflows not in FINISHED state running the ``kill_from_uuid``
    method in a loop.
    
    :param uuid: the UUID of the workflow to kill
    """
    
    from aiida.djsite.db.models import DbWorkflow
    from django.db.models import Q
    
    q_object = Q(user=get_automatic_user())
    q_object.add(~Q(state=wf_states.FINISHED), Q.AND)
    w_list = DbWorkflow.objects.filter(q_object)
    
    for w in w_list:
        Workflow.get_subclass_from_uuid(w.uuid).kill()
        


def get_workflow_info(w, tab_size = 2, short = False, pre_string = ""):
    """
    Return a string with all the information regarding the given workflow and
    all its calculations and subworkflows.
    
    :param w: a DbWorkflow instance
    :param indent_level: the indentation level of this workflow
    :param tab_size: number of spaces to use for the indentation
    :param short: if True, provide a shorter output (only total number of
        calculations, rather than the status of each calculation)
    """
    from django.utils import timezone
    
    from aiida.common.datastructures import calc_states
    from aiida.common.utils import str_timedelta
    
    if tab_size < 2:
        raise ValueError("tab_size must be > 2")
        
    now = timezone.now()

    lines = []
    

    if w.label:
        wf_labelstring = "'{}', ".format(w.label)
    else:
        wf_labelstring = ""
    
    lines.append(pre_string) # put an empty line before any workflow
    lines.append(pre_string + "+ Workflow {} ({}pk: {}) is {} [{}]".format(
               w.module_class, wf_labelstring, w.pk, w.state, str_timedelta(
                    now-w.ctime, negative_to_zero = True)))

    # order all steps by time
    steps = w.steps.all().order_by('time')

    for idx, s in enumerate(steps):
        lines.append(pre_string + "|"+'-'*(tab_size-1) +
                     "* Step: {0} [->{1}] is {2}".format(
                         s.name,s.nextcall,s.state))

        calcs  = s.get_calculations().order_by('ctime')
        
        # print calculations only if it is not short
        if short:
            lines.append(pre_string + "|" + " "*(tab_size-1) +
                "| [{0} calculations]".format(len(calcs)))
        else:    
            for c in calcs:
                uuid = c.uuid
                pk = c.pk
                calc_state = c.get_state()
                time = c.ctime
                if c.label:
                    labelstring = "'{}', ".format(c.label)
                else:
                    labelstring = ""
                 
                if calc_state == calc_states.WITHSCHEDULER:
                    sched_state = c.get_scheduler_state()
                    if sched_state is None:
                        remote_state = "(remote state still unknown)"
                    else:
                        last_check = c._get_scheduler_lastchecktime()
                        if last_check is not None:
                            when_string = " {}".format(
                               str_timedelta(now-last_check, short=True,
                                             negative_to_zero = True))
                            verb_string = "was "
                        else:
                            when_string = ""
                            verb_string = ""
                        remote_state = " ({}{}{})".format(verb_string,
                            sched_state, when_string)
                else:
                    remote_state = ""
                lines.append(pre_string + "|" + " "*(tab_size-1) +
                             "| Calculation ({}pk: {}) is {}{}".format(
                                 labelstring, pk, calc_state, remote_state))
        ## SubWorkflows
        wflows = s.get_sub_workflows()     
        for subwf in wflows:
            lines.append( get_workflow_info(subwf.dbworkflowinstance,
               short=short, tab_size = tab_size,
               pre_string = pre_string + "|" + " "*(tab_size-1)) ) 
        
        if idx != (len(steps) - 1):
            lines.append(pre_string + "|")

    return "\n".join(lines)
    
def list_workflows(short = False, all_states = False, tab_size = 2,
                   past_days=None, pks=[]):
    """
    This function return a string with a description of the AiiDA workflows.
    
    :param short: if True, provide a shorter output (see documentation of the
        ``short`` parameter of the :py:func:`get_workflow_info` function)
    :param all_states:  if True, print also workflows that have finished.
        Otherwise, hide workflows in the FINISHED and ERROR states.
    :param tab_size: how many spaces to use for indentation of subworkflows
    :param past_days: If specified, show only workflows that were created in
        the given number of past days.
    :param pks: if specified, must be a list of integers, and only workflows
        within that list are shown. Otherwise, all workflows are shown.
        If specified, automatically sets all_states to True and ignores the 
        value of the ``past_days`` option.")
    """
    from aiida.djsite.db.models import DbWorkflow
    
    from django.utils import timezone
    import datetime
    from django.db.models import Q
    
    
    if pks:
        q_object = Q(pk__in=pks)
    else:
        q_object = Q(user=get_automatic_user())
        if not all_states:
            q_object.add(~Q(state=wf_states.FINISHED), Q.AND)
            q_object.add(~Q(state=wf_states.ERROR), Q.AND)
        if past_days:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=past_days)
            q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

    wf_list = DbWorkflow.objects.filter(q_object).order_by('ctime')
    
    lines = []
    for w in wf_list:
        if not w.is_subworkflow():
            lines.append(get_workflow_info(w, tab_size=tab_size, short=short))
    
    # empty line between workflows
    retstring = "\n\n".join(lines)
    if not retstring:
        if all_states:
            retstring = "# No workflows found"
        else:
            retstring = "# No running workflows found"
    return retstring
        
                
    
