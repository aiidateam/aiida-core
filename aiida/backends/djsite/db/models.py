# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys

from six import reraise
from django.db import models as m
from django_extensions.db.fields import UUIDField
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet

from aiida.utils import timezone
from aiida.common.exceptions import (
    ConfigurationError, DbContentError, MissingPluginError)

from aiida.backends.settings import AIIDANODES_UUID_VERSION
from aiida.backends.djsite.settings.settings import AUTH_USER_MODEL
import aiida.backends.djsite.db.migrations as migrations
from aiida.backends.utils import AIIDA_ATTRIBUTE_SEP

# This variable identifies the schema version of this file.
# Every time you change the schema below in *ANY* way, REMEMBER TO CHANGE
# the version here in the migration file and update migrations/__init__.py.
# See the documentation for how to do all this.
#
# The version is checked at code load time to verify that the code schema
# version and the DB schema version are the same. (The DB schema version
# is stored in the DbSetting table and the check is done in the
# load_dbenv() function).
SCHEMA_VERSION = migrations.current_schema_version()


class AiidaQuerySet(QuerySet):
    def iterator(self):
        for obj in super(AiidaQuerySet, self).iterator():
            yield obj.get_aiida_class()


class AiidaObjectManager(m.Manager):
    def get_query_set(self):
        return AiidaQuerySet(self.model, using=self._db)


class DbUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email (that is the
        username) and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = BaseUserManager.normalize_email(email)
        user = self.model(email=email,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, date_joined=now, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class DbUser(AbstractBaseUser, PermissionsMixin):
    """
    This class replaces the default User class of Django
    """
    # Set unique email field
    email = m.EmailField(unique=True, db_index=True)
    first_name = m.CharField(max_length=254, blank=True)
    last_name = m.CharField(max_length=254, blank=True)
    institution = m.CharField(max_length=254, blank=True)

    is_staff = m.BooleanField(default=False,
                              help_text='Designates whether the user can log into this admin '
                                        'site.')
    is_active = m.BooleanField(default=True,
                               help_text='Designates whether this user should be treated as '
                                         'active. Unselect this instead of deleting accounts.')
    date_joined = m.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    objects = DbUserManager()

    def get_full_name(self):
        if self.first_name and self.last_name:
            return "{} {} ({})".format(self.first_name, self.last_name,
                                       self.email)
        elif self.first_name:
            return "{} ({})".format(self.first_name, self.email)
        elif self.last_name:
            return "{} ({})".format(self.last_name, self.email)
        else:
            return "{}".format(self.email)

    def get_short_name(self):
        return self.email

    def get_aiida_class(self):
        from aiida.orm.user import User
        return User(dbuser=self)


@python_2_unicode_compatible
class DbNode(m.Model):
    """
    Generic node: data or calculation or code.

    Nodes can be linked (DbLink table)
    Naming convention for Node relationships: A --> C --> B.

    * A is 'input' of C.
    * C is 'output' of A.
    * A is 'parent' of B,C
    * C,B are 'children' of A.

    :note: parents and children are stored in the DbPath table, the transitive
      closure table, automatically updated via DB triggers whenever a link is
      added to or removed from the DbLink table.

    Internal attributes, that define the node itself,
    are stored in the DbAttribute table; further user-defined attributes,
    called 'extra', are stored in the DbExtra table (same schema and methods
    of the DbAttribute table, but the code does not rely on the content of the
    table, therefore the user can use it at his will to tag or annotate nodes.

    :note: Attributes in the DbAttribute table have to be thought as belonging
       to the DbNode, (this is the reason for which there is no 'user' field
       in the DbAttribute field). Moreover, Attributes define uniquely the
       Node so should be immutable (except for the few ones defined in the
       _updatable_attributes attribute of the Node() class, that are updatable:
       these are Attributes that are set by AiiDA, so the user should not
       modify them, but can be changed (e.g., the append_text of a code, that
       can be redefined if the code has to be recompiled).
    """
    uuid = UUIDField(auto=True, version=AIIDANODES_UUID_VERSION, db_index=True)
    # in the form data.upffile., data.structure., calculation., code.quantumespresso.pw., ...
    # Note that there is always a final dot, to allow to do queries of the
    # type (type__startswith="calculation.") and avoid problems with classes
    # starting with the same string
    # max_length required for index by MySql
    type = m.CharField(max_length=255, db_index=True)
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    # creation time
    ctime = m.DateTimeField(default=timezone.now, editable=False)
    mtime = m.DateTimeField(auto_now=True, editable=False)
    # Cannot delete a user if something is associated to it
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.PROTECT,
                        related_name='dbnodes')

    # Direct links
    outputs = m.ManyToManyField('self', symmetrical=False,
                                related_name='inputs', through='DbLink')
    # Transitive closure
    children = m.ManyToManyField('self', symmetrical=False,
                                 related_name='parents', through='DbPath')

    # Used only if dbnode is a calculation, or remotedata
    # Avoid that computers can be deleted if at least a node exists pointing
    # to it.
    dbcomputer = m.ForeignKey('DbComputer', null=True, on_delete=m.PROTECT,
                              related_name='dbnodes')

    # Index that is incremented every time a modification is done on itself or on attributes.
    # Managed by the aiida.orm.Node class. Do not modify
    nodeversion = m.IntegerField(default=1, editable=False)

    # For the API: whether this node
    public = m.BooleanField(default=False)

    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()

    def get_aiida_class(self):
        """
        Return the corresponding aiida instance of class aiida.orm.Node or a
        appropriate subclass.
        """
        from aiida.orm.node import Node
        from aiida.common.old_pluginloader import from_type_to_pluginclassname
        from aiida.common.pluginloader import load_plugin
        from aiida.common import aiidalogger

        try:
            pluginclassname = from_type_to_pluginclassname(self.type)
        except DbContentError:
            raise DbContentError("The type name of node with pk= {} is "
                                 "not valid: '{}'".format(self.pk, self.type))

        try:
            PluginClass = load_plugin(Node, 'aiida.orm', pluginclassname)
        except MissingPluginError:
            aiidalogger.error("Unable to find plugin for type '{}' (node= {}), "
                              "will use base Node class".format(self.type, self.pk))
            PluginClass = Node

        return PluginClass(dbnode=self)

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
            thistype = thistype[:-1]  # Strip final dot
            return thistype.rpartition('.')[2]

    @property
    def attributes(self):
        """
        Return all attributes of the given node as a single dictionary.
        """
        return DbAttribute.get_all_values_for_node(self)

    @property
    def extras(self):
        """
        Return all extras of the given node as a single dictionary.
        """
        return DbExtra.get_all_values_for_node(self)

    def __str__(self):
        simplename = self.get_simple_name(invalid_result="Unknown")
        # node pk + type
        if self.label:
            return "{} node [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} node [{}]".format(simplename, self.pk)


