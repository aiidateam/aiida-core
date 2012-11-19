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
#from uuidfield import UUIDField

#Need to extend the User class with uuid, and add user-computer-username field

#-------------------- Abstract Base Classes ------------------------

class BaseClass(m.Model):
    # UUIDField by default uses version 1 (host ID, sequence number and current time) 
    uuid = UUIDField(auto=True,version=1)
    description = m.TextField(blank=True)
    data = JSONField()

    class Meta:
        abstract = True


# qualitychoice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     

 
class DataClass(BaseClass):
    ctime = m.DateTimeField(auto_now_add=True)
    mtime = m.DateTimeField(auto_now=True)
    user = m.ForeignKey(AuthUser)
# use an attribute instead
#    quality = m.IntegerField(choices=qualitychoice, null=True, blank=True)

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

#---------------- Primary Classes ---------------------------------

class Calculation(DataClass):
    code = m.ForeignKey('Code')
    project = m.ForeignKey('Project')
    status = m.ForeignKey('CalcStatus')
    type = m.ForeignKey('CalcType') #to determine type, relax, tbd
    computer = m.ForeignKey('Computer') #computer to which to submit
    instructures = m.ManyToManyField('Structure', related_name='incalculations', blank=True)
    outstructures = m.ManyToManyField('Structure', related_name='outcalculations', blank=True)
#    method = m.ManyToManyField('Method', blank=True)
    inpotentials = m.ManyToManyField('Potential', related_name='incalculations', blank=True)
    outpotentials = m.ManyToManyField('Potential', related_name='outcalculations', blank=True)
    basis = m.ManyToManyField('Basis', blank=True)
    attrnum = m.ManyToManyField('CalcAttrNum', through = 'CalcAttrNumVal')
    attrtxt = m.ManyToManyField('CalcAttrTxt', through = 'CalcAttrTxtVal')
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

#    flowitems = m.ForeignKey('self', symmetrical=False, blank=True, related_name='works')
#    workflow = m.ForeignKey('Workflow')
#    qjob = m.IntegerField(blank=True, null=True)


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


################################################

class Code(DataClass):
    name = m.CharField(max_length=255,unique=True)
    version = m.CharField(max_length=255)
    type = m.ForeignKey('CodeType') #to identify which parser/plugin
    status = m.ForeignKey('CodeStatus') #need to define
    computer = m.ForeignKey('Computer', blank=True) #for checking computer compatibility, empty means all. 
    attrnum = m.ManyToManyField('CodeAttrNum', through='CodeAttrNumVal')
    attrtxt = m.ManyToManyField('CodeAttrTxt', through='CodeAttrTxtVal')
    group = m.ManyToManyField('CodeGroup', blank=True)
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

###############################################

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
    symbol = m.CharField(max_length=3, unique=True)
    name = m.CharField(max_length=255, unique=True)
    Z = m.IntegerField(unique=True)
    attrnum = m.ManyToManyField('ElementAttrNum', through = 'ElementAttrNumVal')
    attrtxt = m.ManyToManyField('ElementAttrTxt', through = 'ElementAttrTxtVal')
    group = m.ManyToManyField('ElementGroup', blank=True)
        

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

######################################################
#
#class Method(EntityClass):
#    type = m.ForeignKey('MethodType')
#    status = m.ForeignKey('MethodStatus')
#    attrnum = m.ManyToManyField('MethodAttrNum', through = 'MethodAttrNumVal')
#    attrtxt = m.ManyToManyField('MethodAttrTxt', through = 'MethodAttrTxtVal')
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

class Potential(DataClass):
    type = m.ForeignKey('PotentialType')
    status = m.ForeignKey('PotentialStatus')
    elements = m.ManyToManyField('Element')
    attrnum = m.ManyToManyField('PotentialAttrNum', through = 'PotentialAttrNumVal')
    attrtxt = m.ManyToManyField('PotentialAttrTxt', through = 'PotentialAttrTxtVal')
    group = m.ManyToManyField('PotentialGroup', blank=True)

class PotentialAttrTxt(AttrClass): 
    pass

class PotentialAttrNum(AttrClass): 
    pass

class PotentialGroup(GroupClass): 
    pass

class PotentialComment(CommentClass): 
    pass

class PotentialStatus(BaseClass): 
    pass

class PotentialType(BaseClass): 
    pass

class PotentialAttrTxtVal(m.Model):
    item = m.ForeignKey('Potential')
    attr = m.ForeignKey('PotentialAttrTxt')
    val = m.TextField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')
        
class PotentialAttrNumVal(m.Model):
    item = m.ForeignKey('Potential')
    attr = m.ForeignKey('PotentialAttrNum')
    val = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

######################################################

class Basis(DataClass):
    type = m.ForeignKey('BasisType')
    status = m.ForeignKey('BasisStatus')
    element = m.ManyToManyField('Element')
    attrnum = m.ManyToManyField('BasisAttrNum', through = 'BasisAttrNumVal')
    attrtxt = m.ManyToManyField('BasisAttrTxt', through = 'BasisAttrTxtVal')
    group = m.ManyToManyField('BasisGroup', blank=True)

class BasisAttrTxt(AttrClass): 
    pass

class BasisAttrNum(AttrClass): 
    pass

class BasisGroup(GroupClass): 
    pass

class BasisComment(CommentClass): 
    pass

class BasisStatus(BaseClass): 
    pass

class BasisType(BaseClass): 
    pass

class BasisAttrTxtVal(m.Model):
    item = m.ForeignKey('Basis')
    attr = m.ForeignKey('BasisAttrTxt')
    val = m.TextField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')
        
class BasisAttrNumVal(m.Model):
    item = m.ForeignKey('Basis')
    attr = m.ForeignKey('BasisAttrNum')
    val = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

#####################################################

dimensions = ((0,'0'), (1,'1'), (2,'2'), (3,'3'))

class Struc(DataClass):   
    formula = m.CharField(max_length=255) #generated automatically using ordering rules
    dim = m.IntegerField(choices = dimensions)
#    dim = m.ForeignKey('StrucDim') #dimensionality/ make a choice integer field, default 3
    detail = m.TextField(blank=True)  #contains cell and atoms in angstroms json
    element = m.ManyToManyField('Element')
    attrnum = m.ManyToManyField('StrucAttrNum', through = 'StrucAttrNumVal')
    attrtxt = m.ManyToManyField('StrucAttrTxt', through = 'StrucAttrTxtVal')
    group = m.ManyToManyField('StrucGroup', blank=True)
    
class StrucGroup(GroupClass):  
    pass    
    
class StrucComment(CommentClass): 
    pass

class StrucAttrTxt(DataClass):  
    pass

class StrucAttrNum(DataClass):  
    pass

class StrucAttrTxtVal(m.Model):
    item = m.ForeignKey('Struc')
    attr = m.ForeignKey('StrucAttrTxt')
    val = m.TextField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

class StrucAttrNumVal(m.Model):
    item = m.ForeignKey('Struc')
    attr = m.ForeignKey('StrucAttrNum')
    val = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

#class Material(DataClass):   
#    pass
        
#############################################
