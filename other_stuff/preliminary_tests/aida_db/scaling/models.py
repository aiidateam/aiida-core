from django.db import models as m

# Create your models here.
class DataCalc(m.Model):
    uuid = m.CharField(max_length=255, unique=True)
    isdata = m.BooleanField()
    datatype = m.CharField(max_length=255)
    children = m.ManyToManyField('self', symmetrical=False, related_name='parents')
    ## A hint on what is source and what is destination, from the Django
    ## source code 
    ## https://code.djangoproject.com/browser/django/trunk/django/db/models/fields/related.py
    # If this is an m2m-intermediate to self,
    # the first foreign key you find will be
    # the source column. Keep searching for
    # the second foreign key.
    destinations = m.ManyToManyField('self', symmetrical=False, through='Closure', related_name='sources')


    def __unicode__(self):
        string = u"[Data(" if self.isdata else u"[Calc("
        string += unicode(self.datatype)
        string += u"), id="
        string += unicode(self.id)
        string += u"]"
        return string

class Attribute(m.Model):
    datacalc = m.ForeignKey('DataCalc')
    key = m.CharField(max_length=255, db_index=True)
    val_num = m.FloatField(null=True)
    val_text = m.TextField(null=True)

    def is_energy(self):
      if self.key=="energy":
        return True
      else:
        return False

class Closure(m.Model):
	start_datacalc = m.ForeignKey(DataCalc, related_name='destinations_relations')
	end_datacalc = m.ForeignKey(DataCalc, related_name='sources_relations')
	hops = m.IntegerField()
	# Used to delete
	entry_edge_id = m.IntegerField(null=True)
	direct_edge_id = m.IntegerField(null=True)
 	exit_edge_id = m.IntegerField(null=True)
 	# Used to keep more then one TC
	source = m.CharField(max_length=255)
