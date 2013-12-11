from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import User

from django.db.models.query import QuerySet

from aiida.common.exceptions import (
    ConfigurationError, DbContentError, MissingPluginError, InternalError)

# Removed the custom User field, that was creating a lot of problems. Use
# the email as UUID. In case we need it, we can do a couple of south migrations
# to create the new table. See for instance
# http://stackoverflow.com/questions/14904046/

class AiidaQuerySet(QuerySet):
    def iterator(self):
        for obj in super(AiidaQuerySet, self).iterator():
            yield obj.get_aiida_class()

class AiidaObjectManager(m.Manager):
    def get_query_set(self):
        return AiidaQuerySet(self.model, using=self._db)
            
class DbNode(m.Model):
    '''
    Generic node: data or calculation (or code - tbd). There will be several types of connections.
    Naming convention (NOT FINAL): A --> C --> B. 

    * A is 'input' of C.

    * C is 'output' of A. 

    * A is 'parent' of B,C

    * C,B are 'children' of A.

    FINAL DECISION:
    All attributes are stored in the Attribute table.

    * internal attributes (that are used by the Data subclass and similar) are stored\
      starting with an underscore.\
      These (internal) attributes cannot be changed except when defining the object\
      the first time.

    * other attributes MUST start WITHOUT an underscore. These are user-defined and\
      can be appended even after the calculation has run, since they just are metadata.

    * There is no json metadata attached to the DbNode entries. This can go into an attribute if needed.

    * Attributes in the Attribute table have to be thought as belonging to the DbNode,\
      and this is the reason for which there is no 'user' field in the Attribute field.

    * For a Data node, attributes will /define/ the data and hence should be immutable.\
      User-defined attributes are metadata for convenience of tagging and searching only.\
      User should be careful not to attach data computed from data as metadata. 
    '''
    uuid = UUIDField(auto=True)
    # in the form data.upffile., data.structure., calculation., code.quantumespresso.pw., ...
    # Note that there is always a final dot, to allow to do queries of the
    # type (type__startswith="calculation.") and avoid problems with classes
    # starting with the same string
    # max_length required for index by MySql
    type = m.CharField(max_length=255,db_index=True) 
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    # creation time
    ctime = m.DateTimeField(auto_now_add=True, editable=False)
    # last-modified time
    mtime = m.DateTimeField(auto_now=True, editable=False)
    # Cannot delete a user if something is associated to it
    user = m.ForeignKey(User, on_delete=m.PROTECT)

    # Direct links
    outputs = m.ManyToManyField('self', symmetrical=False, related_name='inputs', through='Link')  
    # Transitive closure
    children = m.ManyToManyField('self', symmetrical=False, related_name='parents', through='Path')
    
    # Used only if dbnode is a calculation, or remotedata
    computer = m.ForeignKey('DbComputer', null=True, on_delete=m.PROTECT)

    # Index that is incremented every time a modification is done on itself or on attributes.
    # Managed by the aiida.orm.Node class. Do not modify
    nodeversion = m.IntegerField(default=1,editable=False)
    # Index that keeps track of the last time the node was updated to the remote aiida instance.
    # Zero means that it was never stored, so also files need to be udpated.
    # When this number is > 0, only attributes and not files will be uploaded to the remote aiida
    # instance.
    # Managed by the aiida.orm.Node class. Do not modify
    lastsyncedversion = m.IntegerField(default=0,editable=False)

    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()
    
    def get_aiida_class(self):
        """
        Return the corresponding aiida instance of class aiida.orm.Node or a
        appropriate subclass.
        """
        from aiida.orm import Node
        from aiida.common.pluginloader import load_plugin
        from aiida.common import aiidalogger

        thistype = self.type
        # Fix for base class
        if thistype == "":
            thistype = "node.Node."
        if not thistype.endswith("."):
            raise DbContentError("The type name of node with pk={} is "
                                "not valid: '{}'".format(self.pk, self.type))
        thistype = thistype[:-1] # Strip final dot

        try:
            PluginClass = load_plugin(Node, 'aiida.orm', thistype)
        except MissingPluginError:
            aiidalogger.error("Unable to find plugin for type '{}' (node={}), "
                "will use base Node class".format(self.type,self.pk))
            PluginClass = Node

        return PluginClass(uuid=self.uuid)
            

