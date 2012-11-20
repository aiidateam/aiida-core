from django.db import models as m
from django_extensions.db.fields import UUIDField
from django_extensions.db.fields.json import JSONField
from django.contrib.auth.models import User as AuthUser 
import getpass
import aida.jobmanager.submitter
import os
import os.path
from aida.djsite.settings.settings import LOCAL_REPOSITORY
#from django_orm.postgresql import hstore
#from django_hstore import hstore

#TODO: Need to extend the User class with uuid


######################### Abstract Classes ###########################
class BaseClass(m.Model):
    # UUIDField by default uses version 1 (host ID, sequence number and current time) 
    uuid = UUIDField(auto=True,version=1)
    description = m.TextField(blank=True)
    data = JSONField()

    class Meta:
        abstract = True

class DataClass(BaseClass):
    ctime = m.DateTimeField(auto_now_add=True)
    mtime = m.DateTimeField(auto_now=True)
    user = m.ForeignKey(AuthUser)

    class Meta:
        abstract = True    


class AttrClass(BaseClass):
    name = m.CharField(max_length=255, unique=True)
    isinput = m.BooleanField(default=True)

    class Meta:
        abstract = True    


class GroupClass(DataClass):
    name = m.CharField(max_length=255, unique=True)
    parent = m.ForeignKey('self', blank=True, null=True)

    class Meta:
        abstract = True       


class CommentClass(DataClass):
    name = m.CharField(max_length=255, unique=True)
    parent = m.ForeignKey('self', blank=True, null=True)
    comment = m.TextField(blank=True)

    class Meta:
        abstract = True  
        
############################ Primary Classes ##############################

## ----------Calculation-related tables ----------------
class Calculation(DataClass):
    code = m.ForeignKey('Code')
    project = m.ForeignKey('Project')
    status = m.ForeignKey('CalcStatus')
    type = m.ForeignKey('CalcType') #to determine type, relax, tbd
    computer = m.ForeignKey('Computer') #computer to which to submit
    instructures = m.ManyToManyField('Structure', related_name='incalculations', blank=True)
    outstructures = m.ManyToManyField('Structure', related_name='outcalculations', blank=True)
    inpotentials = m.ManyToManyField('Potential', related_name='incalculations', blank=True)
    outpotentials = m.ManyToManyField('Potential', related_name='outcalculations', blank=True)
    bases = m.ManyToManyField('Basis', blank=True)
    attrsnum = m.ManyToManyField('CalcAttrNum', through = 'CalcAttrNumVal')
    attrstxt = m.ManyToManyField('CalcAttrTxt', through = 'CalcAttrTxtVal')
    groups = m.ManyToManyField('CalcGroup', blank=True)
    parents = m.ManyToManyField('self', related_name='children',
                               symmetrical=False,
                               blank=True)

    def submit(self):
        """
        Submits the calculation to the cluster, using the information
        specified in the database.

        Note:
            To be called after the calculation *and* all related tables
            have been set.
        """
        aida.jobmanager.submitter.submit_calc(self)


class CalcGroup(GroupClass):  
    pass
    

class CalcStatus(BaseClass): 
    name = m.CharField(max_length=255, unique=True)    
    class Meta:
        verbose_name_plural = "Calc statuses"


class Project(DataClass):
    name = m.CharField(max_length=255, unique=True)
    pass


class CalcType(BaseClass):
    name = m.CharField(max_length=255, unique=True)
    pass 


class CalcComment(CommentClass):
    pass


class CalcAttrTxt(AttrClass):   
    pass


class CalcAttrNum(AttrClass):  
    pass


class CalcAttrTxtVal(DataClass):
    calculation = m.ForeignKey('Calculation')
    attribute = m.ForeignKey('CalcAttrTxt')
    value = m.TextField()

    class Meta:
        unique_together=('calculation','attribute')


class CalcAttrNumVal(DataClass):
    calculation = m.ForeignKey('Calculation')
    attribute = m.ForeignKey('CalcAttrNum')
    value = m.FloatField()
    class Meta:
        unique_together=('calculation','attribute')


## ----------Computer-related tables ----------------
class Computer(DataClass):
    """Table of computers or clusters.
    
    Note that some attributes are inherited from the parent class.

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
        user: the local aida user
        remoteusername: the username of the aida user on the remote computer
    """
    computer = m.ForeignKey('Computer')
    user = m.ForeignKey(AuthUser)
    remoteusername = m.CharField(max_length=255)

    class Meta:
        unique_together = (("user", "computer"),)

    def __unicode__(self):
        return self.user.username + " => " + \
            self.remoteusername + "@" + self.computer.hostname


