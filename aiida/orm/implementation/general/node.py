# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import ABCMeta, abstractmethod, abstractproperty
from aiida.common.utils import abstractclassmethod

import collections
import logging
import os
import types

from aiida.common.exceptions import (InternalError, ModificationNotAllowed,
                                     UniquenessError)
from aiida.common.folders import SandboxFolder
from aiida.common.utils import combomethod

from aiida.common.links import LinkType
from aiida.common.lang import override
from aiida.common.old_pluginloader import get_query_type_string
from aiida.backends.utils import validate_attribute_key

_NO_DEFAULT = tuple()


def clean_value(value):
    """
    Get value from input and (recursively) replace, if needed, all occurrences
    of BaseType AiiDA data nodes with their value, and List with a standard list.

    It also makes a deep copy of everything.

    Note however that there is no logic to avoid infinite loops when the
    user passes some perverse recursive dictionary or list.
    In any case, however, this would not be storable by AiiDA...

    :param value: A value to be set as an attribute or an extra
    :return: a "cleaned" value, potentially identical to value, but with
        values replaced where needed.
    """
    # Must be imported in here to avoid recursive imports
    from aiida.orm.data import base as basedatatypes

    if isinstance(value, basedatatypes.BaseType):
        return value.value
    elif isinstance(value, dict):
        # Check dictionary before iterables
        return {k: clean_value(v) for k, v in value.iteritems()}
    elif (isinstance(value, collections.Iterable) and
            not isinstance(value, types.StringTypes)):
        # list, tuple, ... but not a string
        # This should also properly take care of dealing with the
        # basedatatypes.List object
        return [clean_value(v) for v in value]
    else:
        # If I don't know what to do I just return the value
        # itself - it's not super robust, but relies on duck typing
        # (e.g. if there is something that behaves like an integer
        # but is not an integer, I still accept it)
        return value