class Link(m.Model):
    '''
    Direct connection between two dbnodes. The label is identifying the
    link type.
    '''
    input = m.ForeignKey('DbNode',related_name='output_links')
    output = m.ForeignKey('DbNode',related_name='input_links')
    #label for data input for calculation
    label = m.CharField(max_length=255, db_index=True, blank=False)

    class Meta:
        # I cannot add twice the same link
        # I want unique labels among all inputs of a node
        # NOTE!
        # I cannot add ('input', 'label') because in general
        # if the input is a 'data' and I want to add it more than
        # once to different calculations, the different links must be
        # allowed to have the same name. For calculations, it is the
        # rensponsibility of the output plugin to avoid to have many
        # times the same name.
        unique_together = (("input",  "output"),
                           ("output", "label"),
                           )
    

class Path(m.Model):
    """
    Transitive closure table for all dbnode paths.
    
    # TODO: implement Transitive closure with MySql!
    # TODO: if a link is updated, the TC should be updated accordingly
    """
    parent = m.ForeignKey('DbNode',related_name='child_paths',editable=False)
    child = m.ForeignKey('DbNode',related_name='parent_paths',editable=False)
    depth = m.IntegerField(editable=False)

    # Used to delete
    entry_edge_id = m.IntegerField(null=True,editable=False)
    direct_edge_id = m.IntegerField(null=True,editable=False)
    exit_edge_id = m.IntegerField(null=True,editable=False)

attrdatatype_choice = (
    ('float', 'float'),
    ('int', 'int'),
    ('txt', 'txt'),
    ('bool', 'bool'),
    ('date', 'date'),
    ('json', 'json'))

class Attribute(m.Model):
    '''
    Attributes are annotations ONLY for storing metadata and tagging. This is only for
    querying convenience.
    Actual input and output data should never go here, only duplicates and comments.
    '''
    time = m.DateTimeField(auto_now_add=True, editable=False)
    dbnode = m.ForeignKey('DbNode', related_name='attributes')
    # max_length is required by MySql to have indexes and unique constraints
    key = m.CharField(max_length=255,db_index=True,blank=False)
    datatype = m.CharField(max_length=10, choices=attrdatatype_choice, db_index=True)
    tval = m.TextField( default='', blank=True)
    fval = m.FloatField( default=None, null=True)
    ival = m.IntegerField( default=None, null=True)
    bval = m.NullBooleanField(default=None, null=True)
    dval = m.DateTimeField(default=None, null=True)

    class Meta:
        unique_together = (("dbnode", "key"))
        
    def setvalue(self,value):
        """
        This can be called on a given row and will set the corresponding value.
        """
        import json
        import datetime 
        from django.utils.timezone import is_naive, make_aware, get_current_timezone
        
        if isinstance(value,bool):
            self.datatype = 'bool'
            self.bval = value
            self.tval = ''
            self.ival = None
            self.fval = None
            self.dval = None

        elif isinstance(value,int):
            self.datatype = 'int'
            self.ival = value
            self.tval = ''
            self.bval = None
            self.fval = None
            self.dval = None

        elif isinstance(value,float):
            self.datatype = 'float'
            self.fval = value
            self.tval = ''
            self.ival = None
            self.bval = None
            self.dval = None

        elif isinstance(value,basestring):
            self.datatype = 'txt'
            self.tval = value
            self.bval = None
            self.ival = None
            self.fval = None
            self.dval = None

        elif isinstance(value,datetime.datetime):

            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value,get_current_timezone())
            else:
                value_to_set = value

            self.datatype = 'date'
            # TODO: time-aware and time-naive datetime objects, see
            # https://docs.djangoproject.com/en/dev/topics/i18n/timezones/#naive-and-aware-datetime-objects
            self.dval = value_to_set
            self.tval = ''
            self.bval = None
            self.ival = None
            self.fval = None

        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError("Unable to store the value: it must be either "
                                 "a basic datatype, or json-serializable")
            
            self.datatype = 'json'
            self.tval = jsondata
            self.bval = None
            self.ival = None
            self.fval = None
        
        self.save()       
        
    def getvalue(self):
        """
        This can be called on a given row and will get the corresponding value,
        casting it correctly
        """
        import json
        from django.utils.timezone import is_naive, make_aware, get_current_timezone

        if self.datatype == 'bool':
            return self.bval
        elif self.datatype == 'int':
            return self.ival
        elif self.datatype == 'float':
            return self.fval
        elif self.datatype == 'txt':
            return self.tval
        elif self.datatype == 'date':
            if is_naive(self.dval):
                return make_aware(self.dval,get_current_timezone())
            else:
                return self.dval
            return self.dval
        elif self.datatype == 'json':
            try:
                return json.loads(self.tval)
            except ValueError:
                raise DbContentError("Error in the content of the json field")
        else:
            raise DbContentError("The type field '{}' is not recognized".format(
                    self.datatype))        