## ----------Code-related tables ----------------
class Code(DataClass):
    name = m.CharField(max_length=255,unique=True)
    version = m.CharField(max_length=255)
    type = m.ForeignKey('CodeType') #to identify which parser/plugin
    status = m.ForeignKey('CodeStatus') #need to define
    computer = m.ForeignKey('Computer', blank=True) #for checking computer compatibility, empty means all. 
    attrsnum = m.ManyToManyField('CodeAttrNum', through='CodeAttrNumVal')
    attrstxt = m.ManyToManyField('CodeAttrTxt', through='CodeAttrTxtVal')
    groups = m.ManyToManyField('CodeGroup', blank=True)
    def __unicode__(self):
        return self.title


class CodeGroup(GroupClass):  
    pass    

    
class CodeComment(CommentClass): 
    pass


class CodeStatus(BaseClass):   
    name = m.CharField(max_length=255, unique=True)    

    class Meta:
        verbose_name_plural = "Code statuses"


class CodeType(BaseClass):   
    """
    This class defines the code type. Note that the CodeType name should follow
    a specific syntax since from the title AIDA retrieves which input (and
    output) plugins to use.
    The conversion is described in the functions of the 
    :mod:`aida.codeplugins` module.
    """
    name = m.CharField(max_length=255, unique=True)    


class CodeAttrTxt(AttrClass):  
    pass


class CodeAttrNum(AttrClass):   
    pass


class CodeAttrTxtVal(DataClass):
    code = m.ForeignKey('Code')
    attribute = m.ForeignKey('CodeAttrTxt')
    value = m.TextField()

    class Meta:
        unique_together=('code','attribute')

        
class CodeAttrNumVal(DataClass):
    code = m.ForeignKey('Code')
    attribute = m.ForeignKey('CodeAttrNum')
    value = m.FloatField()

    class Meta:
        unique_together=('code','attribute')


## ----------Element-related tables ----------------
class Element(BaseClass):
    """
    This table contains the atomic elements, from hydrogen (Z=1) to
    Lawrencium (Z=103).

    Name contains the English element name.
    
    The atomic mass is stored under the 'mass' key in the json-dumped
    data field. The mass is taken from ASE and, where not available,
    it has been substituted by a nearest integer number.
    
    This default value has not been set as an attribute because the
    attribute require an owner, and this hinders the usage of fixtures
    to fill default data in the database since no default user exists.
    """
    name = m.CharField(max_length=255, unique=True)
    symbol = m.CharField(max_length=3, unique=True)
    Z = m.IntegerField(unique=True)
    attrsnum = m.ManyToManyField('ElementAttrNum', through = 'ElementAttrNumVal')
    attrstxt = m.ManyToManyField('ElementAttrTxt', through = 'ElementAttrTxtVal')
    groups = m.ManyToManyField('ElementGroup', blank=True)
        

class ElementAttrTxt(AttrClass):   
    pass


class ElementAttrNum(AttrClass):   
    pass


class ElementGroup(GroupClass):  
    pass


class ElementAttrTxtVal(DataClass):
    element = m.ForeignKey('Element')
    attribute = m.ForeignKey('ElementAttrTxt')
    value = m.TextField()

    class Meta:
        unique_together=('element','attribute')
        

class ElementAttrNumVal(DataClass):
    element = m.ForeignKey('Element')
    attribute = m.ForeignKey('ElementAttrNum')
    value = m.FloatField()

    class Meta:
        unique_together=('element','attribute')

## ----------Potential-related tables ----------------
class Potential(DataClass):
    type = m.ForeignKey('PotType')
    status = m.ForeignKey('PotStatus')
    elements = m.ManyToManyField('Element')
    attrsnum = m.ManyToManyField('PotAttrNum', through = 'PotAttrNumVal')
    attrstxt = m.ManyToManyField('PotAttrTxt', through = 'PotAttrTxtVal')
    groups = m.ManyToManyField('PotGroup', blank=True)

class PotAttrTxt(AttrClass): 
    pass

class PotAttrNum(AttrClass): 
    pass

class PotGroup(GroupClass): 
    pass

class PotComment(CommentClass): 
    pass

class PotStatus(BaseClass): 
    name = m.CharField(max_length=255, unique=True)    
    class Meta:
        verbose_name_plural = "Pot statuses"

class PotType(BaseClass): 
    name = m.CharField(max_length=255, unique=True)

class PotAttrTxtVal(DataClass):
    potential = m.ForeignKey('Potential')
    attribute = m.ForeignKey('PotAttrTxt')
    value = m.TextField()
    class Meta:
        unique_together=('potential','attribute')
        
class PotAttrNumVal(DataClass):
    potential = m.ForeignKey('Potential')
    attribute = m.ForeignKey('PotAttrNum')
    value = m.FloatField()
    class Meta:
        unique_together=('potential','attribute')

## ----------Basis-related tables ----------------
class Basis(DataClass):
    type = m.ForeignKey('BasisType')
    status = m.ForeignKey('BasisStatus')
    elements = m.ManyToManyField('Element')
    attrsnum = m.ManyToManyField('BasisAttrNum', through = 'BasisAttrNumVal')
    attrstxt = m.ManyToManyField('BasisAttrTxt', through = 'BasisAttrTxtVal')
    groups = m.ManyToManyField('BasisGroup', blank=True)

