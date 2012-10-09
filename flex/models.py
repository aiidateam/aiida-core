from django.db import models as m
#from django_orm.postgresql import hstore
#from django_hstore import hstore
#from django_extensions.db.fields import UUIDField
from uuidfield import UUIDField
from django.contrib.auth.models import User as AuthUser

#-------------------- Abstract Base Classes ------------------------

class Category(m.Model):
    uuid = UUIDField(auto=True)
    title = m.CharField(max_length=765, unique=True)
    description = m.TextField(blank=True)
    
class Entity(m.Model):
    uuid = UUIDField(auto=True)
    category = m.ForeignKey('Category')
    title = m.CharField(max_length=765, unique=True)
    description = m.TextField(blank=True)
    status = m.ForeignKey('Status')
    type = m.ForeignKey('Type')
    user = m.ForeignKey(AuthUser, null=True)
    time_stamp = m.DateTimeField(auto_now=True)
    hdata = m.TextField(blank=True)
    jdata = m.TextField(blank=True)
    def __unicode__(self):
        return "(%s) %s" % (self.category.title, self.title)

class StatusType(m.Model):
    uuid = UUIDField(auto=True)
    category = m.ForeignKey('Category')
    title = m.CharField(max_length=765, unique=True)
    description = m.TextField(blank=True)
    def __unicode__(self):
        return self.title
    
class StatusType(m.Model):
    uuid = UUIDField(auto=True)
    category = m.ForeignKey('Category')
    title = m.CharField(max_length=765, unique=True)
    description = m.TextField(blank=True)
    def __unicode__(self):
        return self.title

class Attribute(m.Model):
    uuid = UUIDField(auto=True)
    category = m.ForeignKey('Category')
    title = m.CharField(max_length=765, unique=True)
    description = m.TextField(blank=True)
    isnumber = m.BooleanField()
    hdata = m.TextField(blank=True)
    jdata = m.TextField(blank=True)
    def __unicode__(self):
        return "%s (%s)" % (self.title, self.datatype)
    class Meta:
        abstract = True

    
#---------------- Primary Classes ---------------------------------

class Computer(Entity):
    hostname = m.CharField(max_length=765, unique=True)
    ip_address = m.CharField(max_length=90, unique=True)
    scratch_location = m.CharField(max_length=765)

class CodeAttr(Attribute):
    pass

class CodeGroup(Entity):
    pass    
    
class CodeStatus(StatusType):
    pass

class CodeType(StatusType):    
    pass

class Code(Entity):
    type = m.ForeignKey('CodeType')
    computer = m.ForeignKey('Computer')
    status = m.ForeignKey('CodeStatus')
    user = m.ForeignKey(AuthUser, null=True)
    #    location = m.CharField(max_length=765)
    attrs = m.ManyToManyField('CodeAttr', through = 'CodeAttrVal')
    groups = m.ManyToManyField('CodeGroup', blank=True)
    def __unicode__(self):
        return self.title

class CodeAttrStr(m.Model):
    code = m.ForeignKey('Code')
    attr = m.ForeignKey('CodeAttr')
    val = m.TextField()
    class Meta:
        unique_together=('code','attr')
        
class CodeAttrNum(m.Model):
    code = m.ForeignKey('Code')
    attr = m.ForeignKey('CodeAttr')
    val = m.FloatField()
    class Meta:
        unique_together=('code','attr')
        
class ElementAttr(Attribute):
    pass

class ElementGroup(Entity):   
    pass

class Element(m.Model):
#    z = m.IntegerField(db_column='Z') # Field name made lowercase.
    name = m.CharField(max_length=135, unique=True)
    symbol = m.CharField(max_length=21, unique=True)
    mass = m.FloatField()
    hdata = m.TextField(blank=True)
    jdata = m.TextField(blank=True)
    attrs = m.ManyToManyField('ElementAttr', through = 'ElementAttrVal')
    groups = m.ManyToManyField('ElementGroup', blank=True)

#class ElementAttrVal(AttributeValue):
#    element = m.ForeignKey('Element')
#    attr = m.ForeignKey('ElementAttr')
#    class Meta:
#        unique_together=('element','attr')
        
