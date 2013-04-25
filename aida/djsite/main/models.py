import getpass
import os

from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import User

from aida.djsite.settings.settings import LOCAL_REPOSITORY
from aida.common.exceptions import DBContentError

# Removed the custom User field, that was creating a lot of problems. Use
# the email as UUID. In case we need it, we can do a couple of south migrations
# to create the new table. See for instance
# http://stackoverflow.com/questions/14904046/
            
class Node(m.Model):
    '''
    Generic node: data or calculation or code. There will be several types of connections.
    Naming convention: A --> C --> B. 
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
    * There is no json metadata attached to the Node entries.
    * Attributes in the Attribute table have to be thought as belonging to the Node,
      and this is the reason for which there is no 'user' field in the Attribute field.
    '''
    uuid = UUIDField(auto=True)
    # in the form data.upffile, data.structure, calculation, code.quantumespresso.pw, ...
    type = m.TextField(db_index=True) 
    label = m.TextField(db_index=True, blank=True)
    description = m.TextField(blank=True)
    time = m.DateTimeField(auto_now_add=True, editable=False)
    user = m.ForeignKey(User)

    # Direct links
    outputs = m.ManyToManyField('self', symmetrical=False, related_name='inputs', through='Link')  
    # Transitive closure
    children = m.ManyToManyField('self', symmetrical=False, related_name='parents', through='Path')
    
    # Used only if node is a calculation
    computer = m.ForeignKey('Computer', null=True)  # only for calculations
    


class Link(m.Model):
    '''
    Direct connection between two nodes. The label is identifying the link type.
    '''
    input = m.ForeignKey('Node',related_name='output_links')
    output = m.ForeignKey('Node',related_name='input_links')
    #label for data input for calculation
    label = m.CharField(max_length=255, db_index=True, blank=True)

    # a field to choose if this link is considered to build a transitive
    # closure or not

    # TODO: implement deletion from TC table
    # TODO: implement triggers on TC on UPDATE

    # TODO: remember to choose hierarchical names for types of nodes,
    #       starting with calculation. data. or code.
    # This depends on how workflow objects are implemented
    
    include_in_tc = m.BooleanField()

    
    # TODO: I also want to check some more logic e.g. to avoid having
    #       two calculations as input of a data object.
    def save(self):
        if self.pk is None:
            if ((self.input.type.startswith('calculation') or
                 self.input.type.startswith('data')) and
                (self.output.type.startswith('calculation') or
                 self.output.type.startswith('data'))):
                self.include_in_tc = True
            else:
                self.include_in_tc = False
        super(Link,self).save()

class Path(m.Model):
    """
    Transitive closure table for all node paths.
    """
    parent = m.ForeignKey('Node',related_name='child_paths',editable=False)
    child = m.ForeignKey('Node',related_name='parent_paths',editable=False)
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
    ('json', 'json'))

class Attribute(m.Model):
    '''
    Attributes are annotations ONLY for storing metadata and tagging. This is only for
    querying convenience.
    Actual input and output data should never go here, only duplicates and comments.
    '''
    time = m.DateTimeField(auto_now_add=True, editable=False)
    node = m.ForeignKey('Node', related_name='attributes')
    key = m.TextField(db_index=True)
    datatype = m.CharField(max_length=10, choices=attrdatatype_choice, db_index=True)
    txtval = m.TextField()
    floatval = m.FloatField()
    intval = m.IntegerField()
    boolval = m.NullBooleanField()

    class Meta:
        unique_together = (("node", "key"))
        
    def set(self,value):
        """
        This can be called on a given row and will set the corresponding value.
        NOTE: Rules below need to be checked.
        """
        import json
        if isinstance(value,bool):
            self.datatype = 'bool'
            if value:
                self.ival = 1

                self.tval = ""
                self.fval = 0.
            else:
                self.ival = 0

                self.fval = 0.
                self.tval = ""
        elif isinstance(value,int):
            self.datatype = 'int'
            self.ival = value

            self.fval = 0.
            self.tval = ""
        elif isinstance(value,float):
            self.datatype = 'float'
            self.fval = value

            self.ival = 0
            self.tval = ""
        elif isinstance(value,basestring):
            self.datatype = 'txt'
            self.tval = value
            
            self.ival = 0
            self.fval = 0.
        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError("Unable to store the value: it must be either "
                                 "a basic datatype, or json-serializable")
            
            self.datatype = 'json'
            self.tval = jsondata
            
            self.ival = 0
            self.fval = 0.
        
    def get(self):
        """
        This can be called on a given row and will get the corresponding value,
        casting it correctly
        """
        import json
        if self.datatype == 'bool':
            if ival == 0:
                return True
            else:
                return False
        elif self.datatype == 'int':
            return self.ival
        elif self.datatype == 'float':
            return self.fval
        elif self.datatype == 'txt':
            return self.tval
        elif self.datatype == 'json':
            try:
                return json.dumps(self.tval)
            except ValueError:
                raise DBContentError("Error in the content of the json field")
        else:
            raise DBContentError("The type field '{}' is not recognized".format(
                    self.datatype))        


class Group(m.Model):
    uuid = UUIDField(auto=True)
    name = m.TextField(unique=True, db_index=True)
    nodes = m.ManyToManyField('Node', related_name='groups')
    time = m.DateTimeField(auto_now_add=True, editable=False)
    description = m.TextField(blank=True)
    user = m.ForeignKey(User)  # The owner of the group, not of the calculations