class Group(m.Model):
    uuid = UUIDField(auto=True)
    # max_length is required by MySql to have indexes and unique constraints
    name = m.CharField(max_length=255,unique=True, db_index=True)
    dbnodes = m.ManyToManyField('DbNode', related_name='groups')
    time = m.DateTimeField(auto_now_add=True, editable=False)
    description = m.TextField(blank=True)
    user = m.ForeignKey(User)  # The owner of the group, not of the calculations

class DbComputer(m.Model):
    """
    Table of computers or clusters.

    Attributes:
    * name: A name to be used to refer to this computer. Must be unique.
    * hostname: Fully-qualified hostname of the host
    * workdir: Full path of the aiida folder on the host. It can contain\
            the string {username} that will be substituted by the username\
            of the user on that machine.\
            The actual workdir is then obtained as\
            workdir.format(username=THE_ACTUAL_USERNAME)\
            Example: \
            workdir = "/scratch/{username}/aiida/"
    * transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:

        * mpirun command

        * num cores per node

        * max num cores

        * allocate full node = True or False

        * ... (further limits per user etc.)

    """
    #TODO: understand if we want that this becomes simply another type of dbnode.

    uuid = UUIDField(auto=True)
    name = m.CharField(max_length=255, unique=True, blank=False)
    hostname = m.CharField(max_length=255)
    description = m.TextField(blank=True)
    enabled = m.BooleanField(default=True)
    # TODO: next three fields should not be blank...
    workdir = m.CharField(max_length=255)
    transport_type = m.CharField(max_length=255)
    scheduler_type = m.CharField(max_length=255)
    transport_params = m.TextField(default="{}") # Will store a json
    metadata = m.TextField(default="{}") # Will store a json

    @classmethod
    def get_dbcomputer(cls,computer):
        """
        Return a DbComputer from its name (or from another Computer or DbComputer instance)
        """
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Computer

        if isinstance(computer, basestring):
            try:
                dbcomputer = DbComputer.objects.get(name=computer)
            except ObjectDoesNotExist:
                raise NotExistent("No computer found in the table of computers with "
                                 "the given name '{}'".format(computer))
            except MultipleObjectsReturned:
                raise DbContentError("There is more than one computer with name '{}', "
                                     "pass a Django Computer instance".format(computer))
        elif isinstance(computer, DbComputer):
            if computer.pk is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer
        elif isinstance(computer,Computer):
            if computer.dbcomputer.pk is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer.dbcomputer
        else:
            raise TypeError("Pass either a computer name, a DbComputer django instance or a Computer object")
        return dbcomputer

