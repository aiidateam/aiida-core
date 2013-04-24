import getpass
import os

from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import User as AuthUser 

from aida.djsite.settings.settings import LOCAL_REPOSITORY
from aida.common.exceptions import DBContentError

class User(AuthUser):
    '''
    Need to extend the User class with uuid
    '''
    uuid = UUIDField(auto=True)
        
#-------------------- Abstract Base Classes ------------------------
  
quality_choice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     

class NodeClass(m.Model):
    uuid = UUIDField(auto=True)
    name = m.CharField(max_length=255, db_index=True)
    description = m.TextField(blank=True)
    time = m.DateTimeField(auto_now_add=True, editable=False)
    user = m.ForeignKey(User)
    quality = m.IntegerField(choices=quality_choice, null=True, blank=True) 
    type = m.CharField(max_length=255, db_index=True)
    path = m.FilePathField()
    attrdata = m.TextField(blank=True)   # json of the data to be split into attrs for querying
    metadata = m.TextField(blank=True)   # json of the data    
    def __unicode__(self):
        return self.name, self.type
    class Meta:
        abstract = True

#----------------------------------------------------------------------

nodetype_choice = (("calculation","calculation"), ("data","data"))

state_choice = (('prepared', 'prepared'),
                ('submitted', 'submitted'), 
                ('queued', 'queued'),
                ('running', 'runnning'),
                ('failed', 'failed'),
                ('finished', 'finished'),
                ('completed', 'completed'))

class Node(NodeClass):
    '''
    Generic node, data or calculation. There will be several types of connections.
    Naming convention: data A --> calc C --> data B. 
    A is 'input' of C. C is 'destination' of A. B is 'output' of C. C is 'source' of B. 
    A is 'parent' of B,C. C,B are 'children' of A.
    TODO: node hierarchy and workflows.
    '''
    state = m.CharField(max_length=255, choices=state_choice, db_index=True)
    # if node is a calculation
    code = m.ForeignKey('Code', null=True)   # only for calculations
    computer = m.ForeignKey('Computer', null=True)  # only for calculations
    inputs = m.ManyToManyField('self', symmetrical=False, related_name='destinations', through='Input')  # only direct inputs
    #if node is data
    source = m.ForeignKey('self', null=True, related_name='outputs')   #only valid for data nodes to link to source calculations
    #for both types
    children = m.ManyToManyField('self', symmetrical=False, related_name='parents', through='Path')
   
   # members = m.ManyToManyField('self', symmetrical=False, related_name='containers') 
#edgetype_choice = (("input","input"), ("member","member"), ("workflow","workflow"))

class Input(m.Model):
    '''
    Connects an input data with a calculation. The label is identifying the input type.
    '''
    data = m.ForeignKey('Node')
    destination = m.ForeignKey('Node')
    label = m.CharField(max_length=255, db_index=True)    #label for data input for calculation 


class Path(m.Model):
    '''
    Transitive closure for all node paths.
    '''
    origin = m.ForeignKey('Node')
    destination = m.ForeignKey('Node')
    depth = m.IntegerField()


attrdatatype_choice = (('float', 'float'), ('int', 'int'), ('txt', 'txt'),  ('bool', 'bool'), ('json', 'json'))


class Attr(m.Model):
    '''
    Attributes are annotations ONLY for storing metadata and tagging. This is only for querying convenience.
    Actual input and output data should never go here, only duplicates and comments.
    '''
    node = m.ForeignKey('Node')
    key = m.CharField(max_length=255, db_index=True)
    user = m.ForeignKey(User)
    time = m.DateTimeField(auto_now_add=True, editable=False)
    tval = m.TextField()
    fval = m.FloatField()
    ival = m.IntegerField()
#    boolval = m.BooleanField()
    datatype = m.CharField(max_length=255, choices=attrdatatype_choice, db_index=True)

    class Meta:
        unique_together = (("node", "key"))
        
    def set(self,value):
        """
        This can be called on a given row and will set the corresponding value.
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
            
            self.datatupe = 'json'
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

#grouptype_choice = (('project', 'project'), ('collection', 'collection'), ('workflow', 'workflow'))


class Group(m.Model):  
    uuid = UUIDField(auto=True)
    node = m.ManyToManyField('Node', blank=True, related_name='group')  
    time = m.DateTimeField(auto_now_add=True, editable=False)
    name = m.CharField(max_length=255, unique=True)
    description = m.TextField(blank=True)
#   type =  m.CharField(max_length=255, choices=calcgrouptype_choice, db_index=True)
    
#datagrouptype_choice = (('collection', 'collection'), ('relation', 'relation'))        


class Computer(m.Model):
    """Table of computers or clusters.

    Attributes:
        hostname: Full hostname of the host
        workdir: Full path of the aida folder on the host. It can contain
            the string {username} that will be substituted by the username
            of the user on that machine.
            The actual workdir is then obtained as
            workdir.format(username=THE_ACTUAL_USERNAME)
            Example: 
            workdir = "/scratch/{username}/aida/"
    """
    hostname = m.CharField(max_length=255, unique=True)
    workdir = m.CharField(max_length=255)
    
    
class Code(NodeClass):
    computer = m.ManyToManyField('Computer') #for checking computer compatibility


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

