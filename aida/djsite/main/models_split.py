from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import User as AuthUser 
import getpass
import aida.jobmanager.submitter
import os
import os.path
from aida.djsite.settings.settings import LOCAL_REPOSITORY
#from uuidfield import UUIDField


class User(AuthUser):
    '''
    Need to extend the User class with uuid
    '''
    uuid = UUIDField(auto=True)
        
#-------------------- Abstract Base Classes ------------------------

class BaseClass(m.Model):
    uuid = UUIDField(auto=True)
    description = m.TextField(blank=True)
    class Meta:
        abstract = True


class NameClass(BaseClass):
    name = m.CharField(max_length=255, unique=True)
    def __unicode__(self):
        return self.title

    
quality_choice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     

 
class EntityClass(BaseClass):
    crtime = m.DateTimeField(auto_now_add=True, editable=False)
    modtime = m.DateTimeField(auto_now=True)
    user = m.ForeignKey(User)
    quality = m.IntegerField(choices=quality_choice, null=True, blank=True)  
    metadata = m.TextField(blank=True)
    class Meta:
        abstract = True
                

#class CommentClass(EntityClass):
#    parent = m.ForeignKey('self', blank=True, null=True)
#    class Meta:
#        abstract = True       
        
#-------------------------- Primary Classes ---------------------------------

#############################################################################
calcstate_choice = (('prepared', 'prepared'),
                    ('submitted', 'submitted'), 
                    ('queued', 'queued'),
                    ('running', 'runnning'),
                    ('failed', 'failed'),
                    ('finished', 'finished'),
                    ('completed', 'completed'))

class Calc(EntityClass):
    code = m.ForeignKey('Code')
    state = m.CharField(max_length=255, choices=calcstate_choice, db_index=True)
    type = m.CharField(max_length=255, db_index=True)
    datain = m.ManyToManyField('Data', blank=True)   
    group = m.ManyToManyField('CalcGroup', blank=True)
    

calcgrouptype_choice = (('project', 'project'), ('collection', 'collection'), ('workflow', 'workflow'))

class CalcGroup(BaseClass):  
    type =  m.CharField(max_length=255, choices=calcgrouptype_choice, db_index=True)
    

#class CalcComment(CommentClass):
#    '''
#    Convenience feature
#    '''
#    pass

attrdatatype_choice = (('float', 'float'), ('int', 'int'), ('txt', 'txt'),  ('bool', 'bool'))

class CalcAttr(NameClass):
    '''
    Attributes are annotations ONLY for storing metadata and tagging. This is only for querying convenience.
    Actual input and output data should never go here.
    '''
    calc = m.ForeignKey('Calc')
    key = m.CharField(max_length=255, db_index=True)
    txtval = m.TextField()
    floatval = m.FloatField()
    intval = m.IntegerField()
    boolval = m.BooleanField()
    datatype = m.CharField(max_length=255, choices=attrdatatype_choice, db_index=True)
    class Meta:
        unique_together = (("calc", "key")


##############################################################

class Data(EntityClass):
    calc = m.ForeignKey('Calc', related_name='dataout')      #unique parent Calc for each data
    type = m.CharField(max_length=255, db_index=True)
    numval = m.FloatField()
    group = m.ManyToManyField('DataGroup', blank=True)
    linkdata = m.ManyToManyField('self')
    attr = m.ManyToManyField('DataAttr', through = 'DataAttrVal')

#datagrouptype_choice = (('collection', 'collection'), ('relation', 'relation'))        


class DataGroup(BaseClass):
    #type = m.CharField(max_length=255, choices=datagrouptype_choice)
    pass


#class DataComment(CommentClass):
#    pass

class DataAttr(NameClass):
    '''
    Attributes are annotations ONLY for storing metadata and tagging. This is only for querying convenience.
    Actual input and output data should never go here.
    '''
    data = m.ForeignKey('Data')
    key = m.CharField(max_length=255, db_index=True)
    txtval = m.TextField()
    floatval = m.FloatField()
    intval = m.IntegerField()
    boolval = m.BooleanField()
    datatype = m.CharField(max_length=255, choices=attrdatatype_choice, db_index=True)
    class Meta:
        unique_together = (("data", "key")


#############################################################


class Computer(NameClass):
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
#

class Code(EntityClass):
    type = m.CharField(max_length=255, db_index=True) #to identify which parser/plugin
    computer = m.ForeignKey('Computer', blank=True) #for checking computer compatibility, empty means all
    group = m.ManyToManyField('CodeGroup', blank=True)
    attr = m.ManyToManyField('CodeAttr', through='CodeAttrVal')
    def __unicode__(self):
        return self.name

class CodeGroup(NameClass):  
    pass    
    
class CodeComment(CommentClass): 
    pass


class DataAttr(NameClass):
    '''
    Attributes are annotations ONLY for storing metadata and tagging. This is only for querying convenience.
    Actual input and output data should never go here.
    '''
    data = m.ForeignKey('Data')
    key = m.CharField(max_length=255, db_index=True)
    txtval = m.TextField()
    floatval = m.FloatField()
    intval = m.IntegerField()
    boolval = m.BooleanField()
    datatype = m.CharField(max_length=255, choices=attrdatatype_choice, db_index=True)
    class Meta:
        unique_together = (("data", "key")