@python_2_unicode_compatible
class DbLink(m.Model):
    """
    Direct connection between two dbnodes. The label is identifying the
    link type.
    """
    # If I delete an output, delete also the link; if I delete an input, stop
    # NOTE: this will in most cases render a DbNode.objects.filter(...).delete()
    # call unusable because some nodes will be inputs; Nodes will have to
    #    be deleted in the proper order (or links will need to be deleted first)
    input = m.ForeignKey('DbNode', related_name='output_links',
                         on_delete=m.PROTECT)
    output = m.ForeignKey('DbNode', related_name='input_links',
                          on_delete=m.CASCADE)
    # label for data input for calculation
    label = m.CharField(max_length=255, db_index=True, blank=False)
    type = m.CharField(max_length=255, db_index=True, blank=True)

    class Meta:
        # I cannot add twice the same link
        # I want unique labels among all inputs of a node
        # NOTE!
        # I cannot add ('input', 'label') because in general
        # if the input is a 'data' and I want to add it more than
        # once to different calculations, the different links must be
        # allowed to have the same name. For calculations, it is the
        # responsibility of the output plugin to avoid to have many
        # times the same name.
        #
        # A calculation can have both a 'return' and a 'create' link to
        # a single data output node, which would violate the unique constraint
        # defined below, since the difference in link type is not considered.
        # The distinction between the type of a 'create' and a 'return' link is not
        # implemented at the moment, so the unique constraint is disabled.
        # unique_together = ("output", "label")
        pass

    def __str__(self):
        return "{} ({}) --> {} ({})".format(
            self.input.get_simple_name(invalid_result="Unknown node"),
            self.input.pk,
            self.output.get_simple_name(invalid_result="Unknown node"),
            self.output.pk, )


@python_2_unicode_compatible
class DbPath(m.Model):
    """
    Transitive closure table for all dbnode paths.
    """
    parent = m.ForeignKey('DbNode', related_name='child_paths', editable=False)
    child = m.ForeignKey('DbNode', related_name='parent_paths', editable=False)
    depth = m.IntegerField(editable=False)

    # Used to delete or to expand the path
    entry_edge_id = m.IntegerField(null=True, editable=False)
    direct_edge_id = m.IntegerField(null=True, editable=False)
    exit_edge_id = m.IntegerField(null=True, editable=False)

    def __str__(self):
        return "{} ({}) ==[{}]==>> {} ({})".format(
            self.parent.get_simple_name(invalid_result="Unknown node"),
            self.parent.pk,
            self.depth,
            self.child.get_simple_name(invalid_result="Unknown node"),
            self.child.pk, )

    def expand(self):
        """
        Method to expand a DbPath (recursive function), i.e., to get a list
        of all dbnodes that are traversed in the given path.

        :return: list of DbNode objects representing the expanded DbPath
        """

        if self.depth == 0:
            return [self.parent, self.child]
        else:
            path_entry = []
            path_direct = DbPath.objects.get(id=self.direct_edge_id).expand()
            path_exit = []
            # we prevent DbNode repetitions
            if self.entry_edge_id != self.direct_edge_id:
                path_entry = DbPath.objects.get(id=self.entry_edge_id).expand()[:-1]
            if self.exit_edge_id != self.direct_edge_id:
                path_exit = DbPath.objects.get(id=self.exit_edge_id).expand()[1:]

            return path_entry + path_direct + path_exit


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

from aiida.common.exceptions import AiidaException


class DeserializationException(AiidaException):
    pass


def _deserialize_attribute(mainitem, subitems, sep, original_class=None,
                           original_pk=None, lesserrors=False):
    """
    Deserialize a single attribute.

    :param mainitem: the main item (either the attribute itself for base
      types (None, string, ...) or the main item for lists and dicts.
      Must contain the 'key' key and also the following keys:
      datatype, tval, fval, ival, bval, dval.
      NOTE that a type check is not performed! tval is expected to be a string,
      dval a date, etc.
    :param subitems: must be a dictionary of dictionaries. In the top-level dictionary,
      the key must be the key of the attribute, stripped of all prefixes
      (i.e., if the mainitem has key 'a.b' and we pass subitems
        'a.b.0', 'a.b.1', 'a.b.1.c', their keys must be '0', '1', '1.c').
        It must be None if the value is not iterable (int, str,
        float, ...).
        It is an empty dictionary if there are no subitems.
    :param sep: a string, the separator between subfields (to separate the
      name of a dictionary from the keys it contains, for instance)
    :param original_class: if these elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass, pass here the class (note: the class,
      not the instance!). This is used only in case the wrong number of elements
      is found in the raw data, to print a more meaningful message (if the class
      has a dbnode associated to it)
    :param original_pk: if the elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass that has a dbnode associated to it,
      pass here the PK integer. This is used only in case the wrong number
      of elements is found in the raw data, to print a more meaningful message
    :param lesserrors: If set to True, in some cases where the content of the
      DB is not consistent but data is still recoverable,
      it will just log the message rather than raising
      an exception (e.g. if the number of elements of a dictionary is different
      from the number declared in the ival field).

    :return: the deserialized value
    :raise DeserializationError: if an error occurs
    """
    from aiida.utils.timezone import (
        is_naive, make_aware, get_current_timezone)
    import json

    from aiida.common import aiidalogger

    if mainitem['datatype'] == 'none':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return None
    elif mainitem['datatype'] == 'bool':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['bval']
    elif mainitem['datatype'] == 'int':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['ival']
    elif mainitem['datatype'] == 'float':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['fval']
    elif mainitem['datatype'] == 'txt':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['tval']
    elif mainitem['datatype'] == 'date':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        if is_naive(mainitem['dval']):
            return make_aware(mainitem['dval'], get_current_timezone())
        else:
            return mainitem['dval']

    elif mainitem['datatype'] == 'list':
        # subitems contains all subitems, here I store only those of
        # deepness 1, i.e. if I have subitems '0', '1' and '1.c' I
        # store only '0' and '1'
        firstlevelsubdict = {k: v for k, v in subitems.iteritems()
                             if sep not in k}

        # For checking, I verify the expected values
        expected_set = set(["{:d}".format(i)
                            for i in range(mainitem['ival'])])
        received_set = set(firstlevelsubdict.keys())
        # If there are more entries than expected, but all expected
        # ones are there, I just issue an error but I do not stop.

        if not expected_set.issubset(received_set):
            if (original_class is not None and original_class._subspecifier_field_name is not None):
                subspecifier_string = "{}={} and ".format(
                    original_class._subspecifier_field_name,
                    original_pk)
            else:
                subspecifier_string = ""
            if original_class is None:
                sourcestr = "the data passed"
            else:
                sourcestr = original_class.__name__

            raise DeserializationException("Wrong list elements stored in {} for "
                                           "{}key='{}' ({} vs {})".format(
                sourcestr,
                subspecifier_string,
                mainitem['key'], expected_set, received_set))
        if expected_set != received_set:
            if (original_class is not None and
                        original_class._subspecifier_field_name is not None):
                subspecifier_string = "{}={} and ".format(
                    original_class._subspecifier_field_name,
                    original_pk)
            else:
                subspecifier_string = ""
            if original_class is None:
                sourcestr = "the data passed"
            else:
                sourcestr = original_class.__name__

            msg = ("Wrong list elements stored in {} for "
                   "{}key='{}' ({} vs {})".format(
                sourcestr,
                subspecifier_string,
                mainitem['key'], expected_set, received_set))
            if lesserrors:
                aiidalogger.error(msg)
            else:
                raise DeserializationException(msg)

        # I get the values in memory as a dictionary
        tempdict = {}
        for firstsubk, firstsubv in firstlevelsubdict.iteritems():
            # I call recursively the same function to get subitems
            newsubitems = {k[len(firstsubk) + len(sep):]: v
                           for k, v in subitems.iteritems()
                           if k.startswith(firstsubk + sep)}
            tempdict[firstsubk] = _deserialize_attribute(mainitem=firstsubv,
                                                         subitems=newsubitems, sep=sep, original_class=original_class,
                                                         original_pk=original_pk)

        # And then I put them in a list
        retlist = [tempdict["{:d}".format(i)] for i in range(mainitem['ival'])]
        return retlist
    elif mainitem['datatype'] == 'dict':
        # subitems contains all subitems, here I store only those of
        # deepness 1, i.e. if I have subitems '0', '1' and '1.c' I
        # store only '0' and '1'
        firstlevelsubdict = {k: v for k, v in subitems.iteritems()
                             if sep not in k}

        if len(firstlevelsubdict) != mainitem['ival']:
            if (original_class is not None and
                        original_class._subspecifier_field_name is not None):
                subspecifier_string = "{}={} and ".format(
                    original_class._subspecifier_field_name,
                    original_pk)
            else:
                subspecifier_string = ""
            if original_class is None:
                sourcestr = "the data passed"
            else:
                sourcestr = original_class.__name__

            msg = ("Wrong dict length stored in {} for "
                   "{}key='{}' ({} vs {})".format(
                sourcestr,
                subspecifier_string,
                mainitem['key'], len(firstlevelsubdict),
                mainitem['ival']))
            if lesserrors:
                aiidalogger.error(msg)
            else:
                raise DeserializationException(msg)

        # I get the values in memory as a dictionary
        tempdict = {}
        for firstsubk, firstsubv in firstlevelsubdict.iteritems():
            # I call recursively the same function to get subitems
            newsubitems = {k[len(firstsubk) + len(sep):]: v
                           for k, v in subitems.iteritems()
                           if k.startswith(firstsubk + sep)}
            tempdict[firstsubk] = _deserialize_attribute(mainitem=firstsubv,
                                                         subitems=newsubitems, sep=sep, original_class=original_class,
                                                         original_pk=original_pk)

        return tempdict
    elif mainitem['datatype'] == 'json':
        try:
            return json.loads(mainitem['tval'])
        except ValueError:
            raise DeserializationException("Error in the content of the json field")
    else:
        raise DeserializationException("The type field '{}' is not recognized".format(
            mainitem['datatype']))


