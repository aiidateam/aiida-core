from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import User

from django.db.models.query import QuerySet

from aiida.common.exceptions import (
    ConfigurationError, DbContentError, MissingPluginError)

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
      A is 'input' of C.
      C is 'output' of A. 
      A is 'parent' of B,C
      C,B are 'children' of A.

    FINAL DECISION:
    All attributes are stored in the Attribute table.
    * internal attributes (that are used by the Data subclass and similar) are stored
      starting with an underscore.
      These (internal) attributes cannot be changed except when defining the object
      the first time.
    * other attributes MUST start WITHOUT an underscore. These are user-defined and
      can be appended even after the calculation has run, since they just are metadata.
    * There is no json metadata attached to the DbNode entries. This can go into an attribute if needed.
    * Attributes in the Attribute table have to be thought as belonging to the DbNode,
      and this is the reason for which there is no 'user' field in the Attribute field.
    * For a Data node, attributes will /define/ the data and hence should be immutable.
      User-defined attributes are metadata for convenience of tagging and searching only.
      User should be careful not to attach data computed from data as metadata. 
    '''
    uuid = UUIDField(auto=True)
    # in the form data.upffile, data.structure, calculation, code.quantumespresso.pw, ...
    # max_length required for index by MySql
    type = m.CharField(max_length=255,db_index=True) 
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    time = m.DateTimeField(auto_now_add=True, editable=False)
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
    label = m.CharField(max_length=255, db_index=True, blank=True)

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
    key = m.CharField(max_length=255,db_index=True)
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
    """Table of computers or clusters.

    # TODO: understand if we want that this becomes simply another type of dbnode.

    Attributes:
        name: A name to be used to refer to this computer. Must be unique.
        hostname: Fully-qualified hostname of the host
        workdir: Full path of the aiida folder on the host. It can contain
            the string {username} that will be substituted by the username
            of the user on that machine.
            The actual workdir is then obtained as
            workdir.format(username=THE_ACTUAL_USERNAME)
            Example: 
            workdir = "/scratch/{username}/aiida/"
        transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:
        - mpirun command
        - num cores per node
        - max num cores
        - allocate full node = True or False
        - ... (further limits per user etc.)
    """
    uuid = UUIDField(auto=True)
    name = m.CharField(max_length=255, unique=True)
    hostname = m.CharField(max_length=255)
    description = m.TextField(blank=True)
    # TODO: next three fields should not be blank...
    workdir = m.CharField(max_length=255)
    transport_type = m.CharField(max_length=255)
    scheduler_type = m.CharField(max_length=255)
    transport_params = m.TextField(default="{}") # Will store a json

    metadata = m.TextField(default="{}") # Will store a json

    @classmethod
    def get_dbcomputer(cls,computer):
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Computer

        if isinstance(computer, basestring):
            try:
                dbcomputer = DbComputer.objects.get(hostname=computer)
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


#
# Workflows
#

#WF_RUNNING +
#workflow_step_exit = "wf_exit"
#workflow_status = (('running', 'running'),
#    ('finished', 'finished'),
#)

# class DbWorkflow(m.Model):
#     
#     uuid        = UUIDField(auto=True)
#     time        = m.DateTimeField(auto_now_add=True, editable=False)
#     name        = m.CharField(max_length=255, editable=False, blank=False, unique=True)
#     version     = m.IntegerField()
#     user        = m.ForeignKey(User, on_delete=m.PROTECT)
#     comment     = m.TextField(blank=True)  
#     repo_folder = m.CharField(max_length=255)

class DbWorkflow(m.Model):
    
    from aiida.common.datastructures import wf_states
    
    uuid         = UUIDField(auto=True)
    time         = m.DateTimeField(auto_now_add=True, editable=False)
    user         = m.ForeignKey(User, on_delete=m.PROTECT)
    # File variables, script is the complete dump of the workflow python script
    module       = m.TextField(blank=False)
    module_class = m.TextField(blank=False)
    script_path  = m.TextField(blank=False)
    script_md5   = m.CharField(max_length=255, blank=False)
    
    status       = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.RUNNING)
    
    def set_status(self, _status):
        
        self.status = _status;
        self.save()
        
    def add_parameters(self, dict):
        
        import json
        try:
            
            for k in dict.keys():            
                p = DbWorkflowParameters.objects.create(workflow=self,name = k, value = json.dumps(dict[k]))
                self.params.add(p)
                
        except:
            raise ValueError("Error adding parameters")
        
    def get_parameters(self):
        
        try:
            dict = {}
            for p in DbWorkflowParameters.objects.filter(workflow=self):
                dict[p.name] = p.deserialize()
            return dict
        except:
            raise ValueError("Error retrieving parameters")
    
    def get_calculations(self):
        
        from aiida.orm import Calculation
        return Calculation.query(steps=self.steps)

    def finish(self):
        self.status = 'finished'

        
class DbWorkflowParameters(m.Model):

    workflow     = m.ForeignKey(DbWorkflow, related_name='params')
    name         = m.CharField(max_length=255, blank=False)
    time         = m.DateTimeField(auto_now_add=True, editable=False)
    value        = m.TextField(blank=False)

    class Meta:
        unique_together = (("workflow", "name"))

    def deserialize(self):
        
        import json
        try:
            return json.loads(self.value)
        except:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))
        
        
class DbWorkflowStep(m.Model):

    from aiida.common.datastructures import wf_states, wf_exit_call
    
    workflow     = m.ForeignKey(DbWorkflow, related_name='steps')
    name         = m.CharField(max_length=255, blank=False)
    user         = m.ForeignKey(User, on_delete=m.PROTECT)
    time         = m.DateTimeField(auto_now_add=True, editable=False)
    nextcall     = m.CharField(max_length=255, blank=False, default=wf_exit_call)
    calculations = m.ManyToManyField('DbNode', symmetrical=False, related_name="steps")
    status       = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.RUNNING)

    class Meta:
        unique_together = (("workflow", "name"))


    def add_calculation(self, step_calculation):
        
        from aiida.orm import Calculation

        if (not isinstance(step_calculation, Calculation)):
            raise ValueError("Cannot add a non-Calculation object to a workflow step")          

        try:
            self.calculations.add(step_calculation)
        except:
            raise ValueError("Error adding calculation to step")                      

    def get_calculations(self):
        
        from aiida.orm import Calculation
        
        return Calculation.query(steps=self)#pk__in = step.calculations.values_list("pk", flat=True))

    def get_calculations_status(self, extended=False):

        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call

        calc_status = self.calculations.filter(attributes__key="_state").values_list("uuid", "attributes__tval")
        if (extended):
            for c in calc_status:
                print "Calculation {0} is {1}".format(c[0], c[1])
                
        s = set([l[1] for l in calc_status])
        if len(s)==1 and calc_states.RETRIEVED in s:
            return wf_states.FINISHED
        else: 
            return wf_states.RUNNING
    
    def is_finished(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        
        return self.status==wf_states.FINISHED
        
    def set_nextcall(self, _nextcall):
        
        self.nextcall = _nextcall;
        self.save()
        
    def set_status(self, _status):
        
        self.status = _status;
        self.save()
