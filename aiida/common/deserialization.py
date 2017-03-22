# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.common.exceptions import AiidaException
from aiida.utils.timezone import is_naive, make_aware, get_current_timezone
import json


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


#    from aiida.common import aiidalogger

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
            if (original_class is not None
                and original_class._subspecifier_field_name is not None):
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
                print msg
                #~ aiidalogger.error(msg)
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
                print msg
                #~ aiidalogger.error(msg)
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