def deserialize_attributes(data, sep, original_class=None, original_pk=None):
    """
    Deserialize the attributes from the format internally stored in the DB
    to the actual format (dictionaries, lists, integers, ...

    :param data: must be a dictionary of dictionaries. In the top-level dictionary,
      the key must be the key of the attribute. The value must be a dictionary
      with the following keys: datatype, tval, fval, ival, bval, dval. Other
      keys are ignored.
      NOTE that a type check is not performed! tval is expected to be a string,
      dval a date, etc.
    :param sep: a string, the separator between subfields (to separate the
      name of a dictionary from the keys it contains, for instance)
    :param original_class: if these elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass, pass here the class (note: the class,
      not the instance!). This is used only in case the wrong number of elements
      is found in the raw data, to print a more meaningful message (if the class
      has a dbnode associated to it)
    :param original_pk: if the elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass that has a dbnode associated to it,
      pass here the PK integer. This is used only in case the wrong number
      of elements is found in the raw data, to print a more meaningful message

    :return: a dictionary, where for each entry the corresponding value is
      returned, deserialized back to lists, dictionaries, etc.
      Example: if ``data = {'a': {'datatype': "list", "ival": 2, ...},
      'a.0': {'datatype': "int", "ival": 2, ...},
      'a.1': {'datatype': "txt", "tval":  "yy"}]``,
      it will return ``{"a": [2, "yy"]}``
    """
    from collections import defaultdict

    # I group results by zero-level entity
    found_mainitems = {}
    found_subitems = defaultdict(dict)
    for mainkey, descriptiondict in data.iteritems():
        prefix, thissep, postfix = mainkey.partition(sep)
        if thissep:
            found_subitems[prefix][postfix] = {k: v for k, v
                                               in descriptiondict.iteritems() if k != "key"}
        else:
            mainitem = descriptiondict.copy()
            mainitem['key'] = prefix
            found_mainitems[prefix] = mainitem

    # There can be mainitems without subitems, but there should not be subitems
    # without mainitmes.
    lone_subitems = set(found_subitems.keys()) - set(found_mainitems.keys())
    if lone_subitems:
        raise DeserializationException("Missing base keys for the following "
                                       "items: {}".format(",".join(lone_subitems)))

    # For each zero-level entity, I call the _deserialize_attribute function
    retval = {}
    for k, v in found_mainitems.iteritems():
        # Note: found_subitems[k] will return an empty dictionary it the
        # key does not exist, as it is a defaultdict
        retval[k] = _deserialize_attribute(mainitem=v,
                                           subitems=found_subitems[k], sep=sep, original_class=original_class,
                                           original_pk=original_pk)

    return retval