class AbstractNode(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), in general attributes cannot
    be changed, except for those listed in the self._updatable_attributes
    tuple (empty for this class, can be extended in a subclass).

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
    """

    class __metaclass__(ABCMeta):
        """
        Some python black magic to set correctly the logger also in subclasses.
        """

        def __new__(cls, name, bases, attrs):

            newcls = ABCMeta.__new__(cls, name, bases, attrs)
            newcls._logger = logging.getLogger(
                '{:s}.{:s}'.format(attrs['__module__'], name))

            # Note: the reverse logic (from type_string to name that can
            # be passed to the plugin loader) is implemented in
            # aiida.common.old_pluginloader.
            prefix = "aiida.orm."
            if attrs['__module__'].startswith(prefix):
                # Strip aiida.orm.
                # Append a dot at the end, always
                newcls._plugin_type_string = "{}.{}.".format(
                    attrs['__module__'][len(prefix):], name)

                # Make sure the pugin implementation match the import name.
                # If you have implementation.django.calculation.job, we remove
                # the first part to only get calculation.job.
                if newcls._plugin_type_string.startswith('implementation.'):
                    newcls._plugin_type_string = \
                        '.'.join(newcls._plugin_type_string.split('.')[2:])
                if newcls._plugin_type_string == 'node.Node.':
                    newcls._plugin_type_string = ''
                newcls._query_type_string = get_query_type_string(
                        newcls._plugin_type_string
                    )
            # Experimental: type string for external plugins
            else:
                from aiida.common.pluginloader import entry_point_tpstr_from
                classname = '.'.join([attrs['__module__'], name])
                if entry_point_tpstr_from(classname):
                    newcls._plugin_type_string = entry_point_tpstr_from(classname)
                    newcls._query_type_string = get_query_type_string(
                            newcls._plugin_type_string
                        )
            return newcls

    # This will be set by the metaclass call
    _logger = None

    # Name to be used for the Repository section
    _section_name = 'node'

    # The name of the subfolder in which to put the files/directories
    # added with add_path
    _path_subfolder_name = 'path'

    # A list of tuples, saying which attributes cannot be set at the same time
    # See documentation in the set() method.
    _set_incompatibilities = []

    @staticmethod
    def get_db_columns():
        """
        This method returns a list with the column names and types of the table
        corresponding to this class.
        :return: a list with the names of the columns
        """
        pass

    @property
    def logger(self):
        """
        Get the logger of the Node object.

        :return: Logger object
        """
        return self._logger

    @abstractclassmethod
    def get_subclass_from_uuid(cls, uuid):
        """
        Get a node object from the uuid, with the proper subclass of Node.
        (if Node(uuid=...) is called, only the Node class is loaded).

        :param uuid: a string with the uuid of the object to be loaded.
        :return: the object of the proper subclass.
        :raise: NotExistent: if there is no entry of the desired
                             object kind with the given uuid.
        """
        pass

    @abstractclassmethod
    def get_subclass_from_pk(cls, pk):
        """
        Get a node object from the pk, with the proper subclass of Node.
        (integer primary key used in this database),
        but loading the proper subclass where appropriate.

        :param pk: a string with the pk of the object to be loaded.
        :return: the object of the proper subclass.
        :raise: NotExistent: if there is no entry of the desired
                             object kind with the given pk.
        """
        pass

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        return self.dbnode.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        return self.dbnode.mtime

    def __int__(self):
        if self._to_be_stored:
            return None
        else:
            return self.id

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize the object Node.

        :param uuid: if present, the Node with given uuid is
          loaded from the database.
          (It is not possible to assign a uuid to a new Node.)
        """
        self._to_be_stored = True
        # Empty cache of input links in any case
        self._inputlinks_cache = {}

    @property
    def is_stored(self):
        """
        Return True if the node is stored, False otherwise.
        """
        return not self._to_be_stored

    def __repr__(self):
         return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
         if not self.is_stored:
             return "uuid: {} (unstored)".format(self.uuid)
         else:
             return "uuid: {} (pk: {})".format(self.uuid, self.pk)

    def _init_internal_params(self):
        """
        Set here the default values for this class; this method
        is automatically called by the init.

        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        pass

    @property
    def _set_defaults(self):
        """
        Default values to set in the __init__, if no value is explicitly provided
        for the given key.
        It is a dictionary, with k=v; if the key k is not provided to the __init__,
        and a value is present here, this is set.
        """
        return {}

    @abstractclassmethod
    def query(cls, *args, **kwargs):
        """
        Map to the aiidaobjects manager of the DbNode, that returns
        Node objects (or their subclasses) instead of DbNode entities.

        # TODO: VERY IMPORTANT: the recognition of a subclass from the type
        #       does not work if the modules defining the subclasses are not
        #       put in subfolders.
        #       In the future, fix it either to make a cache and to store the
        #       full dependency tree, or save also the path.
        """
        pass

    def _set_with_defaults(self, **kwargs):
        """
        Calls the set() method, but also adds the class-defined default
        values (defined in the self._set_defaults attribute),
        if they are not provided by the user.

        :note: for the default values, also allow to define 'hidden' methods,
            meaning that if a default value has a key "_state", it will not call
            the function "set__state" but rather "_set_state".
            This is not allowed, instead, for the standard set() method.
        """
        self._set_internal(arguments=self._set_defaults, allow_hidden=True)

        # Pass everything to 'set'
        self.set(**kwargs)

    def set(self, **kwargs):
        """
        For each k=v pair passed as kwargs, call the corresponding
        set_k(v) method (e.g., calling self.set(property=5, mass=2) will
        call self.set_property(5) and self.set_mass(2).
        Useful especially in the __init__.

        :note: it uses the _set_incompatibilities list of the class to check
            that we are not setting methods that cannot be set at the same time.
            _set_incompatibilities must be a list of tuples, and each tuple
            specifies the elements that cannot be set at the same time.
            For instance, if _set_incompatibilities = [('property', 'mass')],
            then the call self.set(property=5, mass=2) will raise a ValueError.
            If a tuple has more than two values, it raises ValueError if *all*
            keys are provided at the same time, but it does not give any error
            if at least one of the keys is not present.

        :note: If one element of _set_incompatibilities is a tuple with only
            one element, this element will not be settable using this function
            (and in particular,

        :raise ValueError: if the corresponding set_k method does not exist
            in self, or if the methods cannot be set at the same time.
        """
        self._set_internal(arguments=kwargs, allow_hidden=False)

    def _set_internal(self, arguments, allow_hidden=False):
        """
        Works as self.set(), but takes a dictionary as the 'arguments' variable,
        instead of reading it from the ``kwargs``; moreover, it allows to specify
        allow_hidden to True. In this case, if a a key starts with and
        underscore, as for instance ``_state``, it will not call
        the function ``set__state`` but rather ``_set_state``.
        """
        for incomp in self._set_incompatibilities:
            if all(k in arguments.keys() for k in incomp):
                if len(incomp) == 1:
                    raise ValueError("Cannot set {} directly when creating "
                                     "the node or using the .set() method; "
                                     "use the specific method instead.".format(
                        incomp[0]))
                else:
                    raise ValueError("Cannot set {} at the same time".format(
                        " and ".join(incomp)))

        for k, v in arguments.iteritems():
            try:
                if allow_hidden and k.startswith("_"):
                    method = getattr(self, '_set_{}'.format(k[1:]))
                else:
                    method = getattr(self, 'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method "
                                 "found".format(k))
            if not isinstance(method, collections.Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not "
                                 "callable!".format(k))
            method(v)

    @property
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """
        return self.dbnode.label

    @label.setter
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """
        self._update_db_label_field(label)

    @abstractmethod
    def _update_db_label_field(self, field_value):
        """
        Update the label field acting directly on the DB
        """
        pass

    @property
    def description(self):
        """
        Get the description of the node.

        :return: a string
        """
        return self.dbnode.description

    @description.setter
    def description(self, desc):
        """
        Set the description of the node

        :param desc: a string
        """
        self._update_db_description_field(desc)

    @abstractmethod
    def _update_db_description_field(self, field_value):
        """
        Update the description of this node, acting directly at the DB level
        """
        pass

    def _validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr
        and similar methods that automatically read either from the DB or
        from the internal attribute cache.

        For the base class, this is always valid. Subclasses will
        reimplement this.
        In the subclass, always call the super()._validate() method first!
        """
        return True

    def get_user(self):
        """
        Get the user.

        :return: a Django DbUser model object
        """
        return self.dbnode.user

    def _has_cached_links(self):
        """
        Return True if there is at least one cached (input) link, that is a
        link that is not stored yet in the database. False otherwise.
        """
        return len(self._inputlinks_cache) != 0

    def add_link_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)
        :note: In subclasses, change only this. Moreover, remember to call
        the super() method in order to properly use the caching logic!

        :param src: the source object
        :param str label: the name of the label to set the link from src.
                          Default = None.
        :param link_type: The type of link, must be one of the enum values
                          from :class:`~aiida.common.links.LinkType`
        """
        assert src is not None, "You must provide a valid Node to link"

        # Check that the label does not already exist

        # This can happen also if both nodes are stored, e.g. if one first
        # stores the output node and then the input node. Therefore I check
        # it here.
        if label in self._inputlinks_cache:
            raise UniquenessError("Input link with name '{}' already present "
                                  "in the internal cache".format(label))

        # See if I am pointing to already saved nodes and I am already
        # linking to a given node
        if src.uuid in [_[0].uuid for _ in self._inputlinks_cache.values()]:
            raise UniquenessError(
                "A link from node with UUID={} and "
                "the current node (UUID={}) already exists!".format(
                    src.uuid, self.uuid))

        # Check if the source allows output links from this node
        # (will raise ValueError if this is not the case)
        src._linking_as_output(self, link_type)

        # If both are stored, write directly on the DB
        if self.is_stored and src.is_stored:
            self._add_dblink_from(src, label, link_type)
        else:  # at least one is not stored: add to the internal cache
            self._add_cachelink_from(src, label, link_type)

    def _add_cachelink_from(self, src, label, link_type):
        """
        Add a link in the cache.
        """
        if label is None:
            raise ModificationNotAllowed(
                "Cannot store a link in the cache if "
                "no explicit label is provided. You can avoid "
                "to provide an input link name only if "
                "both nodes are already stored: in this case, "
                "the link will be directly stored in the DB "
                "and a default name will be provided")

        if label in self._inputlinks_cache:
            raise UniquenessError("Input link with name '{}' already present "
                                  "in the internal cache".format(label))

        self._inputlinks_cache[label] = (src, link_type)

    def _replace_link_from(self, src, label, link_type=LinkType.UNSPECIFIED):
        """
        Replace an input link with the given label, or simply creates it
        if it does not exist.

        :note: In subclasses, change only this. Moreover, remember to call
           the super() method in order to properly use the caching logic!

        :param src: the source object
        :param str label: the name of the label to set the link from src.
        """
        # If both are stored, write directly on the DB
        if self.is_stored and src.is_stored:
            self._replace_dblink_from(src, label, link_type)
            # If the link was in the local cache, remove it
            # (this could happen if I first store the output node, then
            # the input node.
            try:
                del self._inputlinks_cache[label]
            except KeyError:
                pass
        else:  # at least one is not stored: set in the internal cache
            # See if I am pointing to already saved nodes and I am already
            # linking to a given node
            # It is similar to the 'add' method, but if I am replacing the
            # same node, I will not complain (k!=label)
            if src.uuid in [v[0].uuid for k, v in
                            self._inputlinks_cache.iteritems() if k != label]:
                raise UniquenessError(
                    "A link from node with UUID={} and "
                    "the current node (UUID={}) already exists!".format(
                        src.uuid, self.uuid))
            # I insert the link directly in the cache rather than calling
            # _add_cachelink_from because this latter performs an undesired check
            self._inputlinks_cache[label] = (src, link_type)

           # self._add_cachelink_from(src, label, link_type)

    def _remove_link_from(self, label):
        """
        Remove from the DB the input link with the given label.

        :note: In subclasses, change only this. Moreover, remember to call
            the super() method in order to properly use the caching logic!

        :note: No error is raised if the link does not exist.

        :param str label: the name of the label to set the link from src.
        :param link_type: The type of link, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        # Try to remove from the local cache, no problem if none is present
        try:
            del self._inputlinks_cache[label]
        except KeyError:
            pass

        # If both are stored, remove also from the DB
        if self.is_stored:
            self._remove_dblink_from(label)

    @abstractmethod
    def _replace_dblink_from(self, src, label, link_type):
        """
        Replace an input link with the given label and type, or simply creates
        it if it does not exist.

        :note: this function should not be called directly; it acts directly on
            the database.

        :param str src: the source object.
        :param str label: the label of the link from src to the current Node
        :param link_type: The type of link, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        pass

    @abstractmethod
    def _remove_dblink_from(self, label):
        """
        Remove from the DB the input link with the given label.

        :note: this function should not be called directly; it acts directly on
            the database.

        :note: No checks are done to verify that the link actually exists.

        :param str label: the label of the link from src to the current Node
        :param link_type: The type of link, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        pass

    @abstractmethod
    def _add_dblink_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)

        :note: this function should not be called directly; it acts directly on
            the database.

        :param src: the source object
        :param str label: the name of the label to set the link from src.
                    Default = None.
        """
        pass

    def _linking_as_output(self, dest, link_type):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        Implement in subclasses.

        :param dest: the destination output Node
        :return: a boolean (True)
        """
        return True

    def get_inputs_dict(self, only_in_db=False, link_type=None):
        """
        Return a dictionary where the key is the label of the input link, and
        the value is the input node.

        :param only_in_db: If true only get stored links, not cached
        :param link_type: Only get inputs of this link type, if None then
                returns all inputs of all link types.
        :return: a dictionary {label:object}
        """
        return dict(
            self.get_inputs(
                also_labels=True, only_in_db=only_in_db, link_type=link_type))

    def get_outputs_dict(self, link_type=None):
        """
        Return a dictionary where the key is the label of the output link, and
        the value is the input node.
        As some Nodes (Datas in particular) can have more than one output with
        the same label, all keys have the name of the link with appended the pk
        of the node in output.
        The key without pk appended corresponds to the oldest node.

        :return: a dictionary {linkname:object}
        """
        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError("link_type should be a LinkType object")

        all_outputs = self.get_outputs(also_labels=True, link_type=link_type)

        all_linknames = [i[0] for i in all_outputs]
        linknames_set = list(set(all_linknames))

        # prepare a new output list
        new_outputs = {}
        # first add the defaults
        for irreducible_linkname in linknames_set:
            this_elements = [i[1] for i in all_outputs if i[0] == irreducible_linkname]
            # select the oldest element
            last_element = sorted(this_elements, key=lambda x: x.ctime)[0]
            # for this one add the default value
            new_outputs[irreducible_linkname] = last_element

            # now for everyone append the string with the pk
            for i in this_elements:
                new_outputs[irreducible_linkname + "_{}".format(i.pk)] = i

        return new_outputs

    def get_inputs(self, node_type=None, also_labels=False, only_in_db=False,
                   link_type=None):
        """
        Return a list of nodes that enter (directly) in this node

        :param node_type: If specified, should be a class, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param also_labels: If False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the
                following format: ('label', Node), with 'label' the link label,
                and Node a Node instance or subclass
        :param only_in_db: Return only the inputs that are in the database,
                ignoring those that are in the local cache. Otherwise, return
                all links.
        :param link_type: Only get inputs of this link type, if None then
                returns all inputs of all link types.
        """
        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError("link_type should be a LinkType object")

        inputs_list = self._get_db_input_links(link_type=link_type)

        if not only_in_db:
            # Needed for the check
            input_list_keys = [i[0] for i in inputs_list]

            for label, v in self._inputlinks_cache.iteritems():
                src = v[0]
                if label in input_list_keys:
                    raise InternalError("There exist a link with the same name "
                                        "'{}' both in the DB and in the internal "
                                        "cache for node pk= {}!".format(label, self.pk))
                inputs_list.append((label, src))

        if node_type is None:
            filtered_list = inputs_list
        else:
            filtered_list = [i for i in inputs_list if isinstance(i[1], node_type)]

        if also_labels:
            return list(filtered_list)
        else:
            return [i[1] for i in filtered_list]

    @abstractclassmethod
    def _get_db_input_links(self, link_type):
        """
        Return a list of tuples (label, aiida_class) for each input link,
        possibly filtering only by those of a given type.

        :param link_type: if not None, a link type to filter results
        :return:  a list of tuples (label, aiida_class)
        """
        pass

    @override
    def get_outputs(self, type=None, also_labels=False, link_type=None):
        """
        Return a list of nodes that exit (directly) from this node

        :param type: if specified, should be a class, and it filters only
                elements of that specific type (or a subclass of 'type')
        :param also_labels: if False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the
                following format: ('label', Node), with 'label' the link label,
                and Node a Node instance or subclass
        :param link_type: Only return outputs connected by links of this type.
        """
        outputs_list = self._get_db_output_links(link_type=link_type)

        if type is None:
            if also_labels:
                return list(outputs_list)
            else:
                return [i[1] for i in outputs_list]
        else:
            filtered_list = (i for i in outputs_list if isinstance(i[1], type))
            if also_labels:
                return list(filtered_list)
            else:
                return [i[1] for i in filtered_list]

    @abstractmethod
    def _get_db_output_links(self, link_type):
        """
        Return a list of tuples (label, aiida_class) for each output link,
        possibly filtering only by those of a given type.

        :param link_type: if not None, a link type to filter results
        :return:  a list of tuples (label, aiida_class)
        """
        pass

    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """
        from aiida.orm.computer import Computer
        if self.dbnode.dbcomputer is None:
            return None
        else:
            return Computer(dbcomputer=self.dbnode.dbcomputer)

    def set_computer(self, computer):
        """
        Set the computer to be used by the node.

        Note that the computer makes sense only for some nodes: Calculation,
        RemoteData, ...

        :param computer: the computer object
        """
        if self._to_be_stored:
            self._set_db_computer(computer)
        else:
            raise ModificationNotAllowed(
                "Node with uuid={} was already stored".format(self.uuid))

    @abstractmethod
    def _set_db_computer(self, computer):
        """
        Set the computer directly inside the dbnode member, in the DB.

        DO NOT USE DIRECTLY.

        :param computer: the computer object
        """
        pass

    def _set_attr(self, key, value):
        """
        Set a new attribute to the Node (in the DbAttribute table).

        :param str key: key name
        :param value: its value
        :raise ModificationNotAllowed: if such attribute cannot be added (e.g.
            because the node was already stored, and the attribute is not listed
            as updatable).

        :raise ValidationError: if the key is not valid (e.g. it contains the
            separator symbol).
        """
        validate_attribute_key(key)

        if self._to_be_stored:
            import copy
            self._attrs_cache[key] = clean_value(value)
        else:
            self._set_db_attr(key, clean_value(value))

    @abstractmethod
    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        DO NOT USE DIRECTLY.

        :param str key: key name
        :param value: its value
        """
        pass

    def _del_attr(self, key):
        """
        Delete an attribute.

        :param key: attribute to delete.
        :raise AttributeError: if key does not exist.
        :raise ModificationNotAllowed: if the Node was already stored.
        """
        if self._to_be_stored:
            try:
                del self._attrs_cache[key]
            except KeyError:
                raise AttributeError(
                    "DbAttribute {} does not exist".format(key))
        else:
            self._del_db_attr(key)

    @abstractmethod
    def _del_db_attr(self, key):
        """
        Delete an attribute directly from the DB

        DO NOT USE DIRECTLY.

        :param key: The key of the attribute to delete
        """
        pass

    def _del_all_attrs(self):
        """
        Delete all attributes associated to this node.

        :raise ModificationNotAllowed: if the Node was already stored.
        """
        # I have to convert the attrs in a list, because the list will change
        # while deleting elements
        for attr_name in list(self.attrs()):
            self._del_attr(attr_name)

    def get_attr(self, key, default=_NO_DEFAULT):
        """
        Get the attribute.

        :param key: name of the attribute
        :param default: if no attribute key is found, returns default

        :return: attribute value

        :raise AttributeError: If no attribute is found and there is no default
        """
        try:
            if self._to_be_stored:
                try:
                    return self._attrs_cache[key]
                except KeyError:
                    raise AttributeError(
                        "DbAttribute '{}' does not exist".format(key))
            else:
                return self._get_db_attr(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            return default

    @abstractmethod
    def _get_db_attr(self, key):
        """
        Return the attribute value, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: the attribute key
        :return: the attribute value
        :raise AttributeError: if the attribute does not exist.
        """
        pass

    def set_extra(self, key, value, exclusive=False):
        """
        Sets an extra of a calculation.
        No .store() to be called. Can be used *only* after saving.

        :param key: key name
        :param value: key value
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).

        :raise UniquenessError: if extra already exists and exclusive is True.
        """
        validate_attribute_key(key)

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set only after "
                "storing the node")
        self._set_db_extra(key, clean_value(value), exclusive)


    def set_extra_exclusive(self, key, value):
        """
        Set an extra in exclusive mode (stops if the attribute
        is already there).
        Deprecated, use set_extra() with exclusive=False

        :param key: key name
        :param value: key value
        """
        self.set_extra(key, value, exclusive=True)


    @abstractmethod
    def _set_db_extra(self, key, value, exclusive):
        """
        Store extra directly in the DB, without checks.

        DO NOT USE DIRECTLY.

        :param key: key name
        :param value: key value
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).
        """
        pass

    def set_extras(self, the_dict):
        """
        Immediately sets several extras of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.

        :param the_dict: a dictionary of key:value to be set as extras
        """

        try:
            for key, value in the_dict.iteritems():
                self.set_extra(key, value)
        except AttributeError:
            raise AttributeError("set_extras takes a dictionary as argument")


    def reset_extras(self, new_extras):
        """
        Deletes existing extras and creates new ones.
        :param new_extras: dictionary with new extras
        :return: nothing, an exceptions is raised in several circumnstances
        """
        if not isinstance(new_extras, dict):
            raise TypeError("The new extras have to be a dictionary")

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set only after "
                "storing the node")

        self._reset_db_extras(clean_value(new_extras))

    @abstractmethod
    def _reset_db_extras(self, new_extras):
        """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        pass

    def get_extra(self, key, *args):
        """
        Get the value of a extras, reading directly from the DB!
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        :param key: key name
        :param value: if no attribute key is found, returns value

        :return: the key value

        :raise ValueError: If more than two arguments are passed to get_extra
        """
        if len(args) > 1:
            raise ValueError("After the key name you can pass at most one"
                             "value, that is the default value to be used "
                             "if no extra is found.")

        try:
            if self._to_be_stored:
                raise AttributeError("DbExtra '{}' does not exist yet, the "
                                     "node is not stored".format(key))
            else:
                return self._get_db_extra(key)
        except AttributeError as e:
            try:
                return args[0]
            except IndexError:
                raise e

    @abstractmethod
    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param str key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """
        pass

    def get_extras(self):
        """
        Get the value of extras, reading directly from the DB!
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        :return: the dictionary of extras ({} if no extras)
        """
        return dict(self.iterextras())


    def del_extra(self, key):
        """
        Delete a extra, acting directly on the DB!
        The action is immediately performed on the DB.
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        :param str key: key name
        :raise: AttributeError: if key starts with underscore
        :raise: ModificationNotAllowed: if the node is not stored yet
        """
        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set and deleted "
                "only after storing the node")
        self._del_db_extra(key)

    @abstractmethod
    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param str key: key name
        """
        pass

    def extras(self):
        """
        Get the keys of the extras.

        :return: a list of strings
        """
        for k, v in self.iterextras():
            yield k

    def iterextras(self):
        """
        Iterator over the extras, returning tuples (key, value)

        :todo: verify that I am not creating a list internally
        """
        if self._to_be_stored:
            # If it is not stored yet, there are no extras that can be
            # added (in particular, we do not even have an ID to use!)
            # Return without value, meaning that this is an empty generator
            return
            yield # Needed after return to convert it to a generator
        for _ in self._db_iterextras():
            yield _


    def iterattrs(self):
        """
        Iterator over the attributes, returning tuples (key, value)
        """
        # TODO: check what happens if someone stores the object while
        #        the iterator is being used!
        if self._to_be_stored:
            for k, v in self._attrs_cache.iteritems():
                yield (k, v)
        else:
            for k, v in self._db_iterattrs():
                yield k, v

    def attrs(self):
        """
        Returns the keys of the attributes as a generator.

        :return: a generator of a strings
        """
        # Note: this calls a different function _db_attrs
        # because often it's faster not to retrieve the values from the DB
        if self._to_be_stored:
            for k in self._attrs_cache.iterkeys():
                yield k
        else:
            for k in self._db_attrs():
                yield k

    @abstractmethod
    def _db_attrs(self):
        """
        Returns the keys of the attributes as a generator,
        directly from the DB.

        DO NOT USE DIRECTLY.
        """
        pass

    @abstractmethod
    def _db_iterattrs(self):
        """
        Iterator over the attributes (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        pass

    def get_attrs(self):
        """
        Return a dictionary with all attributes of this node.
        """
        return dict(self.iterattrs())

    @abstractmethod
    def add_comment(self, content, user=None):
        """
        Add a new comment.

        :param content: string with comment
        """
        pass

    @abstractmethod
    def get_comments(self, pk=None):
        """
        Return a sorted list of comment values, one for each comment associated
        to the node.

        :param pk: integer or list of integers. If it is specified, returns the
            comment values with desired pks. (pk refers to DbComment.pk)
        :return: the list of comments, sorted by pk; each element of the
            list is a dictionary, containing (pk, email, ctime, mtime, content)
        """
        pass

    @abstractmethod
    def _get_dbcomments(self, pk=None):
        """
        Return a sorted list of DbComment associated with the Node.

        :param pk: integer or list of integers. If it is specified, returns the
            comment values with desired pks. (pk refers to DbComment.pk)
        :return: the list of DbComment, sorted by pk.
        """
        pass

    @abstractmethod
    def _update_comment(self, new_field, comment_pk, user):
        """
        Function called by verdi comment update
        """
        pass

    @abstractmethod
    def _remove_comment(self, comment_pk, user):
        """
        Function called by verdi comment remove
        """
        pass

    @abstractmethod
    def _increment_version_number_db(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version
        (e.g. on adding a extra or attribute).

        :note: Do not manually increment the version number, because if
            two different threads are adding/changing an attribute concurrently,
            the version number would be incremented only once.
        """
        pass

    @abstractmethod
    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.

        This is a completely new entry in the DB, with its own UUID.
        Works both on stored instances and with not-stored ones.

        Copies files and attributes, but not the extras.
        Does not store the Node to allow modification of attributes.

        :return: an object copy
        """
        pass

    @property
    @abstractmethod
    def uuid(self):
        """
        :return: a string with the uuid
        """
        pass

    @property
    def pk(self):
        """
        :return: the principal key (the ID) as an integer, or None if the
           node was not stored yet
        """
        return self.id

    @property
    @abstractmethod
    def id(self):
        """
        :return: the principal key (the ID) as an integer, or None if the
           node was not stored yet
        """
        pass

    @property
    @abstractmethod
    def dbnode(self):
        """
        :return: the corresponding DbNode object.
        """
        # I also update the internal _dbnode variable, if it was saved
        # from aiida.backends.djsite.db.models import DbNode
        #        if not self._to_be_stored:
        #            self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)
        pass

    @property
    def _repository_folder(self):
        """
        Get the permanent repository folder.
        Use preferentially the folder property.

        :return: the permanent RepositoryFolder object
        """
        return self._repo_folder

    @property
    def folder(self):
        """
        Get the folder associated with the node,
        whether it is in the temporary or the permanent repository.

        :return: the RepositoryFolder object.
        """
        if not self.is_stored:
            return self._get_temp_folder()
        else:
            return self._repository_folder

    @property
    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.

        :return: a Folder object.
        """
        return self.folder.get_subfolder(
            self._path_subfolder_name, reset_limit=True)

    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.

        :param subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self._get_folder_pathsubfolder.get_subfolder(subfolder).get_content_list()

    def _get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.

        :return: a SandboxFolder object mapping the node in the repository.
        """
        # I create the temp folder only at is first usage
        if self._temp_folder is None:
            self._temp_folder = SandboxFolder()  # This is also created
            # Create the 'path' subfolder in the Sandbox
            self._get_folder_pathsubfolder.create()
        return self._temp_folder

    def remove_path(self, path):
        """
        Remove a file or directory from the repository directory.
        Can be called only before storing.

        :param str path: relative path to file/directory.
        """
        if self.is_stored:
            raise ModificationNotAllowed(
                "Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path "
                             "must be a relative path")
        self._get_folder_pathsubfolder.remove_path(path)

    def add_path(self, src_abs, dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.

        :param str src_abs: the absolute path of the file to copy.
        :param str dst_filename: the (relative) path on which to copy.

        :todo: in the future, add an add_attachment() that has the same
            meaning of a extras file. Decide also how to store. If in two
            separate subfolders, remember to reset the limit.
        """
        if self.is_stored:
            raise ModificationNotAllowed(
                "Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a"
                             "filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs, dst_path)

    def get_abs_path(self, path=None, section=None):
        """
        Get the absolute path to the folder associated with the
        Node in the AiiDA repository.

        :param str path: the name of the subfolder inside the section. If None
                         returns the abspath of the folder. Default = None.
        :param section: the name of the subfolder ('path' by default).
        :return: a string with the absolute path

        For the moment works only for one kind of files, 'path' (internal files)
        """
        if path is None:
            return self.folder.abspath
        if section is None:
            section = self._path_subfolder_name
        # TODO: For the moment works only for one kind of files,
        #      'path' (internal files)
        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.folder.get_subfolder(section,
                                         reset_limit=True).get_abs_path(path, check_existence=True)

    @abstractmethod
    def store_all(self, with_transaction=True):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        pass


    def _store_input_nodes(self):
        """
        Find all input nodes, and store them, checking that they do not
        have unstored inputs in turn.

        :note: this function stores all nodes without transactions; always
          call it from within a transaction!
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "_store_input_nodes can be called only if the node is "
                "unstored (node {} is stored, instead)".format(self.pk))

        for label in self._inputlinks_cache:
            parent = self._inputlinks_cache[label][0]
            if not parent.is_stored:
                parent.store(with_transaction=False)

    def _check_are_parents_stored(self):
        """
        Check if all parents are already stored, otherwise raise.

        :raise ModificationNotAllowed: if one of the input nodes in not already
          stored.
        """
        # Preliminary check to verify that inputs are stored already
        for label in self._inputlinks_cache:
            if not self._inputlinks_cache[label][0].is_stored:
                raise ModificationNotAllowed(
                    "Cannot store the input link '{}' because the "
                    "source node is not stored. Either store it first, "
                    "or call _store_input_links with the store_parents "
                    "parameter set to True".format(label))

    @abstractmethod
    def _store_cached_input_links(self, with_transaction=True):
        """
        Store all input links that are in the local cache, transferring them
        to the DB.

        :note: This can be called only if all parents are already stored.

        :note: Links are stored only after the input nodes are stored. Moreover,
            link storage is done in a transaction, and if one of the links
            cannot be stored, an exception is raised and *all* links will remain
            in the cache.

        :note: This function can be called only after the node is stored.
           After that, it can be called multiple times, and nothing will be
           executed if no links are still in the cache.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        pass

    @abstractmethod
    def store(self, with_transaction=True):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        # TODO: This needs to be generalized, allowing for flexible methods
        # for storing data and its attributes.
        pass

    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust
        too much this function!
        """
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    @property
    def out(self):
        """
        Traverse the graph of the database.
        Returns a databaseobject, linked to the current node, by means of the linkname.
        Example:
        B = A.out.results: Returns the object B, with link from A to B, with linkname parameters
        """
        return NodeOutputManager(self)

    @property
    def inp(self):
        """
        Traverse the graph of the database.
        Returns a databaseobject, linked to the current node, by means of the linkname.
        Example:
        B = A.inp.parameters: returns the object (B), with link from B to A, with linkname parameters
        C= A.inp: returns an InputManager, an object that is meant to be accessed as the previous example
        """
        return NodeInputManager(self)

    @abstractproperty
    def has_children(self):
        """
        Property to understand if children are attached to the node
        :return: a boolean
        """
        # use the transitive closure
        pass

    @abstractproperty
    def has_parents(self):
        """
        Property to understand if parents are attached to the node
        :return: a boolean
        """
        # use the transitive closure
        pass

    @combomethod
    def querybuild(self_or_cls, **kwargs):
        """
        Instantiates and
        :returns: a QueryBuilder instance.

        The QueryBuilder's path has one vertice so far, namely this class.
        Additional parameters (e.g. filters or a label),
        can be passes as keyword arguments.

        :param label: Label to give
        :param filters: filters to apply
        :param project: projections

        This class is a comboclass (see :func:`~aiida.common.utils.combomethod`)
        therefore the method can be called as class or instance method.
        If called as an instance method, adds a filter on the id.
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node as AiidaNode
        isclass = kwargs.pop('isclass')
        qb = QueryBuilder()
        if isclass:
            qb.append(self_or_cls, **kwargs)
        else:
            filters = kwargs.pop('filters', {})
            filters.update({'id': self_or_cls.pk})
            qb.append(self_or_cls.__class__, filters=filters, **kwargs)
        return qb


class NodeOutputManager(object):
    """
    To document
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list all valid output links
        """
        node_attributes = self._node.get_outputs_dict().keys()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._node.get_outputs_dict().keys()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_outputs_dict()[name]
        except KeyError:
            raise AttributeError("Node {} does not have an output with link {}"
                                 .format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_outputs_dict()[name]
        except KeyError:
            raise KeyError("Node {} does not have an output with link {}"
                           .format(self._node.pk, name))


class NodeInputManager(object):
    """
    To document
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list all valid input links
        """
        node_attributes = self._node.get_inputs_dict().keys()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._node.get_inputs_dict().keys()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_inputs_dict()[name]
        except KeyError:
            raise AttributeError(
                "Node '{}' does not have an input with link '{}'"
                .format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_inputs_dict()[name]
        except KeyError:
            raise KeyError("Node '{}' does not have an input with link '{}'"
                           .format(self._node.pk, name))


class AttributeManager(object):
    """
    An object used internally to return the attributes as a dictionary.

    :note: Important! It cannot be used to change variables, just to read
      them. To change values (of unstored nodes), use the proper Node methods.
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list the keys of the dictionary
        """
        return sorted(self._node.attrs())

    def __iter__(self):
        """
        Return the keys as an iterator
        """
        for k in self._node.attrs():
            yield k

    def _get_dict(self):
        """
        Return the internal dictionary
        """
        return dict(self._node.iterattrs())

    def __getattr__(self, name):
        """
        Interface to get to dictionary values, using the key as an attribute.

        :note: it works only for attributes that only contain letters, numbers
          and underscores, and do not start with a number.

        :param name: name of the key whose value is required.
        """
        return self._node.get_attr(name)

    def __getitem__(self, name):
        """
        Interface to get to dictionary values as a dictionary.

        :param name: name of the key whose value is required.
        """
        try:
            return self._node.get_attr(name)
        except AttributeError as e:
            raise KeyError(e.message)
