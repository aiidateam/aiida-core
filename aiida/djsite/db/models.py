from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet

from aiida.common.exceptions import (
    ConfigurationError, DbContentError, MissingPluginError, InternalError)

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

    * A is 'input' of C.

    * C is 'output' of A. 

    * A is 'parent' of B,C

    * C,B are 'children' of A.

    FINAL DECISION:
    All attributes are stored in the DbAttribute table.

    * internal attributes (that are used by the Data subclass and similar) are stored\
      starting with an underscore.\
      These (internal) attributes cannot be changed except when defining the object\
      the first time.

    * other attributes MUST start WITHOUT an underscore. These are user-defined and\
      can be appended even after the calculation has run, since they just are extras.

    * There is no json metadata attached to the DbNode entries. This can go into an attribute if needed.

    * Attributes in the DbAttribute table have to be thought as belonging to the DbNode,\
      and this is the reason for which there is no 'user' field in the DbAttribute field.

    * For a Data node, attributes will /define/ the data and hence should be immutable.\
      User-defined attributes are extras for convenience of tagging and searching only.\
      User should be careful not to attach data computed from data as extras. 
    '''
    uuid = UUIDField(auto=True)
    # in the form data.upffile., data.structure., calculation., code.quantumespresso.pw., ...
    # Note that there is always a final dot, to allow to do queries of the
    # type (type__startswith="calculation.") and avoid problems with classes
    # starting with the same string
    # max_length required for index by MySql
    type = m.CharField(max_length=255,db_index=True) 
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    # creation time
    ctime = m.DateTimeField(auto_now_add=True, editable=False)
    # last-modified time
    mtime = m.DateTimeField(auto_now=True, editable=False)
    # Cannot delete a user if something is associated to it
    user = m.ForeignKey(User, on_delete=m.PROTECT)

    # Direct links
    outputs = m.ManyToManyField('self', symmetrical=False, related_name='inputs', through='DbLink')  
    # Transitive closure
    children = m.ManyToManyField('self', symmetrical=False, related_name='parents', through='DbPath')
    
    # Used only if dbnode is a calculation, or remotedata
    dbcomputer = m.ForeignKey('DbComputer', null=True, on_delete=m.PROTECT)

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

    def get_simple_name(self, invalid_result=None):
        """
        Return a string with the last part of the type name.
        
        If the type is empty, use 'Node'.
        If the type is invalid, return the content of the input variable
        ``invalid_result``.
          
        :param invalid_result: The value to be returned if the node type is
            not recognized.
        """
        thistype = self.type
        # Fix for base class
        if thistype == "":
            thistype = "node.Node."
        if not thistype.endswith("."):
            return invalid_result
        else:
            thistype = thistype[:-1] # Strip final dot
            return thistype.rpartition('.')[2]
    
    def increment_version_number(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version
        (e.g. on adding a extra or attribute).

        :note: Do not manually increment the version number, because if
            two different threads are adding/changing an attribute concurrently,
            the version number would be incremented only once.
        """
        from django.db.models import F

        # I increment the node number using a filter
        # (this should be the right way of doing it;
        # dbnode.nodeversion  = F('nodeversion') + 1
        # will do weird stuff, returning Django Objects instead of numbers,
        # and incrementing at every save; moreover in this way I should do
        # the right thing for concurrent writings
        # I use self._dbnode because this will not do a query to
        # update the node; here I only need to get its pk
        self.nodeversion = F('nodeversion') + 1
        self.save()

    @python_2_unicode_compatible
    def __str__(self):
        simplename = self.get_simple_name(invalid_result="Unknown")
        # node pk + type
        if self.label:
            return "{} node [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} node [{}]".format(simplename, self.pk)

class DbLink(m.Model):
    '''
    Direct connection between two dbnodes. The label is identifying the
    link type.
    '''
    input = m.ForeignKey('DbNode',related_name='output_links')
    output = m.ForeignKey('DbNode',related_name='input_links')
    #label for data input for calculation
    label = m.CharField(max_length=255, db_index=True, blank=False)

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
        
    @python_2_unicode_compatible
    def __str__(self):
        return "{} ({}) --> {} ({})".format(
            self.input.get_simple_name(invalid_result="Unknown node"),
            self.input.pk,
            self.output.get_simple_name(invalid_result="Unknown node"),
            self.output.pk,)
            

class DbPath(m.Model):
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

    @python_2_unicode_compatible
    def __str__(self):
        return "{} ({}) ==[{}]==>> {} ({})".format(
            self.parent.get_simple_name(invalid_result="Unknown node"),
            self.parent.pk,
            self.depth,
            self.child.get_simple_name(invalid_result="Unknown node"),
            self.child.pk,)


attrdatatype_choice = (
    ('float', 'float'),
    ('int', 'int'),
    ('txt', 'txt'),
    ('bool', 'bool'),
    ('date', 'date'),
    ('json', 'json'),
    ('dict', 'dict'),
    ('list', 'list'),
    ('none', 'none'))

class DbAttributeBaseClass(m.Model):
    """
    Abstract base class for tables storing element-attribute-value data.
    Element is the dbnode; attribute is the key name.
    Value is the specific value to store. 
    
    This table had different SQL columns to store different types of data, and
    a datatype field to know the actual datatype.
    
    Moreover, this class unpacks dictionaries and lists when possible, so that
    it is possible to query inside recursive lists and dicts.
    """
    time = m.DateTimeField(auto_now_add=True, editable=False)
    # In this way, the related name for the DbAttribute inherited class will be
    # 'dbattributes' and for 'dbextra' will be 'dbextras'
    dbnode = m.ForeignKey('DbNode', related_name='%(class)ss') 
    # max_length is required by MySql to have indexes and unique constraints
    key = m.CharField(max_length=1024,db_index=True,blank=False)
    datatype = m.CharField(max_length=10, choices=attrdatatype_choice, db_index=True)
    tval = m.TextField( default='', blank=True)
    fval = m.FloatField( default=None, null=True)
    ival = m.IntegerField( default=None, null=True)
    bval = m.NullBooleanField(default=None, null=True)
    dval = m.DateTimeField(default=None, null=True)

    # separator for subfields
    _sep = "."
    
    class Meta:
        unique_together = (("dbnode", "key"))
        abstract = True
    
    @classmethod
    def list_all_node_elements(cls, dbnode):
        """
        Return a django queryset with the attributes of the given node,
        only at deepness level zero (i.e., keys not containing the separator).
        """
        from django.db.models import Q

        # This node, and does not contain the separator 
        # (=> show only level-zero entries)
        query = Q(dbnode=dbnode) & ~Q(key__contains=cls._sep)
        return cls.objects.filter(query)

    @classmethod
    def validate_key(cls, key):
        """
        Validate the key string to check if it is valid (e.g., if it does not
        contain the separator symbol.
        
        :return: None if the key is valid
        :raise ValueError: if the key is not valid
        """
        if cls._sep in key:
            raise ValueError("The separator symbol '{}' cannot be present "
                "in the key of a {}.".format(
                cls._sep, cls.__name__))

    @classmethod
    def get_value_for_node(cls, dbnode, key):
        """
        Get an attribute from the database for the given dbnode.
        
        :return: the value stored in the Db table, correctly converted 
            to the right type.
        :raise AttributeError: if no key is found for the given dbnode
        """        
        try:
            attr = cls.objects.get(dbnode=dbnode, key=key)
        except ObjectDoesNotExist:
            raise AttributeError("{} with key {} for node {} not found "
                "in db".format(cls.__name__, key, dbnode.pk))
        return attr.getvalue()

    @classmethod
    def set_value_for_node(cls, dbnode, key, value, incrementversion=True):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from (re)setting a valid key. 
        To be used only internally.

        :todo: there may be some error on concurrent write;
           not checked in this unlucky case!

        :param dbnode: the dbnode for which the attribute should be stored
        :param key: the key of the attribute to store
        :param value: the value of the attribute to store
        :param incrementversion : If incrementversion
          is True (default), each attribute set will
          udpate the version. This can be set to False during the store() so
          that the version does not get increased for each attribute.
        
        :raise ValueError: if the key contains the separator symbol used 
            internally to unpack dictionaries and lists (defined in cls._sep).
        """
        from django.db import transaction
        
        cls.validate_key(key)
        
        try:
            sid = transaction.savepoint()
            
            if incrementversion:
                dbnode.increment_version_number()
            attr, _ = cls.objects.get_or_create(dbnode=dbnode,
                                                       key=key)
            attr.setvalue(value)
        except:
            transaction.savepoint_rollback(sid)
            raise
    
    @classmethod
    def del_value_for_node(cls, dbnode, key):
        """
        Delete an attribute from the database for the given dbnode.
        
        :raise AttributeError: if no key is found for the given dbnode
        """
        dbnode.increment_version_number()
        try:
            # Call the delvalue method, that takes care of recursively deleting
            # the subattributes, if this is a list or dictionary.
            cls.objects.get(dbnode=dbnode, key=key).delvalue()
        except ObjectDoesNotExist:
            raise AttributeError("Cannot delete {} '{}' for node {}, "
                                 "not found in db".format(
                                 cls.__name__, key, dbnode.pk))
        
    def setvalue(self,value):
        """
        This can be called on a given row and will set the corresponding value.
        """
        import json
        import datetime 
        from django.utils.timezone import is_naive, make_aware, get_current_timezone
        from django.db import transaction
        
        with transaction.commit_on_success():
            # Needed, we call this function recursively; we cannot simply use
            sid = transaction.savepoint()
            try:
                # I have to delete the children to start with: if this was a 
                # dictionary or a list, I do not want to leave around pending
                # entries. This call will do nothing if the current entry is 
                # any other datatype
                self.delchildren()
    
                if value is None:
                    self.datatype = 'none'
                    self.bval = None
                    self.tval = ''
                    self.ival = None
                    self.fval = None
                    self.dval = None            
                    
                elif isinstance(value,bool):
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
    
                elif isinstance(value, list):
                                    
                    self.datatype = 'list'
                    self.dval = None
                    self.tval = ''
                    self.bval = None
                    self.ival = len(value)
                    self.fval = None
                    
                    for i, subv in enumerate(value):                           
                        item, _ = self.__class__.objects.get_or_create(
                            dbnode=self.dbnode,
                            key=("{}{}{:d}".format(self.key,self._sep, i)))
                        item.setvalue(subv)
                
                elif isinstance(value, dict):
                                    
                    self.datatype = 'dict'
                    self.dval = None
                    self.tval = ''
                    self.bval = None
                    self.ival = len(value)
                    self.fval = None
                    
                    for subk, subv in value.iteritems():
                        if self._sep in subk:
                            raise ValueError("You are trying to store an entry "
                                "that (maybe at an inner level) has"
                                "contains the character '{}', that "
                                "cannot be used".format(self._sep))
                            
                        item, _ = self.__class__.objects.get_or_create(
                            dbnode=self.dbnode,
                            key=(self.key + self._sep + subk))
                        item.setvalue(subv)
                    
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
            except:
                # Revert this inner transation, and reraise
                transaction.savepoint_rollback(sid)
                raise
        
    def getvalue(self):
        """
        This can be called on a given row and will get the corresponding value,
        casting it correctly
        """
        import json
        import re
    
        from django.utils.timezone import (
            is_naive, make_aware, get_current_timezone)

        from aiida.common import aiidalogger

        if self.datatype == 'none':
            return None
        elif self.datatype == 'bool':
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
        elif self.datatype == 'list':
            retlist = []
            regex_string = r"^{parentkey}{sep}([^{sep}])*$".format(
                    parentkey=re.escape(self.key),
                    sep=re.escape(self._sep))
            dbsubvalues = self.__class__.objects.filter(dbnode=self.dbnode,
                key__regex=regex_string).distinct()

            expected_set = set(["{}{}{:d}".format(self.key,self._sep,i)
                   for i in range(self.ival)])
            db_set = set(dbsubvalues.values_list('key',flat=True))
            # If there are more entries than expected, but all expected
            # ones are there, I just issue an error but I do not stop.
            if not expected_set.issubset(db_set):
                raise DbContentError("Wrong list elements stored in {} for "
                                     "node={} and key='{}' ({} vs {})".format(
                                     self.__class__.__name__, self.pk, self.key,
                                     expected_set, db_set))
            if expected_set != db_set:
                aiidalogger.error("Wrong list elements stored in {} for "
                                  "node={} and key='{}' ({} vs {})".format(
                                    self.__class__.__name__, self.pk, self.key,
                                    expected_set, db_set))                
            
            # I get the values in memory as a dictionary
            tempdict = {i.key: i.getvalue() for i in dbsubvalues}
            # And then I put them in a list
            retlist = [tempdict["{}{}{:d}".format(
                self.key, self._sep, i)] for i in range(self.ival)]
            return retlist
        elif self.datatype == 'dict':
            retdict = {}
            # Note: it may not be the most efficient way to do it
            # I need to look for all elements starting with the same key,
            # followed by the separator, followed by any number of non-separator
            # symbols
            regex_string = r"^{parentkey}{sep}([^{sep}])*$".format(
                    parentkey=re.escape(self.key),
                    sep=re.escape(self._sep))
            dbsubvalues = self.__class__.objects.filter(dbnode=self.dbnode,
                key__regex=regex_string).distinct()
            for subvalue in dbsubvalues:
                # I have to remove the length of the parent key + the length
                # of the separator (to be kept as a length-one string, possibly)
                subkey = subvalue.key[len(self.key)+len(self._sep):]
                retdict[subkey] = subvalue.getvalue()
            if len(dbsubvalues) != self.ival:
                aiidalogger.error("Wrong dict length stored in {} for "
                                  "node={} and key='{}' ({} vs {})".format(
                                    self.__class__.__name__, self.pk, self.key,
                                    len(retdict), self.ival))
            return retdict
        elif self.datatype == 'json':
            try:
                return json.loads(self.tval)
            except ValueError:
                raise DbContentError("Error in the content of the json field")
        else:
            raise DbContentError("The type field '{}' is not recognized".format(
                    self.datatype))        

    def delchildren(self):
        """
        Delete all children of this value *at any level of deepness*
        if it is a list or a dictionary, otherwise do nothing.
        Note that this is *not* done within a transaction: put a transaction
        in the caller (this is because the version of Django we are using
        does not support nested transactions properly.
        """
        if self.datatype == 'dict' or self.datatype == 'list':
            # Here, I have to delete all elements, to any deepness level!
            self.__class__.objects.filter(dbnode=self.dbnode, 
                key__startswith="{parentkey}{sep}".format(
                parentkey=self.key, sep=self._sep)).delete()

    def delvalue(self):
        """
        Deletes this value.
        """
        from django.db import transaction
        
        if self.datatype == 'dict' or self.datatype == 'list':
            with transaction.commit_on_success():
                # Here, I have to delete all elements, to any deepness level!
                self.delchildren()
                # Note! I cannot simply do a delete with a 
                # key__startswith=parentkey, because if I have an entry
                # called 'a' that is a list and another called 'ab', the
                # call would delete also 'ab'. Therefore, first I delete
                # all children, then the item itself.
                self.delete()
        else:
            self.delete()
    
    @python_2_unicode_compatible
    def __str__(self):
        return "[{} ({})].{} ({})".format(
            self.dbnode.get_simple_name(invalid_result="Unknown node"),
            self.dbnode.pk,
            self.key,
            self.datatype,)

class DbAttribute(DbAttributeBaseClass):
    """
    This table stores attributes that uniquely define the content of the
    node. Therefore, their modification corrupts the data.
    """
    pass

class DbExtra(DbAttributeBaseClass):
    """
    This table stores extra data, still in the key-value format,
    that the user can attach to a node.
    Therefore, their modification simply changes the user-defined data,
    but does not corrupt the node (it will still be loadable without errors).
    Could be useful to add "duplicate" information for easier querying, or
    for tagging nodes.
    """
    pass

class DbGroup(m.Model):
    """
    A group of nodes.
    
    Any group of nodes can be created, but some groups may have specific meaning
    if they satisfy specific rules (for instance, groups of UpdData objects are
    pseudopotential families - if no two pseudos are included for the same 
    atomic element).
    """
    uuid = UUIDField(auto=True)
    # max_length is required by MySql to have indexes and unique constraints
    name = m.CharField(max_length=255,unique=True, db_index=True)
    dbnodes = m.ManyToManyField('DbNode', related_name='dbgroups')
    time = m.DateTimeField(auto_now_add=True, editable=False)
    description = m.TextField(blank=True)
    user = m.ForeignKey(User)  # The owner of the group, not of the calculations

    @python_2_unicode_compatible
    def __str__(self):
        return self.name

class DbComputer(m.Model):
    """
    Table of computers or clusters.

    Attributes:
    * name: A name to be used to refer to this computer. Must be unique.
    * hostname: Fully-qualified hostname of the host
    * workdir: Full path of the aiida folder on the host. It can contain\
            the string {username} that will be substituted by the username\
            of the user on that machine.\
            The actual workdir is then obtained as\
            workdir.format(username=THE_ACTUAL_USERNAME)\
            Example: \
            workdir = "/scratch/{username}/aiida/"
    * transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:

        * mpirun command

        * num cores per node

        * max num cores

        * allocate full node = True or False

        * ... (further limits per user etc.)

    """
    #TODO: understand if we want that this becomes simply another type of dbnode.

    uuid = UUIDField(auto=True)
    name = m.CharField(max_length=255, unique=True, blank=False)
    hostname = m.CharField(max_length=255)
    description = m.TextField(blank=True)
    enabled = m.BooleanField(default=True)
    # TODO: next three fields should not be blank...
    workdir = m.CharField(max_length=255)
    transport_type = m.CharField(max_length=255)
    scheduler_type = m.CharField(max_length=255)
    transport_params = m.TextField(default="{}") # Will store a json
    metadata = m.TextField(default="{}") # Will store a json

    @classmethod
    def get_dbcomputer(cls,computer):
        """
        Return a DbComputer from its name (or from another Computer or DbComputer instance)
        """
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Computer

        if isinstance(computer, basestring):
            try:
                dbcomputer = DbComputer.objects.get(name=computer)
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

    @python_2_unicode_compatible
    def __str__(self):
        if self.enabled:
            return "{} ({})".format(self.name, self.hostname)
        else:
            return "{} ({}) [DISABLED]".format(self.name, self.hostname)


#class RunningJob(m.Model):
#    calc = m.OneToOneField(DbNode,related_name='jobinfo') # OneToOneField implicitly sets unique=True
#    calc_state = m.CharField(max_length=64)
#    job_id = m.TextField(blank=True)
#    scheduler_state = m.CharField(max_length=64,blank=True)
#    # Will store a json of the last JobInfo got from the scheduler
#    last_jobinfo = m.TextField(default='{}')  

class DbAuthInfo(m.Model):
    """
    Table that pairs aiida users and computers, with all required authentication
    information.
    """
    aiidauser = m.ForeignKey(User)
    dbcomputer = m.ForeignKey(DbComputer)
    auth_params = m.TextField(default='{}') # Will store a json; contains mainly the remoteuser
                                            # and the private_key

    class Meta:
        unique_together = (("aiidauser", "dbcomputer"),)

    def get_auth_params(self):
        import json
        try:
            return json.loads(self.auth_params)
        except ValueError:
            raise DbContentError(
                "Error while reading auth_params for authinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.username, self.dbcomputer.hostname))

    def set_auth_params(self,auth_params):
        import json
        
        # Raises ValueError if data is not JSON-serializable
        self.auth_params = json.dumps(auth_params)

    # a method of DbAuthInfo
    def get_transport(self):
        """
        Given a computer and an aiida user (as entries of the DB) return a configured
        transport to connect to the computer.
        """    
        from aiida.transport import TransportFactory
        from aiida.orm import Computer

        try:
            ThisTransport = TransportFactory(self.dbcomputer.transport_type)
        except MissingPluginError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.dbcomputer.hostname, self.dbcomputer.transport_type, e.message))

        params = dict(Computer(dbcomputer=self.dbcomputer).get_transport_params().items() +
                      self.get_auth_params().items())
        return ThisTransport(machine=self.dbcomputer.hostname,**params)

    @python_2_unicode_compatible
    def __str__(self):
        return "Authorization info for {}".format(self.dbcomputer.name)


class DbComment(m.Model):
    dbnode = m.ForeignKey(DbNode,related_name='dbcomments')
    time = m.DateTimeField(auto_now_add=True, editable=False)
    user = m.ForeignKey(User)
    content = m.TextField(blank=True)

    @python_2_unicode_compatible
    def __str__(self):
        return "DbComment for [{} {}] on {}".format(self.dbnode.get_simple_name(),
            self.dbnode.pk, self.time.strftime("%Y-%m-%d"))


#-------------------------------------
#         Lock
#-------------------------------------

class DbLock(m.Model):
    
    key        = m.TextField(primary_key=True)
    creation   = m.DateTimeField(auto_now_add=True, editable=False)
    timeout    = m.IntegerField(editable=False)
    owner      = m.CharField(max_length=255, blank=False)
            
#-------------------------------------
#         Workflows
#-------------------------------------

        
        
class DbWorkflow(m.Model):
    
    from aiida.common.datastructures import wf_states, wf_data_types
    
    uuid         = UUIDField(auto=True)
    ctime        = m.DateTimeField(auto_now_add=True, editable=False)
    mtime        = m.DateTimeField(auto_now=True, editable=False)    
    user         = m.ForeignKey(User, on_delete=m.PROTECT)

    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)

    # still to implement, similarly to the DbNode class
    nodeversion = m.IntegerField(default=1,editable=False)
    # to be implemented similarly to the DbNode class
    lastsyncedversion = m.IntegerField(default=0,editable=False)

    state        = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.INITIALIZED)
    report       = m.TextField(blank=True)

    # File variables, script is the complete dump of the workflow python script
    module       = m.TextField(blank=False)
    module_class = m.TextField(blank=False)
    script_path  = m.TextField(blank=False)
    script_md5   = m.CharField(max_length=255, blank=False)
        
    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()
    
    def get_aiida_class(self):
        
        """
        Return the corresponding aiida instance of class aiida.worflow
        """
        from aiida.orm.workflow import Workflow
        return Workflow(uuid=self.uuid)
    
    #  ------------------------------------------------
    
    def set_status(self, _status):
        
        self.state = _status;
        self.save()
    
    def set_script_md5(self, _md5):
        
        self.script_md5 = _md5
        self.save()
        
    # ------------------------------------------------
    #     Get data
    # ------------------------------------------------
        
    def add_data(self, dict, d_type):
        
        from django.db import transaction
        from aiida.common.datastructures import wf_states, wf_data_types
        
#         sid = transaction.savepoint()
        try:

            for k in dict.keys():
                p, create = self.data.get_or_create(name = k, data_type=d_type)
                p.set_value(dict[k])
                
#             transaction.savepoint_commit(sid)
            
        except Exception as e:
            raise
#             transaction.savepoint_rollback(sid)
            #raise ValueError("Error adding parameters")
    
    def get_data(self, d_type):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        
        try:
            dict = {}
            for p in self.data.filter(parent=self, data_type=d_type):
                dict[p.name] = p.get_value()
            return dict
        except Exception as e:
            raise
            #raise ValueError("Error retrieving parameters")
    
        
    # ------------------------------------------------
    #     Parameters, attributes, results
    # ------------------------------------------------

    def add_parameters(self, dict, force=False):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        
        if not self.state == wf_states.INITIALIZED and not force:
            raise ValueError("Cannot add initial parameters to an already initialized workflow")
        
        self.add_data(dict, wf_data_types.PARAMETER)
        
    def add_parameter(self, name, value):
        
        self.add_parameters({name:value})
        
        
    def get_parameters(self):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        return self.get_data(wf_data_types.PARAMETER)
    
    def get_parameter(self, name):
        
        res = self.get_parameters()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))
        
    # ------------------------------------------------
    
    def add_results(self, dict):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        self.add_data(dict, wf_data_types.RESULT)
        
    def add_result(self, name, value):
        
        self.add_results({name:value})
        
        
    def get_results(self):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        return self.get_data(wf_data_types.RESULT)
    
    def get_result(self, name):
        
        res = self.get_results()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))
    
    # ------------------------------------------------
    
    def add_attributes(self, dict):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        self.add_data(dict, wf_data_types.ATTRIBUTE)
        
    def add_attribute(self, name, value):
        
        self.add_attributes({name:value})
        
        
    def get_attributes(self):
        
        from aiida.common.datastructures import wf_states, wf_data_types
        return self.get_data(wf_data_types.ATTRIBUTE)
    
    def get_attribute(self, name):
        
        res = self.get_attributes()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))
          
    # ------------------------------------------------
    #     Reporting
    # ------------------------------------------------

    def clear_report(self):
        
        self.report = None
        self.save()
    
    def append_to_report(self, _text):
        
        from django.utils.timezone import utc
        import datetime
        
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.report += str(now)+"] "+_text+"\n";
        self.save()

    # ------------------------------------------------
    #     Calculations
    # ------------------------------------------------
            
    def get_calculations(self):
        
        from aiida.orm import Calculation
        return Calculation.query(workflow_step=self.steps)
    
    def get_calculations_status(self):

        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call

        calc_status = self.get_calculations().filter(
            dbattributes__key="state").values_list("uuid", "dbattributes__tval")
        return set([l[1] for l in calc_status])

    # ------------------------------------------------
    #     Subworkflows
    # ------------------------------------------------
    
    def get_sub_workflows(self):
        return DbWorkflow.objects.filter(parent_workflow_step=self.steps.all())
    
    def is_subworkflow(self):
        """
        Return True if this is a subworkflow, False if it is a root workflow,
        launched by the user.
        """
        return len(self.parent_workflow_step.all())>0
        
    def finish(self):
        from aiida.common.datastructures import wf_states
    
        self.state = wf_states.FINISHED

    @python_2_unicode_compatible
    def __str__(self):
        simplename = self.module_class
        # node pk + type
        if self.label:
            return "{} workflow [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} workflow [{}]".format(simplename, self.pk)


class DbWorkflowData(m.Model):
    
    from aiida.common.datastructures import wf_data_types, wf_data_value_types
    
    parent       = m.ForeignKey(DbWorkflow, related_name='data')
    name         = m.CharField(max_length=255, blank=False)
    time         = m.DateTimeField(auto_now_add=True, editable=False)
    data_type    = m.TextField(blank=False, default=wf_data_types.PARAMETER)
    
    value_type   = m.TextField(blank=False, default=wf_data_value_types.NONE)
    json_value   = m.TextField(blank=True)
    aiida_obj    = m.ForeignKey(DbNode, blank=True, null=True)
    
    class Meta:
        unique_together = (("parent", "name", "data_type"))
        
    def set_value(self, arg):
        
        import inspect
        from aiida.orm.node import Node
        from aiida.common.datastructures import wf_data_types, wf_data_value_types
        import json
        
        try:
            
            if isinstance(arg, Node) or issubclass(arg.__class__, Node):
                
                self.aiida_obj  = arg.dbnode
                self.value_type = wf_data_value_types.AIIDA
                self.save()
            else:
                
                self.json_value = json.dumps(arg)
                self.value_type = wf_data_value_types.JSON
                self.save()
                
        except:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))
        
    def get_value(self):
        
        import json
        from aiida.common.datastructures import wf_data_types, wf_data_value_types
        
        if self.value_type==wf_data_value_types.JSON:
            return json.loads(self.json_value)
        elif self.value_type==wf_data_value_types.AIIDA:
            return self.aiida_obj.get_aiida_class()
        elif self.value_type==wf_data_value_types.NONE:
            return None
        else:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))

    @python_2_unicode_compatible
    def __str__(self):
        return "Data for workflow {} [{}]: {}".format(
            self.parent.module_class, self.parent.pk, self.name)

           
class DbWorkflowStep(m.Model):

    from aiida.common.datastructures import wf_states, wf_exit_call, wf_default_call
    
    parent        = m.ForeignKey(DbWorkflow, related_name='steps')
    name          = m.CharField(max_length=255, blank=False)
    user          = m.ForeignKey(User, on_delete=m.PROTECT)
    time          = m.DateTimeField(auto_now_add=True, editable=False)
    nextcall      = m.CharField(max_length=255, blank=False, default=wf_default_call)
    
    calculations  = m.ManyToManyField(DbNode, symmetrical=False, related_name="workflow_step")
    sub_workflows = m.ManyToManyField(DbWorkflow, symmetrical=False, related_name="parent_workflow_step")
    
    
    state        = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.CREATED)

    class Meta:
        unique_together = (("parent", "name"))


    # ---------------------------------
    #    Calculations
    # ---------------------------------
    
    def add_calculation(self, step_calculation):
        
        from aiida.orm import Calculation

        if (not isinstance(step_calculation, Calculation)):
            raise ValueError("Cannot add a non-Calculation object to a workflow step")          

        try:
            self.calculations.add(step_calculation)
        except:
            raise ValueError("Error adding calculation to step")                      

    def get_calculations(self, state=None):
        
        from aiida.orm import Calculation
        
        if (state==None):
            return Calculation.query(workflow_step=self)#pk__in = step.calculations.values_list("pk", flat=True))
        else:
            return Calculation.query(workflow_step=self).filter(
                dbattributes__key="state",dbattributes__tval=state)

    def get_calculations_status(self):

        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call

        calc_status = self.calculations.filter(
            dbattributes__key="state").values_list("uuid", "dbattributes__tval")
        return set([l[1] for l in calc_status])
    
    def remove_calculations(self):
        
        self.calculations.all().delete()
        
    # ---------------------------------
    #    Subworkflows
    # ---------------------------------

    def add_sub_workflow(self, sub_wf):
        
        from aiida.orm.workflow import Workflow
        
        if (not issubclass(sub_wf.__class__,Workflow) and not isinstance(sub_wf, Workflow)):
            raise ValueError("Cannot add a workflow not of type Workflow")                        

        try:
            self.sub_workflows.add(sub_wf.dbworkflowinstance)
        except:
            raise ValueError("Error adding calculation to step")                      
 
    def get_sub_workflows(self):
        
        from aiida.orm.workflow import Workflow
        return Workflow.query(uuid__in=self.sub_workflows.values_list("uuid", flat=True))
        #return self.sub_workflows.all()#pk__in = step.calculations.values_list("pk", flat=True))
 
    def get_sub_workflows_status(self):
        
        from aiida.common.datastructures import wf_states
        
        wf_status = self.sub_workflows.all().values_list("uuid", "status")
        return set([l[1] for l in wf_status])
    
    def remove_sub_workflows(self):
        
        self.sub_workflows.all().delete()
    
    # ---------------------------------
    #    Management
    # ---------------------------------

    def is_finished(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        
        return self.state==wf_states.FINISHED
        
    def set_nextcall(self, _nextcall):
        
        self.nextcall = _nextcall;
        self.save()
        
    def set_status(self, _status):
        
        self.state = _status;
        self.save()
        
    def reinitialize(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        self.set_status(wf_states.INITIALIZED)

    def finish(self):
        
        from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
        self.set_status(wf_states.FINISHED)


    @python_2_unicode_compatible
    def __str__(self):
        return "Step {} for workflow {} [{}]".format(self.name,
            self.parent.module_class, self.parent.pk)