class DbMultipleValueAttributeBaseClass(m.Model):
    """
    Abstract base class for tables storing attribute + value data, of
    different data types (without any association to a Node).
    """
    from aiida.backends.djsite.utils import long_field_length

    key = m.CharField(max_length=long_field_length(), db_index=True, blank=False)
    datatype = m.CharField(max_length=10,
                           default='none',
                           choices=attrdatatype_choice, db_index=True)
    tval = m.TextField(default='', blank=True)
    fval = m.FloatField(default=None, null=True)
    ival = m.IntegerField(default=None, null=True)
    bval = m.NullBooleanField(default=None, null=True)
    dval = m.DateTimeField(default=None, null=True)

    # separator for subfields
    _sep = AIIDA_ATTRIBUTE_SEP

    class Meta:
        abstract = True
        unique_together = (('key',),)

    # There are no subspecifiers. If instead you want to group attributes
    # (e.g. by node, as it is done in the DbAttributeBaseClass), specify here
    # the field name
    _subspecifier_field_name = None

    @property
    def subspecifiers_dict(self):
        """
        Return a dict to narrow down the query to only those matching also the
        subspecifier.
        """
        if self._subspecifier_field_name is None:
            return {}
        else:
            return {self._subspecifier_field_name:
                        getattr(self, self._subspecifier_field_name)}

    @property
    def subspecifier_pk(self):
        """
        Return the subspecifier PK in the database (or None, if no
        subspecifier should be used)
        """
        if self._subspecifier_field_name is None:
            return None
        else:
            return getattr(self, self._subspecifier_field_name).pk

    @classmethod
    def validate_key(cls, key):
        """
        Validate the key string to check if it is valid (e.g., if it does not
        contain the separator symbol.).

        :return: None if the key is valid
        :raise ValidationError: if the key is not valid
        """
        from aiida.backends.utils import validate_attribute_key
        return validate_attribute_key(key)

    @classmethod
    def set_value(cls, key, value, with_transaction=True,
                  subspecifier_value=None, other_attribs={},
                  stop_if_existing=False):
        """
        Set a new value in the DB, possibly associated to the given subspecifier.

        :note: This method also stored directly in the DB.

        :param key: a string with the key to create (must be a level-0
          attribute, that is it cannot contain the separator cls._sep).
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param with_transaction: True if you want this function to be managed
          with transactions. Set to False if you already have a manual
          management of transactions in the block where you are calling this
          function (useful for speed improvements to avoid recursive
          transactions)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).
        :param stop_if_existing: if True, it will stop with an
           UniquenessError exception if the new entry would violate an
           uniqueness constraint in the DB (same key, or same key+node,
           depending on the specific subclass). Otherwise, it will
           first delete the old value, if existent. The use with True is
           useful if you want to use a given attribute as a "locking" value,
           e.g. to avoid to perform an action twice on the same node.
           Note that, if you are using transactions, you may get the error
           only when the transaction is committed.
        """
        from django.db import transaction

        cls.validate_key(key)

        try:
            if with_transaction:
                sid = transaction.savepoint()

            # create_value returns a list of nodes to store
            to_store = cls.create_value(key, value,
                                        subspecifier_value=subspecifier_value,
                                        other_attribs=other_attribs)

            if to_store:
                if not stop_if_existing:
                    # Delete the olf values if stop_if_existing is False,
                    # otherwise don't delete them and hope they don't
                    # exist. If they exist, I'll get an UniquenessError

                    ## NOTE! Be careful in case the extra/attribute to
                    ## store is not a simple attribute but a list or dict:
                    ## like this, it should be ok because if we are
                    ## overwriting an entry it will stop anyway to avoid
                    ## to overwrite the main entry, but otherwise
                    ## there is the risk that trailing pieces remain
                    ## so in general it is good to recursively clean
                    ## all sub-items.
                    cls.del_value(key,
                                  subspecifier_value=subspecifier_value)
                cls.objects.bulk_create(to_store)

            if with_transaction:
                transaction.savepoint_commit(sid)
        except BaseException as e:  # All exceptions including CTRL+C, ...
            from django.db.utils import IntegrityError
            from aiida.common.exceptions import UniquenessError

            if with_transaction:
                transaction.savepoint_rollback(sid)
            if isinstance(e, IntegrityError) and stop_if_existing:
                raise UniquenessError("Impossible to create the required "
                                      "entry "
                                      "in table '{}', "
                                      "another entry already exists and the creation would "
                                      "violate an uniqueness constraint.\nFurther details: "
                                      "{}".format(
                    cls.__name__, e.message))
            raise

    @classmethod
    def create_value(cls, key, value, subspecifier_value=None,
                     other_attribs={}):
        """
        Create a new list of attributes, without storing them, associated
        with the current key/value pair (and to the given subspecifier,
        e.g. the DbNode for DbAttributes and DbExtras).

        :note: No hits are done on the DB, in particular no check is done
          on the existence of the given nodes.

        :param key: a string with the key to create (can contain the
          separator cls._sep if this is a sub-attribute: indeed, this
          function calls itself recursively)
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).

        :return: always a list of class instances; it is the user
          responsibility to store such entries (typically with a Django
          bulk_create() call).
        """
        import json
        import datetime
        from aiida.utils.timezone import is_naive, make_aware, get_current_timezone

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            new_entry = cls(key=key, **other_attribs)
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                cls._subspecifier_field_name))
            further_params = other_attribs.copy()
            further_params.update({cls._subspecifier_field_name:
                                       subspecifier_value})
            new_entry = cls(key=key, **further_params)

        list_to_return = [new_entry]

        if value is None:
            new_entry.datatype = 'none'
            new_entry.bval = None
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, bool):
            new_entry.datatype = 'bool'
            new_entry.bval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, (int, long)):
            new_entry.datatype = 'int'
            new_entry.ival = value
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, float):
            new_entry.datatype = 'float'
            new_entry.fval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.bval = None
            new_entry.dval = None

        elif isinstance(value, basestring):
            new_entry.datatype = 'txt'
            new_entry.tval = value
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, datetime.datetime):

            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value

            new_entry.datatype = 'date'
            # TODO: time-aware and time-naive datetime objects, see
            # https://docs.djangoproject.com/en/dev/topics/i18n/timezones/#naive-and-aware-datetime-objects
            new_entry.dval = value_to_set
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        elif isinstance(value, (list, tuple)):

            new_entry.datatype = 'list'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for i, subv in enumerate(value):
                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(cls.create_value(
                    key=("{}{}{:d}".format(key, cls._sep, i)),
                    value=subv,
                    subspecifier_value=subspecifier_value))

        elif isinstance(value, dict):

            new_entry.datatype = 'dict'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for subk, subv in value.iteritems():
                cls.validate_key(subk)

                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(cls.create_value(
                    key="{}{}{}".format(key, cls._sep, subk),
                    value=subv,
                    subspecifier_value=subspecifier_value))
        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError("Unable to store the value: it must be "
                                 "either a basic datatype, or json-serializable")

            new_entry.datatype = 'json'
            new_entry.tval = jsondata
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        return list_to_return

    @classmethod
    def get_query_dict(cls, value):
        """
        Return a dictionary that can be used in a django filter to query
        for a specific value. This takes care of checking the type of the
        input parameter 'value' and to convert it to the right query.

        :param value: The value that should be queried. Note: can only be
           base datatype, not a list or dict. For those, query directly for
           one of the sub-elements.

        :todo: see if we want to give the possibility to query for the existence
           of a (possibly empty) dictionary or list, of for their length.

        :note: this will of course not find a data if this was stored in the
           DB as a serialized JSON.

        :return: a dictionary to be used in the django .filter() method.
            For instance, if 'value' is a string, it will return the dictionary
            ``{'datatype': 'txt', 'tval': value}``.

        :raise: ValueError if value is not of a base datatype (string, integer,
            float, bool, None, or date)
        """
        import datetime
        from aiida.utils.timezone import (
            is_naive, make_aware, get_current_timezone)

        if value is None:
            return {'datatype': 'none'}
        elif isinstance(value, bool):
            return {'datatype': 'bool', 'bval': value}
        elif isinstance(value, (int, long)):
            return {'datatype': 'int', 'ival': value}
        elif isinstance(value, float):
            return {'datatype': 'float', 'fval': value}
        elif isinstance(value, basestring):
            return {'datatype': 'txt', 'tval': value}
        elif isinstance(value, datetime.datetime):
            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value
            return {'datatype': 'date', 'dval': value_to_set}
        elif isinstance(value, list):
            raise ValueError("Lists are not supported for getting the "
                             "query_dict")
        elif isinstance(value, dict):
            raise ValueError("Dicts are not supported for getting the "
                             "query_dict")
        else:
            raise ValueError("Unsupported type for getting the "
                             "query_dict, it is {}".format(str(type(value))))

    def getvalue(self):
        """
        This can be called on a given row and will get the corresponding value,
        casting it correctly.
        """
        try:
            if self.datatype == 'list' or self.datatype == 'dict':
                prefix = "{}{}".format(self.key, self._sep)
                prefix_len = len(prefix)
                dballsubvalues = self.__class__.objects.filter(
                    key__startswith=prefix,
                    **self.subspecifiers_dict).values_list('key',
                                                           'datatype', 'tval', 'fval',
                                                           'ival', 'bval', 'dval')
                # Strip the FULL prefix and replace it with the simple
                # "attr" prefix
                data = {"attr.{}".format(_[0][prefix_len:]): {
                    "datatype": _[1],
                    "tval": _[2],
                    "fval": _[3],
                    "ival": _[4],
                    "bval": _[5],
                    "dval": _[6],
                } for _ in dballsubvalues
                        }
                # for _ in dballsubvalues}
                # Append also the item itself
                data["attr"] = {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": self.datatype,
                    "tval": self.tval,
                    "fval": self.fval,
                    "ival": self.ival,
                    "bval": self.bval,
                    "dval": self.dval}
                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self.__class__,
                                              original_pk=self.subspecifier_pk)['attr']
            else:
                data = {"attr": {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": self.datatype,
                    "tval": self.tval,
                    "fval": self.fval,
                    "ival": self.ival,
                    "bval": self.bval,
                    "dval": self.dval}}

                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self.__class__,
                                              original_pk=self.subspecifier_pk)['attr']
        except DeserializationException as e:
            exc = DbContentError(e.message)
            exc.original_exception = e
            raise exc

    @classmethod
    def del_value(cls, key, only_children=False, subspecifier_value=None):
        """
        Delete a value associated with the given key (if existing).

        :note: No exceptions are raised if no entry is found.

        :param key: the key to delete. Can contain the separator cls._sep if
          you want to delete a subkey.
        :param only_children: if True, delete only children and not the
          entry itself.
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        """
        from django.db.models import Q

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            subspecifiers_dict = {}
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                cls._subspecifier_field_name))
            subspecifiers_dict = {cls._subspecifier_field_name:
                                      subspecifier_value}

        query = Q(key__startswith="{parentkey}{sep}".format(
            parentkey=key, sep=cls._sep),
            **subspecifiers_dict)

        if not only_children:
            query.add(Q(key=key, **subspecifiers_dict), Q.OR)

        cls.objects.filter(query).delete()