class ElementAttrStr(m.Model):
    element = m.ForeignKey('Element')
    attr = m.ForeignKey('ElementAttr')
    val = m.TextField()
    class Meta:
        unique_together=('element','attr')
        
class ElementAttrNum(m.Model):
    element = m.ForeignKey('Element')
    attr = m.ForeignKey('ElementAttr')
    val = m.FloatField()
    class Meta:
        unique_together=('element','attr')

class PotBasisAttr(Attribute):
    pass

class PotBasisGroup(Entity):   
    pass

class PotBasisStatus(StatusType):
    pass

class PotBasisType(StatusType):    
    pass

class PotBasis(Entity):
    type = m.ForeignKey('PotBasisType')
    status = m.ForeignKey('PotBasisStatus')
    element = m.ManyToManyField('Element')
    user = m.ForeignKey(AuthUser)
    attrs = m.ManyToManyField('PotBasisAttr', through = 'PotBasisAttrVal')
    groups = m.ManyToManyField('PotBasisGroup', blank=True)

#class PotBasisAttrVal(AttributeValue):
#    potbasis = m.ForeignKey('PotBasis')
#    attr = m.ForeignKey('PotBasisAttr')
#    class Meta:
#        unique_together=('potbasis','attr')

class PotBasisAttrStr(m.Model):
    potbasis = m.ForeignKey('PotBasis')
    attr = m.ForeignKey('PotBasisAttr')
    val = m.TextField()
    class Meta:
        unique_together=('potbasis','attr')
        
class PotBasisAttrNum(m.Model):
    potbasis = m.ForeignKey('PotBasis')
    attr = m.ForeignKey('PotBasisAttr')
    val = m.FloatField()
    class Meta:
        unique_together=('potbasis','attr')
        
class Project(StatusType):
    pass

class StrucAttr(Attribute):
    pass

class StrucStatus(StatusType):
    pass

class StrucGroup(Entity):   
    pass

class StrucType(StatusType):    
    pass

class Struc(Entity):   
    formula = m.CharField(max_length=765)
    user = m.ForeignKey(AuthUser)
    type = m.ForeignKey('StrucType')
    attrs = m.ManyToManyField('StrucAttr', through = 'StrucAttrVal')
    groups = m.ManyToManyField('StrucGroup', blank=True)
    parent = m.ManyToManyField('self', related_name='child',
                                symmetrical=False,
                                verbose_name = 'Parent Structures',
                                blank=True)

class StrucAttrVal(AttributeValue):
    struc = m.ForeignKey('Struc')
    attr = m.ForeignKey('StrucAttr')
    class Meta:
        unique_together=('struc','attr')
        
class Composition(m.Model):
    struc = m.ForeignKey('Struc')
    element = m.ForeignKey('Element')
    quantity = m.IntegerField()


class CalcGroup(Entity):
    pass    
    
class CalcAttr(Attribute):
    pass
    
class CalcStatus(StatusType):
    pass

class CalcType(StatusType):    
    pass
    
class Calc(Entity):
    code = m.ForeignKey('Code')
    project = m.ForeignKey('Project')
    status = m.ForeignKey('CalcStatus')
    type = m.ForeignKey('CalcType')
    user = m.ForeignKey(AuthUser)
    computer = m.ForeignKey('Computer')
    qjob = m.IntegerField(blank=True, null=True)
    in_struc = m.ManyToManyField('Struc', related_name='in_calcs', blank=True)#, through='CalculationStructureLink')
    out_struc = m.ManyToManyField('Struc', related_name='out_calcs', blank=True)
    potbasis = m.ManyToManyField('PotBasis', blank=True)
    attrs = m.ManyToManyField('CalcAttr', through = 'CalcAttrVal')
    groups = m.ManyToManyField('CalcGroup', blank=True)
    parent = m.ManyToManyField('self', related_name='child',
                                symmetrical=False,
                                verbose_name = 'Parent Calculations',
                                blank=True)
    

class CalcAttrStr(AttributeValue):
    calc = m.ForeignKey('Calc')
    attr = m.ForeignKey('CalcAttr')
    isinput = m.BooleanField()
    class Meta:
        unique_together=('calc','attr','isinput')
