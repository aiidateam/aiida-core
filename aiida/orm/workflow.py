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
	
	_logger       = aiida.common.aiidalogger.getChild('workflow')
	
	def __init__(self,**kwargs):

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
						
						self.logger.info("Workflow found in the database, now retrieved")
						
				except ObjectDoesNotExist:
						raise NotExistent("No entry with the UUID {} found".format(uuid))
					
			else:
				
				import inspect
				stack = inspect.stack()
				
				cur_fr  = inspect.currentframe()
				call_fr = inspect.getouterframes(cur_fr, 2)
				stack_frame = stack[1][0]
				
				#print call_fr
				
				caller_module       = inspect.getmodule(inspect.currentframe().f_back)
				caller_module_class = stack_frame.f_locals.get('self', None).__class__
				caller_file         = call_fr[1][1]
				caller_funct        = call_fr[1][3]
				
				
				
				if caller_module == None or not caller_module.__name__.startswith("aiida.workflows"):
						raise ValueError("The superclass can't be called directly")
				
				self.caller_module = caller_module.__name__
				self.caller_module_class  = caller_module_class.__name__
				self.caller_file   = caller_file
				self.caller_funct  = caller_funct
				
				self.store()
				
	
	@property
	def logger(self):
		return self._logger
		
	def store(self):

		from aiida.djsite.db.models import DbWorkflow
		import hashlib
		
		
		
		self.dbworkflowinstance = DbWorkflow.objects.create(user=get_automatic_user(),
														module = self.caller_module,
														module_class = self.caller_module_class,
														script_path = self.caller_file,
														script_md5 = hashlib.md5(self.caller_file).hexdigest()
														)
		
				
	@classmethod
	def query(cls,**kwargs):
				
		from aiida.djsite.db.models import DbWorkflow
		return DbWorkflow.objects.filter(**kwargs)

	def info(self):
		
		return [self.dbworkflowinstance.module,
			self.dbworkflowinstance.module_class, 
			self.dbworkflowinstance.script_path,
			self.dbworkflowinstance.script_md5,
			self.dbworkflowinstance.time,
			self.dbworkflowinstance.status]
	#
	# Steps
	#
	
	def set_params(self, params):
		
		self.params = params
		self.dbworkflowinstance.add_parameters(self.params)
	
	def get_parameters(self):
		
		return self.dbworkflowinstance.get_parameters()

	def get_step(self,method):

		if isinstance(method, basestring):
			method_name = method
		else:
			method_name = method.__name__
		
		if (method_name==WF_STEP_EXIT):
			raise InternalError("Cannot query a step with name {}, reserved string".format(method_name))    		
	
		step, created = self.dbworkflowinstance.steps.get_or_create(name=method_name, user=get_automatic_user())
		return step

	def list_steps(self):

		try:
				return self.dbworkflowinstance.steps.all()
		except ObjectDoesNotExist:
				raise AttributeError("No steps found for the workflow")
	
	def add_calculation(self, calc):
		
		from aiida.orm import Calculation
		from celery.task import task
		from aiida.djsite.db import tasks

		import inspect

		if (not isinstance(calc,Calculation)):
			raise AiidaException("Cannot add a calculation not of type Calculation")    					

		curframe = inspect.currentframe()
		calframe = inspect.getouterframes(curframe, 2)
		caller_funct = calframe[1][3]

		self.get_step(caller_funct).add_calculation(calc)
		
	def next(self, method):
		
		if isinstance(method, basestring):
			method_name = method
		else:
			method_name = method.__name__
			
		import inspect
		from aiida.common.datastructures import wf_start_call, wf_states, wf_exit_call

		curframe = inspect.currentframe()
		calframe = inspect.getouterframes(curframe, 2)
		caller_funct = calframe[1][3]
		
		self.get_step(caller_funct).set_nextcall(method_name)
		
		if (caller_funct==wf_start_call):
			self.dbworkflowinstance.set_status(wf_states.RUNNING)

		
	def get_calculations(self, method):
		
		if isinstance(method, basestring):
			method_name = method
		else:
			method_name = method.__name__
		
		try:
			return self.dbworkflowinstance.steps.get(name=method_name).get_calculations()
		except:
			raise AiidaException("Cannot retrive step's calculations")

	def run_method(self, method):
		
		if isinstance(method, basestring):
			method_name = method
		else:
			method_name = method.__name__
			
	 	module = self.dbworkflowinstance.module
	 	module_class = self.dbworkflowinstance.module_class
	 	
	 	try:
	 		wf_mod = importlib.import_module(module)
	 	except ImportError:
	 		raise NotExistent("Unable to load the workflow module {}".format(module))
	 
	 	for elem_name, elem in wf_mod.__dict__.iteritems():
	 		
	 		print "Element: {0}".format(elem_name)
	 		
	 		if module_class==elem_name and issubclass(elem, self.__class__):
	 			print "Found new subclass {0} of {1}".format(elem, self.__class__)
	 			
	
	def finish_step_calculations(self, stepname):
	
		from aiida.common.datastructures import calc_states
		
		for c in self.dbworkflowinstance.steps.get(name=stepname).get_calculations():
			c._set_state(calc_states.RETRIEVED)
			
	def start(self,*args,**kwargs):
		pass

	def exit(self):
		pass
#
#
#

def list_workflows(expired=False):
	
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
		
		if expired:
			steps = w.steps.all()
		else:
			steps = w.steps.filter(status=wf_states.RUNNING)
			
		for s in steps:
			print "- Running step: {0} [{1}] -> {2}".format(s.name,s.status, s.nextcall)
			
			calcs = s.get_calculations().filter(attributes__key="_state").values_list("uuid", "time", "attributes__tval")
			
			for c in calcs:
				print "   Calculation {0} started at {1} is {2}".format(c[0], c[1], c[2])

#
#
#

def retrieve(wf_db):
	
	from aiida.djsite.db.models import DbWorkflow
	import importlib
	
	module       = wf_db.module
 	module_class = wf_db.module_class
 	
 	try:
 		wf_mod = importlib.import_module(module)
 	except ImportError:
 		raise NotExistent("Unable to load the workflow module {}".format(module))
 
 	for elem_name, elem in wf_mod.__dict__.iteritems():
 		#print "Element: {0} - {1}".format(elem_name,module_class)
 		if module_class==elem_name: #and issubclass(elem, Workflow):
 			#print "Found new subclass {0} of {1}".format(elem, Workflow)
 			
 			return  getattr(wf_mod,elem_name)(uuid=wf_db.uuid)
						
			
def retrieve_by_uuid(uuid):
	
	from aiida.djsite.db.models import DbWorkflow
	
	try:
		
		dbworkflowinstance    = DbWorkflow.objects.get(uuid=uuid)
		return  retrieve(dbworkflowinstance)
		 	 
	except ObjectDoesNotExist:
		raise NotExistent("No entry with the UUID {} found".format(uuid))
						