class Computer(m.Model):
    """Table of computers or clusters.

    # TODO: understand if we want that this becomes simply another type of node.

    Attributes:
        hostname: Full hostname of the host
        workdir: Full path of the aida folder on the host. It can contain
            the string {username} that will be substituted by the username
            of the user on that machine.
            The actual workdir is then obtained as
            workdir.format(username=THE_ACTUAL_USERNAME)
            Example: 
            workdir = "/scratch/{username}/aida/"
        transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:
        - mpirun command
        - num cores per node
        - max num cores
        - allocate full node = True or False
        - ... (further limits per user etc.)
    """
    uuid = UUIDField(auto=True)
    hostname = m.CharField(max_length=255, unique=True) # FQDN
    description = m.TextField(blank=True)
    workdir = m.CharField(max_length=255)
    transport_type = m.CharField(max_length=255)
    scheduler_type = m.CharField(max_length=255)
    transport_params = m.TextField(default="{}") # Will store a json

    metadata = m.TextField(default="{}") # Will store a json

    def get_transport_params(self):
        import json
        try:
            return json.loads(self.transport_params)
        except ValueError:
            raise DBContentError(
                "Error while reading transport_params for computer {}".format(
                    self.hostname))
        
    def get_scheduler(self):
        import aida.scheduler
        from aida.common.pluginloader import load_plugin

        try:
            ThisPlugin = load_plugin(aida.scheduler.Scheduler, 'aida.scheduler.plugins',
                               self.scheduler_type)
            # I call the init without any parameter
            return ThisPlugin()
        except ImportError as e:
            raise ConfigurationError('No scheduler found for {} [type {}], message: {}'.format(
                self.hostname, self.scheduler_type, e.message))

class RunningJob(m.Model):
    calc = m.OneToOneField(Node,related_name='jobinfo') # OneToOneField implicitly sets unique=True
    calc_state = m.CharField(max_length=64)
    job_id = m.TextField(blank=True)
    scheduler_state = m.CharField(max_length=64,blank=True)
    # Will store a json of the last JobInfo got from the scheduler
    last_jobinfo = m.TextField(default='{}')  

class AuthInfo(m.Model):
    """
    Table that pairs aida users and computers, with all required authentication
    information.
    """
    aidauser = m.ForeignKey(User)
    computer = m.ForeignKey(Computer)
    auth_params = m.TextField(default='{}')  # Will store a json; contains mainly the remoteuser
                                             # and the private_key

    class Meta:
        unique_together = (("aidauser", "computer"),)

    def update_running_table(self):
        import aida
        aida.execmanager.update_running_table(self)

    def get_auth_params(self):
        import json
        try:
            return json.loads(self.auth_params)
        except ValueError:
            raise DBContentError(
                "Error while reading auth_params for authinfo, aidauser={}, computer={}".format(
                    self.aidauser, self.computer))

    # a method of AuthInfo
    def get_transport(self):
        """
        Given a computer and an aida user (as entries of the DB) return a configured
        transport to connect to the computer.
        """    
        from aida.common.pluginloader import load_plugin

        try:
            ThisTransport = load_plugin(aida.transport.Transport, 'aida.transport.plugins',
                                        self.computer.transport_type)
        except ImportError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.computer.hostname, self.computer.transport_type, e.message))

        params = self.computer.get_transport_params() + self.get_auth_params()
        return ThisTransport(machine=self.computer.hostname,**params)

class Comment(m.Model):
    node = m.ForeignKey(Node,related_name='comments')
    time = m.DateTimeField(auto_now_add=True, editable=False)
    user = m.ForeignKey(User)
    content = m.TextField(blank=True)

#class Code(NodeClass):
#    computer = m.ManyToManyField('Computer') #for checking computer compatibility

#class ComputerUsername(m.Model):
#    """Association of aida users with given remote usernames on a computer.
#
#    There is an unique_together constraint to be sure that each aida user
#    has no more than one remote username on a given computer.
#
#    Attributes:
#        computer: the remote computer
#        aidauser: the aida user
#        remoteusername: the username of the aida user on the remote computer
#    NOTE: this table can be eliminated in favor of a text field in each computer containing a dict.
#    """
#    computer = m.ForeignKey('Computer')
#    aidauser = m.ForeignKey(User)
#    remoteusername = m.CharField(max_length=255)
#
#    class Meta:
#        unique_together = (("aidauser", "computer"),)
#
#    def __unicode__(self):
#        return self.aidauser.username + " => " + \
#            self.remoteusername + "@" + self.computer.hostname

#-------------------- Abstract Base Classes ------------------------
#quality_choice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     
#nodetype_choice = (("calculation","calculation"), ("data","data"))
#state_choice = (('prepared', 'prepared'),
#                ('submitted', 'submitted'), 
#                ('queued', 'queued'),
#                ('running', 'runnning'),
#                ('failed', 'failed'),
#               ('finished', 'finished'),
#               ('completed', 'completed'))

## OLDSTUFF OF Node
#    path = m.FilePathField()
#    quality = m.IntegerField(choices=quality_choice, null=True, blank=True) 
#    #if node is data
#    source = m.ForeignKey('self', null=True, related_name='outputs')   #only valid for data nodes to link to source calculations
   # members = m.ManyToManyField('self', symmetrical=False, related_name='containers') 
#edgetype_choice = (("input","input"), ("member","member"), ("workflow","workflow"))
#    state = m.CharField(max_length=255, choices=state_choice, db_index=True)

## OLDSTUFF OF group
#grouptype_choice = (('project', 'project'), ('collection', 'collection'), ('workflow', 'workflow'))
#datagrouptype_choice = (('collection', 'collection'), ('relation', 'relation'))
#   type =  m.CharField(max_length=255, choices=calcgrouptype_choice, db_index=True)    
    