@python_2_unicode_compatible
class DbAttributeBaseClass(DbMultipleValueAttributeBaseClass):
    """
    Abstract base class for tables storing element-attribute-value data.
    Element is the dbnode; attribute is the key name.
    Value is the specific value to store.

    This table had different SQL columns to store different types of data, and
    a datatype field to know the actual datatype.

    Moreover, this class unpacks dictionaries and lists when possible, so that
    it is possible to query inside recursive lists and dicts.
    """
    # In this way, the related name for the DbAttribute inherited class will be
    # 'dbattributes' and for 'dbextra' will be 'dbextras'
    # Moreover, automatically destroy attributes and extras if the parent
    # node is deleted
    dbnode = m.ForeignKey('DbNode', related_name='%(class)ss', on_delete=m.CASCADE)
    # max_length is required by MySql to have indexes and unique constraints

    _subspecifier_field_name = 'dbnode'

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
    def get_all_values_for_node(cls, dbnode):
        """
        Return a dictionary with all attributes for the given dbnode.

        :return: a dictionary where each key is a level-0 attribute
            stored in the Db table, correctly converted
            to the right type.
        """
        return cls.get_all_values_for_nodepk(dbnode.pk)

    @classmethod
    def get_all_values_for_nodepk(cls, dbnodepk):
        """
        Return a dictionary with all attributes for the dbnode with given PK.

        :return: a dictionary where each key is a level-0 attribute
            stored in the Db table, correctly converted
            to the right type.
        """
        dballsubvalues = cls.objects.filter(dbnode__id=dbnodepk).values_list(
            'key', 'datatype', 'tval', 'fval',
            'ival', 'bval', 'dval')

        data = {_[0]: {
            "datatype": _[1],
            "tval": _[2],
            "fval": _[3],
            "ival": _[4],
            "bval": _[5],
            "dval": _[6],
        } for _ in dballsubvalues
                }
        try:
            return deserialize_attributes(data, sep=cls._sep,
                                          original_class=cls,
                                          original_pk=dbnodepk)
        except DeserializationException as e:
            exc = DbContentError(e.message)
            exc.original_exception = e
            raise exc

    @classmethod
    def reset_values_for_node(cls, dbnode, attributes, with_transaction=True,
                              return_not_store=False):
        from django.db import transaction

        # cls.validate_key(key)

        nodes_to_store = []

        try:
            if with_transaction:
                sid = transaction.savepoint()

            if isinstance(dbnode, (int, long)):
                dbnode_node = DbNode(id=dbnode)
            else:
                dbnode_node = dbnode

            # create_value returns a list of nodes to store
            for k, v in attributes.iteritems():
                nodes_to_store.extend(
                    cls.create_value(k, v,
                                     subspecifier_value=dbnode_node,
                                     ))

            if return_not_store:
                return nodes_to_store
            else:
                # Reset. For set, use also a filter for key__in=attributes.keys()
                cls.objects.filter(dbnode=dbnode_node).delete()

                if nodes_to_store:
                    cls.objects.bulk_create(nodes_to_store)

            if with_transaction:
                transaction.savepoint_commit(sid)
        except:
            if with_transaction:
                transaction.savepoint_rollback(sid)
            raise

    @classmethod
    def set_value_for_node(cls, dbnode, key, value, with_transaction=True,
                           stop_if_existing=False):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from (re)setting a valid key.
        To be used only internally.

        :todo: there may be some error on concurrent write;
           not checked in this unlucky case!

        :param dbnode: the dbnode for which the attribute should be stored;
          in an integer is passed, this is used as the PK of the dbnode,
          without any further check (for speed reasons)
        :param key: the key of the attribute to store; must be a level-zero
          attribute (i.e., no separators in the key)
        :param value: the value of the attribute to store
        :param with_transaction: if True (default), do this within a transaction,
           so that nothing gets stored if a subitem cannot be created.
           Otherwise, if this parameter is False, no transaction management
           is performed.
        :param stop_if_existing: if True, it will stop with an
           UniquenessError exception if the key already exists
           for the given node. Otherwise, it will
           first delete the old value, if existent. The use with True is
           useful if you want to use a given attribute as a "locking" value,
           e.g. to avoid to perform an action twice on the same node.
           Note that, if you are using transactions, you may get the error
           only when the transaction is committed.

        :raise ValueError: if the key contains the separator symbol used
            internally to unpack dictionaries and lists (defined in cls._sep).
        """
        if isinstance(dbnode, (int, long)):
            dbnode_node = DbNode(id=dbnode)
        else:
            dbnode_node = dbnode

        cls.set_value(key, value, with_transaction=with_transaction,
                      subspecifier_value=dbnode_node,
                      stop_if_existing=stop_if_existing)

    @classmethod
    def del_value_for_node(cls, dbnode, key):
        """
        Delete an attribute from the database for the given dbnode.

        :note: no exception is raised if no attribute with the given key is
          found in the DB.

        :param dbnode: the dbnode for which you want to delete the key.
        :param key: the key to delete.
        """
        cls.del_value(key, subspecifier_value=dbnode)

    @classmethod
    def has_key(cls, dbnode, key):
        """
        Return True if the given dbnode has an attribute with the given key,
        False otherwise.
        """
        return bool(cls.objects.filter(dbnode=dbnode, key=key))

    def __str__(self):
        return "[{} ({})].{} ({})".format(
            self.dbnode.get_simple_name(invalid_result="Unknown node"),
            self.dbnode.pk,
            self.key,
            self.datatype, )


@python_2_unicode_compatible
class DbSetting(DbMultipleValueAttributeBaseClass):
    """
    This will store generic settings that should be database-wide.
    """
    # I also add a description field for the variables
    description = m.TextField(blank=True)
    # Modification time of this attribute
    time = m.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "'{}'={}".format(self.key, self.getvalue())


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


class DbCalcState(m.Model):
    """
    Store the state of calculations.

    The advantage of a table (with uniqueness constraints) is that this
    disallows entering twice in the same state (e.g., retrieving twice).
    """
    from aiida.common.datastructures import calc_states
    # Delete states when deleting the calc, does not make sense to keep them
    dbnode = m.ForeignKey(DbNode, on_delete=m.CASCADE,
                          related_name='dbstates')
    state = m.CharField(max_length=25,
                        choices=tuple((_, _) for _ in calc_states),
                        db_index=True)
    time = m.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        unique_together = (("dbnode", "state"))


@python_2_unicode_compatible
class DbGroup(m.Model):
    """
    A group of nodes.

    Any group of nodes can be created, but some groups may have specific meaning
    if they satisfy specific rules (for instance, groups of UpdData objects are
    pseudopotential families - if no two pseudos are included for the same
    atomic element).
    """
    uuid = UUIDField(auto=True, version=AIIDANODES_UUID_VERSION)
    # max_length is required by MySql to have indexes and unique constraints
    name = m.CharField(max_length=255, db_index=True)
    # The type of group: a user group, a pseudopotential group,...
    # User groups have type equal to an empty string
    type = m.CharField(default="", max_length=255, db_index=True)
    dbnodes = m.ManyToManyField('DbNode', related_name='dbgroups')
    # Creation time
    time = m.DateTimeField(default=timezone.now, editable=False)
    description = m.TextField(blank=True)
    # The owner of the group, not of the calculations
    # On user deletion, remove his/her groups too (not the calcuations, only
    # the groups
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.CASCADE,
                        related_name='dbgroups')

    class Meta:
        unique_together = (("name", "type"),)

    def __str__(self):
        if self.type:
            return '<DbGroup [type: {}] "{}">'.format(self.type, self.name)
        else:
            return '<DbGroup [user-defined] "{}">'.format(self.name)


@python_2_unicode_compatible
class DbComputer(m.Model):
    """
    Table of computers or clusters.

    Attributes:
    * name: A name to be used to refer to this computer. Must be unique.
    * hostname: Fully-qualified hostname of the host
    * transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:

        * mpirun command

        * num cores per node

        * max num cores

        * workdir: Full path of the aiida folder on the host. It can contain\
            the string {username} that will be substituted by the username\
            of the user on that machine.\
            The actual workdir is then obtained as\
            workdir.format(username=THE_ACTUAL_USERNAME)\
            Example: \
            workdir = "/scratch/{username}/aiida/"


        * allocate full node = True or False

        * ... (further limits per user etc.)

    """
    # TODO: understand if we want that this becomes simply another type of dbnode.

    uuid = UUIDField(auto=True, version=AIIDANODES_UUID_VERSION)
    name = m.CharField(max_length=255, unique=True, blank=False)
    hostname = m.CharField(max_length=255)
    description = m.TextField(blank=True)
    enabled = m.BooleanField(default=True)
    # TODO: next three fields should not be blank...
    transport_type = m.CharField(max_length=255)
    scheduler_type = m.CharField(max_length=255)
    transport_params = m.TextField(default="{}")  # Will store a json
    metadata = m.TextField(default="{}")  # Will store a json

    @classmethod
    def get_dbcomputer(cls, computer):
        """
        Return a DbComputer from its name (or from another Computer or DbComputer instance)
        """
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
        from aiida.common.exceptions import NotExistent
        from aiida.orm.computer import Computer

        if isinstance(computer, basestring):
            try:
                dbcomputer = DbComputer.objects.get(name=computer)
            except ObjectDoesNotExist:
                raise NotExistent("No computer found in the table of computers with "
                                  "the given name '{}'".format(computer))
            except MultipleObjectsReturned:
                raise DbContentError("There is more than one computer with name '{}', "
                                     "pass a Django Computer instance".format(computer))
        elif isinstance(computer, int):
            try:
                dbcomputer = DbComputer.objects.get(pk=computer)
            except ObjectDoesNotExist:
                raise NotExistent("No computer found in the table of computers with "
                                  "the given pk '{}'".format(computer))
        elif isinstance(computer, DbComputer):
            if computer.pk is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer
        elif isinstance(computer, Computer):
            if computer.dbcomputer.pk is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer.dbcomputer
        else:
            raise TypeError(
                "Pass either a computer name, a DbComputer django instance, a Computer pk or a Computer object")
        return dbcomputer

    def get_aiida_class(self):
        from aiida.orm.computer import Computer
        return Computer(dbcomputer=self)

    def get_workdir(self):
        import json

        try:
            metadata = json.loads(self.metadata)
        except ValueError:
            raise DbContentError(
                "Error while reading metadata for DbComputer {} ({})".format(
                    self.name, self.hostname))

        try:
            return metadata['workdir']
        except KeyError:
            raise ConfigurationError('No workdir found for DbComputer {} '.format(
                self.name))

    def __str__(self):
        if self.enabled:
            return "{} ({})".format(self.name, self.hostname)
        else:
            return "{} ({}) [DISABLED]".format(self.name, self.hostname)


# class RunningJob(m.Model):
#    calc = m.OneToOneField(DbNode,related_name='jobinfo') # OneToOneField implicitly sets unique=True
#    calc_state = m.CharField(max_length=64)
#    job_id = m.TextField(blank=True)
#    scheduler_state = m.CharField(max_length=64,blank=True)
#    # Will store a json of the last JobInfo got from the scheduler
#    last_jobinfo = m.TextField(default='{}')

@python_2_unicode_compatible
class DbAuthInfo(m.Model):
    """
    Table that pairs aiida users and computers, with all required authentication
    information.
    """
    # Delete the DbAuthInfo if either the user or the computer are removed
    aiidauser = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.CASCADE)
    dbcomputer = m.ForeignKey(DbComputer, on_delete=m.CASCADE)
    auth_params = m.TextField(default='{}')  # Will store a json; contains mainly the remoteuser
    # and the private_key

    # The keys defined in the metadata of the DbAuthInfo will override the
    # keys with the same name defined in the DbComputer (using a dict.update()
    # call of python).
    metadata = m.TextField(default="{}")  # Will store a json
    # Whether this computer is enabled (user-level enabling feature)
    enabled = m.BooleanField(default=True)

    class Meta:
        unique_together = (("aiidauser", "dbcomputer"),)

    def get_auth_params(self):
        import json

        try:
            return json.loads(self.auth_params)
        except ValueError:
            raise DbContentError(
                "Error while reading auth_params for authinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.email, self.dbcomputer.hostname))

    def set_auth_params(self, auth_params):
        import json

        # Raises ValueError if data is not JSON-serializable
        self.auth_params = json.dumps(auth_params)

    def get_workdir(self):
        import json

        try:
            metadata = json.loads(self.metadata)
        except ValueError:
            raise DbContentError(
                "Error while reading metadata for authinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.email, self.dbcomputer.hostname))

        try:
            return metadata['workdir']
        except KeyError:
            return self.dbcomputer.get_workdir()

    # a method of DbAuthInfo
    def get_transport(self):
        """
        Given a computer and an aiida user (as entries of the DB) return a configured
        transport to connect to the computer.
        """
        from aiida.transport import TransportFactory
        from aiida.orm.computer import Computer

        try:
            ThisTransport = TransportFactory(self.dbcomputer.transport_type)
        except MissingPluginError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.dbcomputer.hostname, self.dbcomputer.transport_type, e.message))

        params = dict(Computer(dbcomputer=self.dbcomputer).get_transport_params().items() +
                      self.get_auth_params().items())
        return ThisTransport(machine=self.dbcomputer.hostname, **params)

    def __str__(self):
        if self.enabled:
            return "Authorization info for {} on {}".format(self.aiidauser.email, self.dbcomputer.name)
        else:
            return "Authorization info for {} on {} [DISABLED]".format(self.aiidauser.email, self.dbcomputer.name)


@python_2_unicode_compatible
class DbComment(m.Model):
    uuid = UUIDField(auto=True, version=AIIDANODES_UUID_VERSION)
    # Delete comments if the node is removed
    dbnode = m.ForeignKey(DbNode, related_name='dbcomments', on_delete=m.CASCADE)
    ctime = m.DateTimeField(default=timezone.now, editable=False)
    mtime = m.DateTimeField(auto_now=True, editable=False)
    # Delete the comments of a deleted user (TODO: check if this is a good policy)
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.CASCADE)
    content = m.TextField(blank=True)

    def __str__(self):
        return "DbComment for [{} {}] on {}".format(self.dbnode.get_simple_name(),
                                                    self.dbnode.pk, timezone.localtime(self.ctime).strftime("%Y-%m-%d"))


@python_2_unicode_compatible
class DbLog(m.Model):
    # Creation time
    time = m.DateTimeField(default=timezone.now, editable=False)
    loggername = m.CharField(max_length=255, db_index=True)
    levelname = m.CharField(max_length=50, db_index=True)
    # A string to know what is the referred object (e.g. a Calculation,
    # or other)
    objname = m.CharField(max_length=255, blank=True, db_index=True)
    objpk = m.IntegerField(db_index=True, null=True)  # It is not a ForeignKey
    # because it may be in different
    # tables
    message = m.TextField(blank=True)
    metadata = m.TextField(default="{}")  # Will store a json

    def __str__(self):
        return "[Log: {} for {} {}] {}".format(self.levelname,
                                               self.objname, self.objpk, self.message)


class DbLock(m.Model):
    key = m.CharField(max_length=255, primary_key=True)
    creation = m.DateTimeField(default=timezone.now, editable=False)
    timeout = m.IntegerField(editable=False)
    owner = m.CharField(max_length=255, blank=False)


@python_2_unicode_compatible
class DbWorkflow(m.Model):
    from aiida.common.datastructures import wf_states

    uuid = UUIDField(auto=True, version=AIIDANODES_UUID_VERSION)
    ctime = m.DateTimeField(default=timezone.now, editable=False)
    mtime = m.DateTimeField(auto_now=True, editable=False)
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.PROTECT)
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    # still to implement, similarly to the DbNode class
    nodeversion = m.IntegerField(default=1, editable=False)
    # to be implemented similarly to the DbNode class
    lastsyncedversion = m.IntegerField(default=0, editable=False)
    state = m.CharField(max_length=255, choices=zip(list(wf_states), list(wf_states)), default=wf_states.INITIALIZED)
    report = m.TextField(blank=True)
    # File variables, script is the complete dump of the workflow python script
    module = m.TextField(blank=False)
    module_class = m.TextField(blank=False)
    script_path = m.TextField(blank=False)
    script_md5 = m.CharField(max_length=255, blank=False)

    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()

    def get_aiida_class(self):
        """
        Return the corresponding aiida instance of class aiida.worflow
        """
        from aiida.orm.workflow import Workflow

        return Workflow.get_subclass_from_dbnode(self)

    def set_state(self, _state):
        self.state = _state
        self.save()

    def set_script_md5(self, _md5):

        self.script_md5 = _md5
        self.save()

    def add_data(self, dict, d_type):
        try:
            for k in dict.keys():
                p, create = self.data.get_or_create(name=k, data_type=d_type)
                p.set_value(dict[k])
        except Exception as e:
            raise

    def get_data(self, d_type):
        try:
            dict = {}
            for p in self.data.filter(parent=self, data_type=d_type):
                dict[p.name] = p.get_value()
            return dict
        except Exception as e:
            raise

    def add_parameters(self, dict, force=False):
        from aiida.common.datastructures import wf_states, wf_data_types

        if not self.state == wf_states.INITIALIZED and not force:
            raise ValueError("Cannot add initial parameters to an already initialized workflow")

        self.add_data(dict, wf_data_types.PARAMETER)

    def add_parameter(self, name, value):
        self.add_parameters({name: value})

    def get_parameters(self):
        from aiida.common.datastructures import wf_data_types

        return self.get_data(wf_data_types.PARAMETER)

    def get_parameter(self, name):
        res = self.get_parameters()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))

    def add_results(self, dict):
        from aiida.common.datastructures import wf_data_types

        self.add_data(dict, wf_data_types.RESULT)

    def add_result(self, name, value):
        self.add_results({name: value})

    def get_results(self):
        from aiida.common.datastructures import wf_data_types

        return self.get_data(wf_data_types.RESULT)

    def get_result(self, name):
        res = self.get_results()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))

    def add_attributes(self, dict):
        from aiida.common.datastructures import wf_data_types

        self.add_data(dict, wf_data_types.ATTRIBUTE)

    def add_attribute(self, name, value):
        self.add_attributes({name: value})

    def get_attributes(self):
        from aiida.common.datastructures import wf_data_types

        return self.get_data(wf_data_types.ATTRIBUTE)

    def get_attribute(self, name):
        res = self.get_attributes()
        if name in res:
            return res[name]
        else:
            raise ValueError("Error retrieving results: {0}".format(name))

    def clear_report(self):
        self.report = ''
        self.save()

    def append_to_report(self, _text):
        from aiida.utils.timezone import utc
        import datetime

        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.report += str(now) + "] " + _text + "\n"
        self.save()

    def get_calculations(self):
        from aiida.orm import JobCalculation

        return JobCalculation.query(workflow_step=self.steps)

    def get_sub_workflows(self):
        return DbWorkflow.objects.filter(parent_workflow_step=self.steps.all())

    def is_subworkflow(self):
        """
        Return True if this is a subworkflow, False if it is a root workflow,
        launched by the user.
        """
        return len(self.parent_workflow_step.all()) > 0

    def finish(self):
        from aiida.common.datastructures import wf_states

        self.state = wf_states.FINISHED

    def __str__(self):
        simplename = self.module_class
        # node pk + type
        if self.label:
            return "{} workflow [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} workflow [{}]".format(simplename, self.pk)


@python_2_unicode_compatible
class DbWorkflowData(m.Model):
    from aiida.common.datastructures import wf_data_types, wf_data_value_types

    parent = m.ForeignKey(DbWorkflow, related_name='data')
    name = m.CharField(max_length=255, blank=False)
    time = m.DateTimeField(default=timezone.now, editable=False)
    data_type = m.CharField(max_length=255,
                            blank=False, default=wf_data_types.PARAMETER)
    value_type = m.CharField(max_length=255, blank=False,
                             default=wf_data_value_types.NONE)
    json_value = m.TextField(blank=True)
    aiida_obj = m.ForeignKey(DbNode, blank=True, null=True)

    class Meta:
        unique_together = (("parent", "name", "data_type"))

    def set_value(self, arg):
        from aiida.orm.node import Node
        from aiida.common.datastructures import wf_data_value_types
        import json

        try:
            if isinstance(arg, Node) or issubclass(arg.__class__, Node):
                if arg.pk is None:
                    raise ValueError("Cannot add an unstored node as an attribute of a Workflow!")
                self.aiida_obj = arg.dbnode
                self.value_type = wf_data_value_types.AIIDA
                self.save()
            else:
                self.json_value = json.dumps(arg)
                self.value_type = wf_data_value_types.JSON
                self.save()
        except Exception as exc:
            reraise(ValueError, "Cannot set the parameter {}".format(self.name), sys.exc_info()[2])

    def get_value(self):
        import json
        from aiida.common.datastructures import wf_data_value_types

        if self.value_type == wf_data_value_types.JSON:
            return json.loads(self.json_value)
        elif self.value_type == wf_data_value_types.AIIDA:
            return self.aiida_obj.get_aiida_class()
        elif self.value_type == wf_data_value_types.NONE:
            return None
        else:
            raise ValueError("Cannot rebuild the parameter {}".format(self.name))

    def __str__(self):
        return "Data for workflow {} [{}]: {}".format(
            self.parent.module_class, self.parent.pk, self.name)


@python_2_unicode_compatible
class DbWorkflowStep(m.Model):
    from aiida.common.datastructures import wf_states, wf_default_call

    parent = m.ForeignKey(DbWorkflow, related_name='steps')
    name = m.CharField(max_length=255, blank=False)
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.PROTECT)
    time = m.DateTimeField(default=timezone.now, editable=False)
    nextcall = m.CharField(max_length=255, blank=False,
                           default=wf_default_call)
    calculations = m.ManyToManyField(DbNode, symmetrical=False,
                                     related_name="workflow_step")
    sub_workflows = m.ManyToManyField(DbWorkflow, symmetrical=False,
                                      related_name="parent_workflow_step")
    state = m.CharField(max_length=255,
                        choices=zip(list(wf_states), list(wf_states)),
                        default=wf_states.CREATED)

    class Meta:
        unique_together = (("parent", "name"))

    def add_calculation(self, step_calculation):
        from aiida.orm import JobCalculation

        if (not isinstance(step_calculation, JobCalculation)):
            raise ValueError("Cannot add a non-Calculation object to a workflow step")

        try:
            self.calculations.add(step_calculation)
        except:
            raise ValueError("Error adding calculation to step")

    def get_calculations(self, state=None):
        from aiida.orm import JobCalculation

        if (state == None):
            return JobCalculation.query(workflow_step=self)
        else:
            return JobCalculation.query(workflow_step=self).filter(
                dbattributes__key="state", dbattributes__tval=state)

    def remove_calculations(self):
        self.calculations.all().delete()

    def add_sub_workflow(self, sub_wf):
        from aiida.orm.workflow import Workflow

        if (not issubclass(sub_wf.__class__, Workflow) and not isinstance(sub_wf, Workflow)):
            raise ValueError("Cannot add a workflow not of type Workflow")
        try:
            self.sub_workflows.add(sub_wf.dbworkflowinstance)
        except:
            raise ValueError("Error adding calculation to step")

    def get_sub_workflows(self):
        return self.sub_workflows(manager='aiidaobjects').all()

    def remove_sub_workflows(self):
        self.sub_workflows.all().delete()

    def is_finished(self):
        from aiida.common.datastructures import wf_states

        return self.state == wf_states.FINISHED

    def set_nextcall(self, _nextcall):
        self.nextcall = _nextcall
        self.save()

    def set_state(self, _state):
        self.state = _state
        self.save()

    def reinitialize(self):
        from aiida.common.datastructures import wf_states

        self.set_state(wf_states.INITIALIZED)

    def finish(self):
        from aiida.common.datastructures import wf_states

        self.set_state(wf_states.FINISHED)

    def __str__(self):
        return "Step {} for workflow {} [{}]".format(self.name,
                                                     self.parent.module_class, self.parent.pk)
