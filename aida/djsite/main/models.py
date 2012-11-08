from django.db import models as m
from django_extensions.db.fields import UUIDField
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
    uuid = UUIDField(auto=True)
    title = m.CharField(max_length=255, unique=True)
    description = m.TextField(blank=True)
    data = m.TextField(blank=True)
    def __unicode__(self):
        return self.title
    class Meta:
        abstract = True

qualitychoice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     
 
class DataClass(BaseClass):
#    hdata = m.TextField(blank=True)
    time = m.DateTimeField(auto_now=True)
    user = m.ForeignKey(AuthUser)
    quality = m.IntegerField(choices=qualitychoice, null=True, blank=True)  
    def save(self, *args, **kwargs):
        uname = getpass.getuser()
        self.user = AuthUser.objects.get(username=uname)
        super(DataClass, self).save(*args, **kwargs)
    class Meta:
        abstract = True    

class AttrClass(DataClass):
    isinput = m.BooleanField(default=True)
    class Meta:
        abstract = True    


class GroupClass(DataClass):
    parent = m.ForeignKey('self', blank=True, null=True)
    class Meta:
        abstract = True       


class CommentClass(DataClass):
    parent = m.ForeignKey('self', blank=True, null=True)
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

class Calc(DataClass):
    code = m.ForeignKey('Code')
    project = m.ForeignKey('Project')
    status = m.ForeignKey('CalcStatus')
    type = m.ForeignKey('CalcType') #to determine type, relax, tbd
    computer = m.ForeignKey('Computer') #computer to which to submit
    inpstruc = m.ManyToManyField('Struc', related_name='inpcalc', blank=True)
    outstruc = m.ManyToManyField('Struc', related_name='outcalc', blank=True)
#    method = m.ManyToManyField('Method', blank=True)
    inppot = m.ManyToManyField('Potential', related_name='inpcalc', blank=True)
    outpot = m.ManyToManyField('Potential', related_name='outcalc', blank=True)
    basis = m.ManyToManyField('Basis', blank=True)
    attrnum = m.ManyToManyField('CalcAttrNum', through = 'CalcAttrNumVal')
    attrtxt = m.ManyToManyField('CalcAttrTxt', through = 'CalcAttrTxtVal')
    group = m.ManyToManyField('CalcGroup', blank=True)
    parent = m.ManyToManyField('self', related_name='child',
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
        aidasrv.submitter.submit_calc(self)

    def get_local_dir(self):
        """
        Returns the path to the directory in the local repository
        containing all the information of the present calculation.
        """
        return os.path.join(LOCAL_REPOSITORY, 'calcs', unicode(self.id))

    def get_local_indir(self):
        """
        Returns the subdirectory of the local repository containing the 
        input files of the current calculation.
        """
        return os.path.join(self.get_local_dir(), 'inputs')

    def get_local_outdir(self):
        """
        Returns the subdirectory of the local repository containing the 
        output files retrieved from the current calculation.
        """
        return os.path.join(self.get_local_dir(), 'outputs')

    def get_local_attachdir(self):
        """
        Returns the subdirectory of the local repository containing the 
        files attached by the user to the current calculation
        (e.g. documentation, comments, ...)
        """
        return os.path.join(self.get_local_dir(), 'attachments')

#    flowitems = m.ForeignKey('self', symmetrical=False, blank=True, related_name='works')
#    workflow = m.ForeignKey('Workflow')
#    qjob = m.IntegerField(blank=True, null=True)


class CalcGroup(GroupClass):  
    pass
    
class CalcStatus(BaseClass):     
    class Meta:
        verbose_name_plural = "Calc statuses"


class Project(BaseClass):  
    pass

class CalcType(BaseClass):   
    pass 

class CalcComment(CommentClass):
    pass

class CalcAttrTxt(AttrClass):   
    pass

class CalcAttrNum(AttrClass):  
    pass

class CalcAttrTxtVal(m.Model):
    item = m.ForeignKey('Calc')
    attr = m.ForeignKey('CalcAttrTxt')
    val = m.TextField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

class CalcAttrNumVal(m.Model):
    item = m.ForeignKey('Calc')
    attr = m.ForeignKey('CalcAttrNum')
    val = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

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
    
class ComputerUsername(DataClass):
    """Association of aida users with given remote usernames on a computer.

    There is an unique_together constraint to be sure that each aida user
    has no more than one remote username on a given computer.

    Note:
        User has already a reverse relationship called computerusername_set
        that points to all elements that are owned by that user.
        We need thus to give another related_name for the aidauser key:
        it is computerusername_remoteuser_set
        This points to those elements of this table for which a remote
        username has been set for the given aidauser.

    Attributes:
        computer: the remote computer
        aidauser: the aida user
        remoteusername: the username of the aida user on the remote computer
    """
    computer = m.ForeignKey('Computer')
    aidauser = m.ForeignKey(AuthUser,
                            related_name='computerusername_remoteuser_set')
    remoteusername = m.CharField(max_length=255)

    class Meta:
        unique_together = (("aidauser", "computer"),)

    def __unicode__(self):
        return self.aidauser.username + " => " + \
            self.remoteusername + "@" + self.computer.hostname


################################################

class Code(DataClass):
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

    class Meta:
        verbose_name_plural = "Code statuses"

class CodeType(BaseClass):   
    """
    This class defines the code type. Note that the code title should follow
    a specific syntax since from the title AIDA retrieves which input (and
    output) plugins to use.
    The conversion is described in
    :func:`aidalib.inputplugins._get_plugin_module_name`.
    """
    pass

class CodeAttrTxt(DataClass):  
    pass

class CodeAttrNum(DataClass):   
    pass

class CodeAttrTxtVal(m.Model):
    item = m.ForeignKey('Code')
    attr = m.ForeignKey('CodeAttrTxt')
    val = m.TextField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')
        
class CodeAttrNumVal(m.Model):
    item = m.ForeignKey('Code')
    attr = m.ForeignKey('CodeAttrNum')
    val = m.FloatField()
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
    attrnum = m.ManyToManyField('ElementAttrNum', through = 'ElementAttrNumVal')
    attrtxt = m.ManyToManyField('ElementAttrTxt', through = 'ElementAttrTxtVal')
    group = m.ManyToManyField('ElementGroup', blank=True)
        
class ElementAttrTxt(AttrClass):   
    pass

class ElementAttrNum(AttrClass):   
    pass

class ElementGroup(GroupClass):  
    pass

class ElementAttrTxtVal(m.Model):
    item = m.ForeignKey('Element')
    attr = m.ForeignKey('ElementAttrTxt')
    val = m.TextField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')
        
class ElementAttrNumVal(m.Model):
    item = m.ForeignKey('Element')
    attr = m.ForeignKey('ElementAttrNum')
    val = m.FloatField()
    time = m.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('item','attr')

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
    element = m.ManyToManyField('Element')
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