#class RunningJob(m.Model):
#    calc = m.OneToOneField(DbNode,related_name='jobinfo') # OneToOneField implicitly sets unique=True
#    calc_state = m.CharField(max_length=64)
#    job_id = m.TextField(blank=True)
#    scheduler_state = m.CharField(max_length=64,blank=True)
#    # Will store a json of the last JobInfo got from the scheduler
#    last_jobinfo = m.TextField(default='{}')  

class AuthInfo(m.Model):
    """
    Table that pairs aiida users and computers, with all required authentication
    information.
    """
    aiidauser = m.ForeignKey(User)
    computer = m.ForeignKey(DbComputer)
    auth_params = m.TextField(default='{}') # Will store a json; contains mainly the remoteuser
                                            # and the private_key

    class Meta:
        unique_together = (("aiidauser", "computer"),)

    def get_auth_params(self):
        import json
        try:
            return json.loads(self.auth_params)
        except ValueError:
            raise DbContentError(
                "Error while reading auth_params for authinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.username, self.computer.hostname))

    def set_auth_params(self,auth_params):
        import json
        
        # Raises ValueError if data is not JSON-serializable
        self.auth_params = json.dumps(auth_params)

    # a method of AuthInfo
    def get_transport(self):
        """
        Given a computer and an aiida user (as entries of the DB) return a configured
        transport to connect to the computer.
        """    
        from aiida.transport import TransportFactory
        from aiida.orm import Computer

        try:
            ThisTransport = TransportFactory(self.computer.transport_type)
        except MissingPluginError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.computer.hostname, self.computer.transport_type, e.message))

        params = dict(Computer(dbcomputer=self.computer).get_transport_params().items() +
                      self.get_auth_params().items())
        return ThisTransport(machine=self.computer.hostname,**params)

class Comment(m.Model):
    dbnode = m.ForeignKey(DbNode,related_name='comments')
    time = m.DateTimeField(auto_now_add=True, editable=False)
    user = m.ForeignKey(User)
    content = m.TextField(blank=True)

#-------------------------------------
#         Lock
#-------------------------------------

class DbLock(m.Model):
    
    key        = m.TextField(primary_key=True)
    creation   = m.DateTimeField(auto_now_add=True, editable=False)
    timeout    = m.IntegerField(editable=False)
    owner      = m.CharField(max_length=255, blank=False)
            
#-------------------------------------
#         Workflows
#-------------------------------------

        
        
class DbWorkflow(m.Model):
    
    from aiida.common.datastructures import wf_states, wf_data_types
    
    uuid         = UUIDField(auto=True)
    time         = m.DateTimeField(auto_now_add=True, editable=False)
    user         = m.ForeignKey(User, on_delete=m.PROTECT)
    report       = m.TextField(blank=True)
    
    # File variables, script is the complete dump of the workflow python script
    module       = m.TextField(blank=False)
    module_class = m.TextField(blank=False)
    script_path  = m.TextField(blank=False)
    script_md5   = m.CharField(max_length=255, blank=False)
    
    status       = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.INITIALIZED)
    
    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()
    
    def get_aiida_class(self):
        
        """
        Return the corresponding aiida instance of class aiida.worflow
        """
        from aiida.orm.workflow import Workflow
        return Workflow(uuid=self.uuid)
    
    #  ------------------------------------------------
    
    def set_status(self, _status):
        
        self.status = _status;
        self.save()
    
    def set_script_md5(self, _md5):
        
        self.script_md5 = _md5
        self.save()
        
    # ------------------------------------------------
    #     Get data
    # ------------------------------------------------
        
    def add_data(self, dict, d_type):
        
        from django.db import transaction
        from aiida.common.datastructures import wf_states, wf_data_types
        
#         sid = transaction.savepoint()
        try:

            for k in dict.keys():
                p, create = self.data.get_or_create(name = k, data_type=d_type)
                p.set_value(dict[k])
                
