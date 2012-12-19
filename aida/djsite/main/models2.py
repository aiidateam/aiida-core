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
    Need to extend the User class with uuid, and add user-computer-username field
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
    
qualitychoice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     

 
class EntityClass(BaseClass):
    crtime = m.DateTimeField(auto_now_add=True, editable=False)
    modtime = m.DateTimeField(auto_now=True)
    user = m.ForeignKey(User)
    quality = m.IntegerField(choices=qualitychoice, null=True, blank=True)  
    metadata = m.TextField(blank=True)
    class Meta:
        abstract = True
                
        
class CommentClass(EntityClass):
    parent = m.ForeignKey('self', blank=True, null=True)
    class Meta:
        abstract = True       
        
#-------------------------- Primary Classes ---------------------------------

#################################################################
class Calculation(EntityClass):
    code = m.ForeignKey('Code')
    project = m.ForeignKey('Project')
    state = m.ForeignKey('CalculationState')
    type = m.ForeignKey('CalculationType')
    dataout = m.ManyToManyField('Data', blank=True)   
    attr = m.ManyToManyField('CalculationAttr', through = 'CalculationAttrVal')
    group = m.ManyToManyField('CalculationGroup', blank=True)


class CalculationGroup(BaseClass):  
    type = m.ForeignKey('CalculationGroupType')


class CalculationGroupType(NameClass):
    '''
    Groups of calculations can be: projects, collections, or workflows
    ''' 
    pass
    

class CalculationState(NameClass):     
    '''
    Calculation state can be: prepared, submitted, queued, running, failed, finished, completed.
    '''
    pass


class CalculationType(NameClass):   
    '''
    Calculation type may be: spectrum, energy etc or just a blank link.
    This is for user convenience.
    '''
    pass 


class CalculationComment(CommentClass):
    '''
    Convenience feature
    '''
    pass


class CalculationAttr(NameClass):
    '''
    Attributes are convenience ONLY for storing metadata and tagging.
    Actual input and output data should never go here.
    '''
    pass 


class CalculationAttrVal(m.Model):
    item = m.ForeignKey('Calculation')
    attr = m.ForeignKey('CalculationAttr')
    txtval = m.TextField()
    numval = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

##############################################################

class Data(EntityClass):
    calculation = m.ForeignKey('Calculation', related_name='datain')      #unique parent calculation for each data
    type = m.ForeignKey('DataType')
    element = m.ManyToManyField('Element')
    numval = m.FloatField()
    txtval = m.TextField()
    path = m.TextField(null=True, blank=True)
    attr = m.ManyToManyField('DataAttr', through = 'DataAttrVal')

        
class DataGroup(BaseClass):  
    type = m.ForeignKey('DataGroupType')

class DataGroupType(NameClass):
    '''
    Data group types can be: collection or relation (data objects linked logically)
    '''
    pass

class DataType(NameClass):
    '''
    Data types can be: energy, spectrucm, density, structure, potential, etc
    '''
    format = m.TextField() 

class DataComment(CommentClass):
    pass

class DataAttr(EntityClass):   
    pass

class DataAttrVal(m.Model):
    item = m.ForeignKey('Data')
    attr = m.ForeignKey('DataAttr')
    txtval = m.TextField()
    numval = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

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
    
class ComputerUsername(m.Model):
    """Association of aida users with given remote usernames on a computer.

    There is an unique_together constraint to be sure that each aida user
    has no more than one remote username on a given computer.

    Attributes:
        computer: the remote computer
        aidauser: the aida user
        remoteusername: the username of the aida user on the remote computer
    NOTE: this table can be eliminated in favor of a text field in each computer containing a dict.
    """
    computer = m.ForeignKey('Computer')
    aidauser = m.ForeignKey(User)
    remoteusername = m.CharField(max_length=255)

    class Meta:
        unique_together = (("aidauser", "computer"),)

    def __unicode__(self):
        return self.aidauser.username + " => " + \
            self.remoteusername + "@" + self.computer.hostname

################################################
#
#class Job(DataClass):
#    computer = m.ForeignKey('Computer') #computer to which to submit
#    qjobid = m.IntegerField(blank=True, null=True)
################################################

class Code(EntityClass):
    type = m.ForeignKey('CodeType') #to identify which parser/plugin
    state = m.ForeignKey('CodeState') #need to define
    computer = m.ForeignKey('Computer', blank=True) #for checking computer compatibility, empty means all. 
    attr = m.ManyToManyField('CodeAttr', through='CodeAttrVal')
    group = m.ManyToManyField('CodeGroup', blank=True)
    def __unicode__(self):
        return self.title

class CodeGroup(NameClass):  
    pass    
    
class CodeComment(CommentClass): 
    pass

class CodeState(NameClass):   
    pass

class CodeType(NameClass):   
    """
    This class defines the code type. Note that the code title should follow
    a specific syntax since from the title AIDA retrieves which input (and
    output) plugins to use.
    The conversion is described in the functions of the 
    :mod:`aida.codeplugins` module.
    """
    pass

class CodeAttr(NameClass):  
    pass


class CodeAttrVal(m.Model):
    item = m.ForeignKey('Code')
    attr = m.ForeignKey('CodeAttr')
    txtval = m.TextField()
    numval = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

###############################################

class Element(BaseClass):
    """
    This table contains the atomic elements, from hydrogen (Z=1) to
    Lawrencium (Z=103).

    The element symbol is stored in the 'title' field. 
    The element name is stored in the 'description' field.
    
    The atomic mass is stored under the 'mass' key in the json-dumped
    data field. The mass is taken from ASE and, where not available,
    it has been substituted by a nearest integer number.
    
    This default value has not been set as an attribute because the
    attribute require an owner, and this hinders the usage of fixtures
    to fill default data in the database since no default user exists.
    """
    Z = m.IntegerField(unique=True)
    attr = m.ManyToManyField('ElementAttr', through = 'ElementAttrVal')
    group = m.ManyToManyField('ElementGroup', blank=True)
        
class ElementGroup(NameClass):  
    pass

class ElementAttr(NameClass):   
    pass

class ElementAttrVal(m.Model):
    item = m.ForeignKey('Element')
    attr = m.ForeignKey('ElementAttr')
    txtval = m.TextField()
    numval = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

######################################################