class BasisAttrTxt(AttrClass): 
    pass

class BasisAttrNum(AttrClass): 
    pass

class BasisGroup(GroupClass): 
    pass

class BasisComment(CommentClass): 
    pass

class BasisStatus(BaseClass): 
    name = m.CharField(max_length=255, unique=True)    
    class Meta:
        verbose_name_plural = "Pot statuses"

class BasisType(BaseClass): 
    name = m.CharField(max_length=255, unique=True)

class BasisAttrTxtVal(DataClass):
    basis = m.ForeignKey('Basis')
    attribute = m.ForeignKey('BasisAttrTxt')
    value = m.TextField()
    class Meta:
        unique_together=('basis','attribute')
        
class BasisAttrNumVal(DataClass):
    basis = m.ForeignKey('Basis')
    attribute = m.ForeignKey('BasisAttrNum')
    value = m.FloatField()
    class Meta:
        unique_together=('basis','attribute')


## ----------Structure-related tables ----------------
dimensions = ((0,'0'), (1,'1'), (2,'2'), (3,'3'))
class Structure(DataClass):   
    formula = m.CharField(max_length=255) #generated automatically using ordering rules
    dim = m.IntegerField(choices = dimensions, default=3)
    elements = m.ManyToManyField('Element')
    attrsnum = m.ManyToManyField('StructAttrNum', through = 'StructAttrNumVal')
    attrstxt = m.ManyToManyField('StructAttrTxt', through = 'StructAttrTxtVal')
    groups = m.ManyToManyField('StructGroup', blank=True)
    
class StructGroup(GroupClass):  
    pass    
    
class StructComment(CommentClass): 
    pass

class StructAttrTxt(AttrClass):  
    pass

class StructAttrNum(AttrClass):  
    pass

class StructAttrTxtVal(DataClass):
    structure = m.ForeignKey('Structure')
    attribute = m.ForeignKey('StructAttrTxt')
    value = m.TextField()
    class Meta:
        unique_together=('structure','attribute')

class StructAttrNumVal(DataClass):
    structure = m.ForeignKey('Structure')
    attribute = m.ForeignKey('StructAttrNum')
    val = m.FloatField()
    class Meta:
        unique_together=('structure','attribute')


#############################################
##Old Stuff:
##In data class:
# qualitychoice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     
# use an attribute instead
#    quality = m.IntegerField(choices=qualitychoice, null=True, blank=True)
##
#
#class EntityClass(DataClass):
#    ''' 
#    quality: 1-5 stars, NULL means unranked
#    '''
#    time = m.DateTimeField(auto_now=True)
#    user = m.ForeignKey(AuthUser)
#    quality = m.IntegerField(choices=qualitychoice, null=True)
#    def save(self, *args, **kwargs):
#        uname = getpass.getuser()
#        self.user = AuthUser.objects.get(username=uname)
#        super(EntityClass, self).save(*args, **kwargs)
#    class Meta:
#        abstract = True
#        
# static entries: type, status --> use BaseClass
# time: Calc, Struc, Computer, Pot, ... Groups, Attributes, NOT status?
# data: calc, struc, computer, pot, groups, attrs
# user: Calc, Struc, computer, Pot, Basis, Attr
# quality: Calc, Pot, Code, Basis, NOT struc, NOT attr, element, group
# single parent: Groups, comments
# multi-parent: calc only
##
##In calculation
#    flowitems = m.ForeignKey('self', symmetrical=False, blank=True, related_name='works')
#    workflow = m.ForeignKey('Workflow')
#    qjob = m.IntegerField(blank=True, null=True)
######################################################
#
#class Method(EntityClass):
#    type = m.ForeignKey('MethodType')
#    status = m.ForeignKey('MethodStatus')
#    attrsnum = m.ManyToManyField('MethodAttrNum', through = 'MethodAttrNumVal')
#    attrstxt = m.ManyToManyField('MethodAttrTxt', through = 'MethodAttrTxtVal')
#    groups = m.ManyToManyField('MethodGroup', blank=True)
#
#class MethodAttrTxt(DataClass): 
#    pass
#
#class MethodAttrNum(DataClass): 
#    pass
#
#class MethodGroup(EntityClass):
#    pass
#    
#class MethodStatus(BaseClass): 
#    pass
#
#class MethodType(BaseClass): 
#    pass
#
#class MethodAttrTxtVal(m.Model):
#    item = m.ForeignKey('Method')
#    attr = m.ForeignKey('MethodAttrTxt')
#    val = m.TextField()
#    time = m.DateTimeField(auto_now=True)
#    class Meta:
#        unique_together=('item','attr')
#        
#class MethodAttrNumVal(m.Model):
#    item = m.ForeignKey('Method')
#    attr = m.ForeignKey('MethodAttrNum')
#    val = m.FloatField()
#    time = m.DateTimeField(auto_now=True)
#    class Meta:
#        unique_together=('item','attr')
#####################################################