#             transaction.savepoint_commit(sid)
            
        except:
            
#             transaction.savepoint_rollback(sid)
            raise ValueError("Error adding parameters")
    
    def get_data(self, d_type):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        
        try:
            dict = {}
            for p in self.data.filter(parent=self, data_type=d_type):
                dict[p.name] = p.get_value()
            return dict
        except:
            raise ValueError("Error retrieving parameters")
    
        
    # ------------------------------------------------
    #     Parameters, attributes, results
    # ------------------------------------------------

    def add_parameters(self, dict, force=False):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        
        if not self.status == wf_states.INITIALIZED and not force:
            raise ValueError("Cannot add initial parameters to an already initialized workflow")
        
        self.add_data(dict, wf_data_types.PARAMETER)
        
    def add_parameter(self, name, value):
        
        self.add_parameters({name:value})
        
        
    def get_parameters(self):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        return self.get_data(wf_data_types.PARAMETER)
    
    def get_parameter(self, name):
        
        res = self.get_parameters()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))
        
    # ------------------------------------------------
    
    def add_results(self, dict):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        self.add_data(dict, wf_data_types.RESULT)
        
    def add_result(self, name, value):
        
        self.add_results({name:value})
        
        
    def get_results(self):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        return self.get_data(wf_data_types.RESULT)
    
    def get_result(self, name):
        
        res = self.get_results()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))
    
    # ------------------------------------------------
    
    def add_attributes(self, dict):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        self.add_data(dict, wf_data_types.ATTRIBUTE)
        
    def add_attribute(self, name, value):
        
        self.add_attributes({name:value})
        
        
    def get_attributes(self):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        return self.get_data(wf_data_types.ATTRIBUTE)
    
    def get_attribute(self, name):
        
        res = self.get_attributes()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))
          
    # ------------------------------------------------
    #     Reporting
    # ------------------------------------------------

    def clear_report(self):
        
        self.report = None
        self.save()
    
    def append_to_report(self, _text):
        
        from django.utils.timezone import utc
        import datetime
        
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.report += str(now)+"] "+_text+"\n";
        self.save()

    # ------------------------------------------------
    #     Calculations
    # ------------------------------------------------
            
    def get_calculations(self):
        
        from aiida.orm import Calculation
        return Calculation.query(workflow_step=self.steps)
    
    def get_calculations_status(self):

        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call

        calc_status = self.get_calculations().filter(attributes__key="_state").values_list("uuid", "attributes__tval")
        return set([l[1] for l in calc_status])

    # ------------------------------------------------
    #     Subworkflows
    # ------------------------------------------------
    
    def get_sub_workflows(self):
        
        from aiida.orm import Calculation
        return DbWorkflow.objects.filter(parent_workflow_step=self.steps.all())
    
            
    def finish(self):
        self.status = 'finished'


class DbWorkflowData(m.Model):
    
    from aiida.common.datastructures import wf_data_types, wf_data_value_types
    
    parent       = m.ForeignKey(DbWorkflow, related_name='data')
    name         = m.CharField(max_length=255, blank=False)
    time         = m.DateTimeField(auto_now_add=True, editable=False)
    data_type    = m.TextField(blank=False, default=wf_data_types.PARAMETER)
    
    value_type   = m.TextField(blank=False, default=wf_data_value_types.NONE)
    json_value   = m.TextField(blank=True)
    aiida_obj    = m.ForeignKey(DbNode, blank=True, null=True)
    
    class Meta:
        unique_together = (("parent", "name", "data_type"))
        
    def set_value(self, arg):
        
        import inspect
        from aiida.orm.node import Node
        from aiida.common.datastructures import wf_data_types, wf_data_value_types
        import json
        
        try:
            
            if isinstance(arg, Node) or issubclass(arg.__class__, Node):
                
                self.aiida_obj  = arg.dbnode
                self.value_type = wf_data_value_types.AIIDA
                self.save()
            else:
                
                self.json_value = json.dumps(arg)
                self.value_type = wf_data_value_types.JSON
                self.save()
                
        except:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))
        
    def get_value(self):
        
        import json
        from aiida.common.datastructures import wf_data_types, wf_data_value_types
        
        if self.value_type==wf_data_value_types.JSON:
            return json.loads(self.json_value)
        elif self.value_type==wf_data_value_types.AIIDA:
            return self.aiida_obj.get_aiida_class()
        elif self.value_type==wf_data_value_types.NONE:
            return None
        else:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))
        
           
