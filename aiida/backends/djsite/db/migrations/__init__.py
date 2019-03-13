# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from django.core.exceptions import ObjectDoesNotExist
from aiida.common.exceptions import AiidaException, DbContentError
from six.moves import range


class DeserializationException(AiidaException):
    pass


LATEST_MIGRATION = '0030_dbnode_type_to_dbnode_node_type'


def _update_schema_version(version, apps, schema_editor):
    from aiida.backends.djsite.utils import set_db_schema_version
    set_db_schema_version(version)


def upgrade_schema_version(up_revision, down_revision):
    from functools import partial
    from django.db import migrations

    return migrations.RunPython(
        partial(_update_schema_version, up_revision),
        reverse_code=partial(_update_schema_version, down_revision))


def current_schema_version():
    # Have to use this ugly way of importing because the django migration
    # files start with numbers which are not a valid package name
    latest_migration = __import__(
        'aiida.backends.djsite.db.migrations.{}'.format(LATEST_MIGRATION),
        fromlist=['REVISION']
    )
    return latest_migration.REVISION


# Here I copied the class method definitions from aiida.backends.djsite.db.models
# used to set and delete values for nodes.
# This was done because:
# 1) The DbAttribute object loaded with apps.get_model() does not provide the class methods
# 2) When the django model changes the migration will continue to work
# 3) If we defined in the migration a new class with these methodds as an extension of the DbAttribute class,
# django detects a change in the model and creates a new migration


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
    :raise aiida.backends.djsite.db.models.DeserializationException: if an error occurs
    """
    from aiida.common import json
    from aiida.common.timezone import (
        is_naive, make_aware, get_current_timezone)

    from aiida.common import AIIDA_LOGGER

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
        firstlevelsubdict = {k: v for k, v in subitems.items()
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
                AIIDA_LOGGER.error(msg)
            else:
                raise DeserializationException(msg)

        # I get the values in memory as a dictionary
        tempdict = {}
        for firstsubk, firstsubv in firstlevelsubdict.items():
            # I call recursively the same function to get subitems
            newsubitems = {k[len(firstsubk) + len(sep):]: v
                           for k, v in subitems.items()
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
        firstlevelsubdict = {k: v for k, v in subitems.items()
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
                AIIDA_LOGGER.error(msg)
            else:
                raise DeserializationException(msg)

        # I get the values in memory as a dictionary
        tempdict = {}
        for firstsubk, firstsubv in firstlevelsubdict.items():
            # I call recursively the same function to get subitems
            newsubitems = {k[len(firstsubk) + len(sep):]: v
                           for k, v in subitems.items()
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
    for mainkey, descriptiondict in data.items():
        prefix, thissep, postfix = mainkey.partition(sep)
        if thissep:
            found_subitems[prefix][postfix] = {k: v for k, v
                                               in descriptiondict.items() if k != "key"}
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
    for k, v in found_mainitems.items():
        # Note: found_subitems[k] will return an empty dictionary it the
        # key does not exist, as it is a defaultdict
        retval[k] = _deserialize_attribute(mainitem=v,
                                           subitems=found_subitems[k], sep=sep, original_class=original_class,
                                           original_pk=original_pk)

    return retval


class ModelModifierV0025(object):

    from aiida.backends.utils import AIIDA_ATTRIBUTE_SEP

    _subspecifier_field_name = 'dbnode'
    _sep = AIIDA_ATTRIBUTE_SEP

    def __init__(self, apps, model_class):
        self._apps = apps
        self._model_class = model_class

    @property
    def apps(self):
        return self._apps

    def subspecifiers_dict(self, attr):
        """
        Return a dict to narrow down the query to only those matching also the
        subspecifier.
        """
        if self._subspecifier_field_name is None:
            return {}
        else:
            return {self._subspecifier_field_name: getattr(attr, self._subspecifier_field_name)}

    def subspecifier_pk(self, attr):
        """
        Return the subspecifier PK in the database (or None, if no
        subspecifier should be used)
        """
        if self._subspecifier_field_name is None:
            return None
        else:
            return getattr(attr, self._subspecifier_field_name).pk

    def validate_key(self, key):
        """
        Validate the key string to check if it is valid (e.g., if it does not
        contain the separator symbol.).

        :return: None if the key is valid
        :raise aiida.common.ValidationError: if the key is not valid
        """
        from aiida.backends.utils import validate_attribute_key
        return validate_attribute_key(key)

    def get_value_for_node(self, dbnode, key):
        """
        Get an attribute from the database for the given dbnode.

        :return: the value stored in the Db table, correctly converted
            to the right type.
        :raise AttributeError: if no key is found for the given dbnode
        """
        cls = self._model_class
        DbNode = self.apps.get_model('db', 'DbNode')

        if isinstance(dbnode, six.integer_types):
            dbnode_node = DbNode(id=dbnode)
        else:
            dbnode_node = dbnode

        try:
            attr = cls.objects.get(dbnode=dbnode_node, key=key)
        except ObjectDoesNotExist:
            raise AttributeError("{} with key {} for node {} not found in db".format(cls.__name__, key, dbnode.pk))

        return self.getvalue(attr)

    def getvalue(self, attr):
        """This can be called on a given row and will get the corresponding value, casting it correctly. """
        try:
            if attr.datatype == 'list' or attr.datatype == 'dict':
                prefix = "{}{}".format(attr.key, self._sep)
                prefix_len = len(prefix)
                dballsubvalues = self._model_class.objects.filter(
                    key__startswith=prefix,
                    **self.subspecifiers_dict(attr)).values_list('key',
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
                    "datatype": attr.datatype,
                    "tval": attr.tval,
                    "fval": attr.fval,
                    "ival": attr.ival,
                    "bval": attr.bval,
                    "dval": attr.dval}
                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self._model_class,
                                              original_pk=self.subspecifier_pk(attr))['attr']
            else:
                data = {"attr": {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": attr.datatype,
                    "tval": attr.tval,
                    "fval": attr.fval,
                    "ival": attr.ival,
                    "bval": attr.bval,
                    "dval": attr.dval}}

                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self._model_class,
                                              original_pk=self.subspecifier_pk(attr))['attr']
        except DeserializationException as exc:
            exc = DbContentError(exc)
            exc.original_exception = exc
            raise exc

    def set_value_for_node(self, dbnode, key, value, with_transaction=False,
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
        cls = self._model_class
        DbNode = self.apps.get_model('db', 'DbNode')

        if isinstance(dbnode, six.integer_types):
            dbnode_node = DbNode(id=dbnode)
        else:
            dbnode_node = dbnode

        self.set_value(key, value, with_transaction=with_transaction,
                      subspecifier_value=dbnode_node,
                      stop_if_existing=stop_if_existing)

    def del_value_for_node(self, dbnode, key):
        """
        Delete an attribute from the database for the given dbnode.

        :note: no exception is raised if no attribute with the given key is
          found in the DB.

        :param dbnode: the dbnode for which you want to delete the key.
        :param key: the key to delete.
        """
        self.del_value(key, subspecifier_value=dbnode)

    def del_value(self, key, only_children=False, subspecifier_value=None):
        """
        Delete a value associated with the given key (if existing).

        :note: No exceptions are raised if no entry is found.

        :param key: the key to delete. Can contain the separator self._sep if
          you want to delete a subkey.
        :param only_children: if True, delete only children and not the
          entry itself.
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        """
        cls = self._model_class
        from django.db.models import Q

        if self._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            subspecifiers_dict = {}
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(self.__name__,
                                                                self._subspecifier_field_name))
            subspecifiers_dict = {self._subspecifier_field_name:
                                      subspecifier_value}

        query = Q(key__startswith="{parentkey}{sep}".format(
            parentkey=key, sep=self._sep),
            **subspecifiers_dict)

        if not only_children:
            query.add(Q(key=key, **subspecifiers_dict), Q.OR)

        cls.objects.filter(query).delete()

    def set_value(self, key, value, with_transaction=False,
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
        cls = self._model_class
        from django.db import transaction

        self.validate_key(key)

        try:
            if with_transaction:
                sid = transaction.savepoint()

            # create_value returns a list of nodes to store
            to_store = self.create_value(key, value,
                                        subspecifier_value=subspecifier_value,
                                        other_attribs=other_attribs)

            if to_store:
                if not stop_if_existing:
                    # Delete the old values if stop_if_existing is False,
                    # otherwise don't delete them and hope they don't
                    # exist. If they exist, I'll get an UniquenessError

                    # NOTE! Be careful in case the extra/attribute to
                    # store is not a simple attribute but a list or dict:
                    # like this, it should be ok because if we are
                    # overwriting an entry it will stop anyway to avoid
                    # to overwrite the main entry, but otherwise
                    # there is the risk that trailing pieces remain
                    # so in general it is good to recursively clean
                    # all sub-items.
                    self.del_value(key,
                                  subspecifier_value=subspecifier_value)
                cls.objects.bulk_create(to_store)

            if with_transaction:
                transaction.savepoint_commit(sid)
        except BaseException as exc:  # All exceptions including CTRL+C, ...
            from django.db.utils import IntegrityError
            from aiida.common.exceptions import UniquenessError

            if with_transaction:
                transaction.savepoint_rollback(sid)
            if isinstance(exc, IntegrityError) and stop_if_existing:
                raise UniquenessError("Impossible to create the required "
                                      "entry "
                                      "in table '{}', "
                                      "another entry already exists and the creation would "
                                      "violate an uniqueness constraint.\nFurther details: "
                                      "{}".format(cls.__name__, exc))
            raise

    def create_value(self, key, value, subspecifier_value=None,
                     other_attribs={}):
        """
        Create a new list of attributes, without storing them, associated
        with the current key/value pair (and to the given subspecifier,
        e.g. the DbNode for DbAttributes and DbExtras).

        :note: No hits are done on the DB, in particular no check is done
          on the existence of the given nodes.

        :param key: a string with the key to create (can contain the
          separator self._sep if this is a sub-attribute: indeed, this
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
        cls = self._model_class
        import datetime

        from aiida.common import json
        from aiida.common.timezone import is_naive, make_aware, get_current_timezone

        if self._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            new_entry = cls(key=key, **other_attribs)
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                self._subspecifier_field_name))
            further_params = other_attribs.copy()
            further_params.update({self._subspecifier_field_name:
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

        elif isinstance(value, six.integer_types):
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

        elif isinstance(value, six.string_types):
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
                list_to_return.extend(self.create_value(
                    key=("{}{}{:d}".format(key, self._sep, i)),
                    value=subv,
                    subspecifier_value=subspecifier_value))

        elif isinstance(value, dict):

            new_entry.datatype = 'dict'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for subk, subv in value.items():
                self.validate_key(subk)

                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(self.create_value(
                    key="{}{}{}".format(key, self._sep, subk),
                    value=subv,
                    subspecifier_value=subspecifier_value))
        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError(
                    "Unable to store the value: it must be either a basic datatype, or json-serializable: {}".format(
                        value))

            new_entry.datatype = 'json'
            new_entry.tval = jsondata
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        return list_to_return