class DbWorkflowStep(m.Model):

    from aiida.common.datastructures import wf_states, wf_exit_call, wf_default_call
    
    parent        = m.ForeignKey(DbWorkflow, related_name='steps')
    name          = m.CharField(max_length=255, blank=False)
    user          = m.ForeignKey(User, on_delete=m.PROTECT)
    time          = m.DateTimeField(auto_now_add=True, editable=False)
    nextcall      = m.CharField(max_length=255, blank=False, default=wf_default_call)
    
    calculations  = m.ManyToManyField(DbNode, symmetrical=False, related_name="workflow_step")
    sub_workflows = m.ManyToManyField(DbWorkflow, symmetrical=False, related_name="parent_workflow_step")
    
    
    status        = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.CREATED)

    class Meta:
        unique_together = (("parent", "name"))


    # ---------------------------------
    #    Calculations
    # ---------------------------------
    
    def add_calculation(self, step_calculation):
        
        from aiida.orm import Calculation

        if (not isinstance(step_calculation, Calculation)):
            raise ValueError("Cannot add a non-Calculation object to a workflow step")          

        try:
            self.calculations.add(step_calculation)
        except:
            raise ValueError("Error adding calculation to step")                      

    def get_calculations(self, state=None):
        
        from aiida.orm import Calculation
        
        if (state==None):
            return Calculation.query(workflow_step=self)#pk__in = step.calculations.values_list("pk", flat=True))
        else:
            return Calculation.query(workflow_step=self).filter(attributes__key="_state",attributes__tval=state)

    def get_calculations_status(self):

        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call

        calc_status = self.calculations.filter(attributes__key="_state").values_list("uuid", "attributes__tval")
        return set([l[1] for l in calc_status])
    
    def remove_calculations(self):
        
        self.calculations.all().delete()
        
    # ---------------------------------
    #    Subworkflows
    # ---------------------------------

    def add_sub_workflow(self, sub_wf):
        
        from aiida.orm.workflow import Workflow
        
        if (not issubclass(sub_wf.__class__,Workflow) and not isinstance(sub_wf, Workflow)):
            raise ValueError("Cannot add a workflow not of type Workflow")                        

        try:
            self.sub_workflows.add(sub_wf.dbworkflowinstance)
        except:
            raise ValueError("Error adding calculation to step")                      
 
    def get_sub_workflows(self):
        
        from aiida.orm.workflow import Workflow
        return Workflow.query(uuid__in=self.sub_workflows.values_list("uuid", flat=True))
        #return self.sub_workflows.all()#pk__in = step.calculations.values_list("pk", flat=True))
 
    def get_sub_workflows_status(self):
        
        from aiida.common.datastructures import wf_states
        
        wf_status = self.sub_workflows.all().values_list("uuid", "status")
        return set([l[1] for l in wf_status])
    
    def remove_sub_workflows(self):
        
        self.sub_workflows.all().delete()
    
    # ---------------------------------
    #    Management
    # ---------------------------------

    def is_finished(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        
        return self.status==wf_states.FINISHED
        
    def set_nextcall(self, _nextcall):
        
        self.nextcall = _nextcall;
        self.save()
        
    def set_status(self, _status):
        
        self.status = _status;
        self.save()
        
    def reinitialize(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        self.set_status(wf_states.INITIALIZED)

    def finish(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        self.set_status(wf_states.FINISHED)
