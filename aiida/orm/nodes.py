# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for Computer entities"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import importlib
import os
import typing
import warnings

import six

from aiida.orm.utils import links
from aiida.backends.utils import validate_attribute_key
from aiida.common.caching import get_use_cache
from aiida.common.links import LinkType
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
from aiida.common import exceptions
from aiida.common.utils import combomethod, classproperty, type_check, sql_string_match
from aiida.manage import get_manager
from aiida.orm.implementation.general.node import _AbstractNodeMeta, clean_value, _NO_DEFAULT, NodeOutputManager, \
    NodeInputManager, _HASH_EXTRA_KEY
from . import comments
from . import convert
from . import entities
from . import groups
from . import computers
from . import querybuilder
from . import users

__all__ = ('Node',)

# pylint: disable=too-many-lines


@six.add_metaclass(_AbstractNodeMeta)
class Node(entities.Entity):
    """
    Base class for all nodes in AiiDA.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
    """

    # pylint: disable=too-many-public-methods

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

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes = tuple()

    # Flag that determines whether the class can be cached.
    _cacheable = True

    # Flag that says if the node is storable or not.
    # By default, bare nodes (and also ProcessNodes) are not storable,
    # all subclasses (WorkflowNode, CalculationNode, Data and their subclasses)
    # are storable. This flag is checked in store()
    _storable = False

    @classmethod
    def from_backend_entity(cls, backend_entity):
        entity = super(Node, cls).from_backend_entity(backend_entity)
        entity._repo_folder = RepositoryFolder(section=entity._section_name, uuid=entity.uuid)
        # Set the internal parameters
        # Can be redefined in the subclasses
        entity._init_internal_params()

    @classproperty
    def plugin_type_string(cls):
        """Returns the plugin type string of the node class."""
        return cls._plugin_type_string

    def __init__(self, backend=None, **kwargs):
        """
        Initialize the object Node.

        :param uuid: if present, the Node with given uuid is
          loaded from the database.
          (It is not possible to assign a uuid to a new Node.)
        """
        backend = backend or get_manager().get_backend()
        model = backend.nodes.create()
        super(Node, self).__init__(model)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        self._attrs_cache = {}

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = list()

        self._temp_folder = None
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust
        too much this function!
        """
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if not self.is_stored:
            return "uuid: {} (unstored)".format(self.uuid)

        return "uuid: {} (pk: {})".format(self.uuid, self.pk)

    def __copy__(self):
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo):
        """Deep copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('deep copying a base Node is not supported')

    @property
    def logger(self):
        """
        Get the logger of the Node object.

        :return: Logger object
        """
        return self._logger

    def get_desc(self):
        """
        Returns a string with infos retrieved from a node's properties.
        This method is actually overwritten by the inheriting classes

        :return: a description string
        :rtype: str
        """
        return ''

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        return self._backend_entity.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        return self._backend_entity.mtime

    def has_cached_links(self):
        """
        Return whether there are unstored incoming links in the cache.

        :return: boolean, True when there are links in the incoming cache, False otherwise
        """
        return bool(self._incoming_cache)

    def _init_internal_params(self):
        """
        Set the default values for this class; this method is automatically called by the init.

        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        pass

    @property
    def _set_defaults(self):
        """
        Default values to set in the __init__, if no value is explicitly provided for the given key.
        It is a dictionary, with k=v; if the key k is not provided to the __init__, and a value is present here,
        this is set.
        """
        return {}

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
                                     "use the specific method instead.".format(incomp[0]))
                else:
                    raise ValueError("Cannot set {} at the same time".format(" and ".join(incomp)))

        for key, value in arguments.items():
            try:
                if allow_hidden and key.startswith("_"):
                    method = getattr(self, '_set_{}'.format(key[1:]))
                else:
                    method = getattr(self, 'set_{}'.format(key))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method " "found".format(key))
            if not isinstance(method, typing.Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not " "callable!".format(key))
            method(value)

    @property
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        return self._backend_entity.type

    @property
    def nodeversion(self):
        """
        Return the version of the node

        :return: A version integer
        :rtype: int
        """
        return self._backend_entity.nodeversion

    @property
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """
        return self._get_db_label_field()

    @label.setter
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """
        self._update_db_label_field(label)

    def _get_db_label_field(self):
        """
        Get the label field acting directly on the DB

        :return: a string.
        """
        return self._backend_entity.get_db_label_field()

    def _update_db_label_field(self, field_value):
        """
        Set the label field acting directly on the DB
        """
        self._backend_entity.set_db_label_field(field_value)

    @property
    def description(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """
        return self._get_db_description_field()

    @description.setter
    def description(self, desc):
        """
        Set the description of the node

        :param desc: a string
        """
        self._update_db_description_field(desc)

    def _get_db_description_field(self):
        """
        Get the description of this node, acting directly at the DB level
        """
        return self._backend_entity.get_db_description_field()

    def _update_db_description_field(self, field_value):
        """
        Update the description of this node, acting directly at the DB level
        """
        self._backend_entity.update_db_description_field(field_value)

    def _validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr
        and similar methods that automatically read either from the DB or
        from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super()._validate() method first!
        """
        return True

    def get_user(self):
        """
        Get the user.

        :return: a User model object
        :rtype: :class:`aiida.orm.User`
        """
        return users.User.from_backend_entity(self.backend_entity.get_user())

    def set_user(self, user):
        """
        Set the user

        :param user: The new user
        """
        type_check(user, user.User)
        self.backend_entity.set_user(user.backend_entity)

    def validate_incoming(self, source, link_type, link_label):
        """
        Validate adding a link of the given type from a given node to ourself.

        This function will first validate the types of the inputs, followed by the node and link types and validate
        whether in principle a link of that type between the nodes of these types is allowed.the

        Subsequently, the validity of the "degree" of the proposed link is validated, which means validating the
        number of links of the given type from the given node type is allowed.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        type_check(link_type, LinkType)
        type_check(source, Node)

        from aiida.orm.utils.links import validate_link
        validate_link(source, self, link_type, link_label)

    def validate_outgoing(self, target, link_type, link_label):  # pylint: disable=unsed-argument
        """
        Validate adding a link of the given type from ourself to a given node.

        The validity of the triple (source, link, target) should be validated in the `validate_incoming` call.
        This method will be called afterwards and can be overriden by subclasses to add additional checks that are
        specific to that subclass.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        type_check(link_type, LinkType)
        type_check(target, Node)

    def add_incoming(self, source, link_type, link_label):
        """
        Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :return: True if the proposed link is allowed, False otherwise
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        self.validate_incoming(source, link_type, link_label)
        source.validate_outgoing(self, link_type, link_label)

        if self.is_stored and source.is_stored:
            self.backend_entity.add_link_from(source, link_type, link_label)
        else:
            self._add_cachelink_from(source, link_type, link_label)

    def _add_cachelink_from(self, source, link_type, link_label):
        """Add an incoming link to the cache.

        .. note: the proposed link is not validated in this function, so this should not be called directly
            but it should only be called by `Node.add_incoming`.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        """
        link_triple = links.LinkTriple(source, link_type, link_label)

        if link_triple in self._incoming_cache:
            raise exceptions.UniquenessError('the link triple {} is already present in the cache'.format(link_triple))

        self._incoming_cache.append(link_triple)

    def get_incoming(self, node_class=None, link_type=(), link_label_filter=None):
        """
        Return a list of link triples that are (directly) incoming into this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        """
        if not isinstance(link_type, tuple):
            link_type = (link_type,)

        if self.is_stored:
            link_triples = self.get_stored_link_triples(node_class, link_type, link_label_filter, 'incoming')
        else:
            link_triples = []

        # Get all cached link triples
        for link_triple in self._incoming_cache:

            if link_triple in link_triples:
                raise exceptions.InternalError('Node<{}> has both a stored and cached link triple {}'.format(
                    self.pk, link_triple))

            if not link_type or link_triple.link_type in link_type:
                if link_label_filter is not None:
                    if sql_string_match(string=link_triple.link_label, pattern=link_label_filter):
                        link_triples.append(link_triple)
                else:
                    link_triples.append(link_triple)

        return links.LinkManager(link_triples)

    def get_outgoing(self, node_class=None, link_type=(), link_label_filter=None):
        """
        Return a list of link triples that are (directly) outgoing of this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all outputs of all link types.
        :param link_label_filter: filters the outgoing nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        """
        link_triples = self.get_stored_link_triples(node_class, link_type, link_label_filter, 'outgoing')
        return links.LinkManager(link_triples)

    def get_stored_link_triples(self, node_class=None, link_type=(), link_label_filter=None, link_direction='incoming'):
        """
        Return the list of stored link triples directly incoming to or outgoing of this node.

        Note this will only return link triples that are stored in the database. Anything in the cache is ignored.

        :param node_class: If specified, should be a class, and it filters only elements of that (subclass of) type
        :param link_type: Only get inputs of this link type, if empty tuple then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label. This should be a regex statement as
            one would pass directly to a QuerBuilder filter statement with the 'like' operation.
        :param link_direction: `incoming` or `outgoing` to get the incoming or outgoing links, respectively.
        """
        if not isinstance(link_type, tuple):
            link_type = (link_type,)

        if link_type and not all([isinstance(t, LinkType) for t in link_type]):
            raise TypeError('link_type should be a LinkType or tuple of LinkType: got {}'.format(link_type))

        node_class = node_class or Node
        node_filters = {'id': {'==': self.id}}
        edge_filters = {}

        if link_type:
            edge_filters['type'] = {'in': [t.value for t in link_type]}

        if link_label_filter:
            edge_filters['label'] = {'like': link_label_filter}

        builder = querybuilder.QueryBuilder()
        builder.append(Node, filters=node_filters, tag='main')

        if link_direction == 'outgoing':
            builder.append(
                node_class,
                with_incoming='main',
                project=['*'],
                edge_project=['type', 'label'],
                edge_filters=edge_filters)
        else:
            builder.append(
                node_class,
                with_outgoing='main',
                project=['*'],
                edge_project=['type', 'label'],
                edge_filters=edge_filters)

        return [links.LinkTriple(entry[0], LinkType(entry[1]), entry[2]) for entry in builder.all()]

    def _replace_link_from(self, source, link_type, link_label):
        """
        Replace an incoming link with the given type andlabel, or create it if it does not exist.

        :note: In subclasses, change only this. Moreover, remember to call
           the super() method in order to properly use the caching logic!

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        """
        self.validate_incoming(source, link_type, link_label)
        source.validate_outgoing(self, link_type, link_label)

        link_triple = links.LinkTriple(source, link_type, link_label)

        # If both are stored, write directly on the DB
        if self.is_stored and source.is_stored:
            self._replace_dblink_from(source, link_type, link_label)

            # If the link triple was in the local cache, remove it, which can happen if one first stores the target
            # node, followed by the source node.
            try:
                self._incoming_cache.remove(link_triple)
            except ValueError:
                pass
        else:
            # At least one node is not stored yet so add it to the internal cache
            # I insert the link directly in the cache rather than calling _add_cachelink_from
            # because this latter performs an undesired check
            self._incoming_cache.append(link_triple)

    def _remove_link_from(self, label):
        """
        Remove from the DB the input link with the given label.

        :note: In subclasses, change only this. Moreover, remember to call
            the super() method in order to properly use the caching logic!

        :note: No error is raised if the link does not exist.

        :param str label: the name of the label to set the link from src.
        :param link_type: the link type, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        if self.is_stored:
            self.backend_entity.remove_link_from(label)
        else:
            try:
                del self._incoming_cache[label]
            except KeyError:
                pass

    def _replace_dblink_from(self, src, link_type, label):
        """
        Replace an input link with the given label and type, or simply creates
        it if it does not exist.

        :note: this function should not be called directly; it acts directly on
            the database.

        :param str src: the source object.
        :param str label: the label of the link from src to the current Node
        :param link_type: the link type, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        self.backend_entity.replace_dblink_from(src, link_type, label)

    def _remove_dblink_from(self, label):
        """
        Remove from the DB the input link with the given label.

        :note: this function should not be called directly; it acts directly on
            the database.

        :note: No checks are done to verify that the link actually exists.

        :param str label: the label of the link from src to the current Node
        :param link_type: the link type, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        self.backend_entity.remove_dblink_from(label)

    def _add_dblink_from(self, src, link_type, label):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)

        :note: this function should not be called directly; it acts directly on
            the database.

        :param src: the source object
        :param str label: the name of the label to set the link from src.
        """
        self.backend_entity.add_dblink_from(src, link_type, label)

    def get_inputs_dict(self, only_in_db=False, link_type=None):
        """
        Return a dictionary where the key is the label of the input link, and
        the value is the input node.

        :param only_in_db: If true only get stored links, not cached
        :param link_type: Only get inputs of this link type, if None then
                returns all inputs of all link types.
        :return: a dictionary {label:object}
        """
        warnings.warn('get_inputs_dict method is deprecated, use get_incoming instead', DeprecationWarning)

        return dict(self.get_inputs(also_labels=True, only_in_db=only_in_db, link_type=link_type))

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
        warnings.warn('get_outputs_dict method is deprecated, use get_outgoing instead', DeprecationWarning)

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

    def get_inputs(self, node_type=None, also_labels=False, only_in_db=False, link_type=None):
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
        warnings.warn('get_inputs method is deprecated, use get_incoming instead', DeprecationWarning)

        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError('link_type should be a LinkType object')

        inputs_list = self._get_db_input_links(link_type=link_type)

        if not only_in_db:
            # Needed for the check
            input_list_keys = [i[0] for i in inputs_list]

            for link_triple in self._incoming_cache:
                if link_triple.link_label in input_list_keys:
                    raise exceptions.InternalError(
                        "There exist a link with the same name '{}' both in the DB and in the internal "
                        "cache for node pk= {}!".format(link_triple.link_label, self.pk))

                if link_type is None or link_triple.link_type is link_type:
                    inputs_list.append((link_triple.link_label, link_triple.node))

        if node_type is None:
            filtered_list = inputs_list
        else:
            filtered_list = [i for i in inputs_list if isinstance(i[1], node_type)]

        if also_labels:
            return list(filtered_list)

        return [i[1] for i in filtered_list]

    def _get_db_input_links(self, link_type):
        """
        Return a list of tuples (label, aiida_class) for each input link,
        possibly filtering only by those of a given type.

        :param link_type: if not None, a link type to filter results
        :return:  a list of tuples (label, aiida_class)
        """
        return self.backend_entity.get_db_input_links(link_type)

    def get_outputs(self, node_type=None, also_labels=False, link_type=None):
        """
        Return a list of nodes that exit (directly) from this node

        :param node_type: if specified, should be a class, and it filters only
            elements of that specific node_type (or a subclass of 'node_type')
        :param also_labels: if False (default) only return a list of input nodes.
            If True, return a list of tuples, where each tuple has the
            following format: ('label', Node), with 'label' the link label,
            and Node a Node instance or subclass
        :param link_type: Only return outputs connected by links of this type.
        """
        warnings.warn('get_outputs method is deprecated, use get_outgoing instead', DeprecationWarning)

        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError('link_type should be a LinkType object')

        outputs_list = [
            convert.get_orm_entity(entity) for entity in self.backend_entity.get_output_links(link_type=link_type)
        ]

        if node_type is None:
            filtered_list = outputs_list
        else:
            filtered_list = (i for i in outputs_list if isinstance(i[1], node_type))

        if also_labels:
            return list(filtered_list)

        return [i[1] for i in filtered_list]

    def get_computer(self):
        """
        Get the computer associated to the node.

        TODO: Move this to calculation

        :return: the Computer object or None.
        """
        backend_computer = self.backend_entity.get_computer()
        if backend_computer is None:
            return None

        return computers.Computer.from_backend_entity(self.backend_entity.computer)

    def set_computer(self, computer):
        """
        Set the computer to be used by the node.

        Note that the computer makes sense only for some nodes: Calculation, RemoteData, ...

        TODO: Move this to Calculation

        :param computer: the computer object
        :type computer: :class:`aiida.orm.Computer`
        """
        type_check(computer, computers.Computer)

        if not self.is_stored:
            if not computer.is_stored:
                raise ValueError("The computer instance has not yet been stored")
            self.backend_entity.set_db_computer(computer.backend_entity)
        else:
            raise exceptions.ModificationNotAllowed("Node with uuid={} was already stored".format(self.uuid))

    # region Attributes

    def iterattrs(self):
        """
        Iterator over the attributes, returning tuples (key, value)
        """
        if not self.is_stored:
            for key, value in self._attrs_cache.items():
                yield (key, value)
        else:
            for key, value in self.backend_entity.iterattrs():
                yield key, value

    def attrs(self):
        """
        Returns the keys of the attributes as a generator.

        :return: a generator of a strings
        """
        # Note: this calls a different function _db_attrs
        # because often it's faster not to retrieve the values from the DB
        if not self.is_stored:
            for key in self._attrs_cache:
                yield key
        else:
            for key in self.backend_entity.attrs():
                yield key

    def get_attrs(self):
        """
        Return a dictionary with all attributes of this node.
        """
        return dict(self.iterattrs())

    def _set_attr(self, key, value, clean=True, stored_check=True):
        """
        Set a node attribute

        :param key: key name
        :param value: its value
        :param clean: whether to clean values.
            WARNING: when set to False, storing will throw errors
            for any data types not recognized by the db backend
        :param stored_check: when set to False will disable the mutability check
        :raise ModificationNotAllowed: if node is already stored
        :raise ValidationError: if the key is not valid, e.g. it contains the separator symbol
        """
        if stored_check and self.is_stored:
            raise exceptions.ModificationNotAllowed('Cannot change the attributes of a stored node')

        validate_attribute_key(key)

        if not self.is_stored:
            if clean:
                value = clean_value(value)
            self._attrs_cache[key] = value
        else:
            self.backend_entity.set_attr(key, clean_value(value))

    def _append_to_attr(self, key, value, clean=True):
        """
        Append value to an attribute of the Node (in the DbAttribute table).

        :param key: key name of "list-type" attribute If attribute doesn't exist, it is created.
        :param value: the value to append to the list
        :param clean: whether to clean the value
            WARNING: when set to False, storing will throw errors
            for any data types not recognized by the db backend
        :raise ValidationError: if the key is not valid, e.g. it contains the separator symbol
        """
        validate_attribute_key(key)

        try:
            values = self.get_attr(key)
        except AttributeError:
            values = []

        try:
            if clean:
                values.append(clean_value(value))
            else:
                values.append(value)
        except AttributeError:
            raise AttributeError("Use _set_attr only on attributes containing lists")

        self._set_attr(key, values, clean=False)

    def _del_attr(self, key, stored_check=True):
        """
        Delete an attribute.

        :param key: attribute to delete.
        :param stored_check: when set to False will disable the mutability check
        :raise AttributeError: if key does not exist.
        :raise ModificationNotAllowed: if node is already stored
        """
        if stored_check and self.is_stored:
            raise exceptions.ModificationNotAllowed('Cannot change the attributes of a stored node')

        if not self.is_stored:
            try:
                del self._attrs_cache[key]
            except KeyError:
                raise AttributeError("DbAttribute {} does not exist".format(key))
        else:
            self.backend_entity.del_attr(key)

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
            if not self.is_stored:
                try:
                    return self._attrs_cache[key]
                except KeyError:
                    raise AttributeError("DbAttribute '{}' does not exist".format(key))
            else:
                return self.backend_entity.get_attr(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            return default

    # endregion

    # region Extras

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

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed("The extras of a node can be set only after " "storing the node")
        self.backend_entity.set_extra(key, clean_value(value), exclusive)

    def set_extra_exclusive(self, key, value):
        """
        Set an extra in exclusive mode (stops if the attribute is already there).
        Deprecated, use set_extra() with exclusive=False

        :param key: key name
        :param value: key value
        """
        self.set_extra(key, value, exclusive=True)

    def set_extras(self, the_dict):
        """
        Immediately sets several extras of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.

        :param the_dict: a dictionary of key:value to be set as extras
        """

        try:
            for key, value in the_dict.items():
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

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed("The extras of a node can be set only after " "storing the node")

        self.backend_entity.reset_extras(clean_value(new_extras))

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
            if not self.is_stored:
                raise AttributeError("DbExtra '{}' does not exist yet, the " "node is not stored".format(key))
            else:
                return self.backend_entity.get_extra(key)
        except AttributeError:
            try:
                return args[0]
            except IndexError:
                raise

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

        :param key: key name
        :raise: AttributeError: if key starts with underscore
        :raise: ModificationNotAllowed: if the node is not stored yet
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed("The extras of a node can be set and deleted "
                                                    "only after storing the node")
        self.backend_entity.del_extra(key)

    def extras(self):
        """
        Get the keys of the extras.

        :return: a list of strings
        """
        for key, value in self.iterextras():
            yield key

    def iterextras(self):
        """
        Iterator over the extras, returning tuples (key, value)

        :todo: verify that I am not creating a list internally
        """
        if not self.is_stored:
            # If it is not stored yet, there are no extras that can be
            # added (in particular, we do not even have an ID to use!)
            # Return without value, meaning that this is an empty generator
            return
            yield  # Needed after return to convert it to a generator
        for extra in self.backend_entity.iterextras():
            yield extra

    # endregion

    def add_comment(self, content, user=None):
        """
        Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """
        user = user or users.User.objects.get_default()
        return comments.Comment(node=self, user=user, content=content, backend=self._backend).store()

    def get_comment(self, identifier):
        """
        Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """
        return comments.Comment.objects(self._backend).get(comment=identifier)

    def get_comments(self):
        """
        Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """
        return comments.Comment.objects(self._backend).find(filters={'dbnode_id': self.pk}, order_by=[{'id': 'asc'}])

    def update_comment(self, identifier, content):
        """
        Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """
        comments.Comment.objects(self._backend).get(comment=identifier).set_content(content)

    def remove_comment(self, identifier):
        """
        Delete an existing comment.

        :param identifier: the comment pk
        """
        comments.Comment.objects(self._backend).delete(comment=identifier)

    @property
    def uuid(self):
        """
        :return: a string with the uuid
        """
        return self.backend_entity.uuid

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

        return self._repository_folder

    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.

        :return: a Folder object.
        """
        return self.folder.get_subfolder(self._path_subfolder_name, reset_limit=True)

    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.

        :param subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self._get_folder_pathsubfolder().get_subfolder(subfolder).get_content_list()

    def _get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.

        :return: a SandboxFolder object mapping the node in the repository.
        """
        # I create the temp folder only at is first usage
        if self._temp_folder is None:
            self._temp_folder = SandboxFolder()  # This is also created
            # Create the 'path' subfolder in the Sandbox
            self._get_folder_pathsubfolder().create()
        return self._temp_folder

    def remove_path(self, path):
        """
        Remove a file or directory from the repository directory.
        Can be called only before storing.

        :param str path: relative path to file/directory.
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed("Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path must be a relative path")
        self._get_folder_pathsubfolder().remove_path(path)

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
            raise exceptions.ModificationNotAllowed("Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a" "filename without any subfolder")
        self._get_folder_pathsubfolder().insert_path(src_abs, dst_path)

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
        return self.folder.get_subfolder(section, reset_limit=True).get_abs_path(path, check_existence=True)

    def store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, no transaction is used. This is meant to be used ONLY if the outer
            calling function has already a transaction open!
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('Node<{}> is already stored'.format(self.id))

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self._incoming_cache:
            try:
                link_triple.node._check_are_parents_stored()
            except exceptions.ModificationNotAllowed:
                raise exceptions.ModificationNotAllowed(
                    'source Node<{}> has unstored parents, cannot proceed (only direct parents can be unstored and '
                    'will be stored by store_all, not grandparents or other ancestors'.format(link_triple.node.pk))

        return self._db_store_all(with_transaction, use_cache=use_cache)

    def _db_store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!

        :param use_cache: Determines whether caching is used to find an equivalent node.
        :type use_cache: bool
        """
        with self.backend.transaction():
            self._store_input_nodes()
            self.store()

    def _store_input_nodes(self):
        """
        Find all input nodes, and store them, checking that they do not
        have unstored inputs in turn.

        :note: this function stores all nodes without transactions; always
          call it from within a transaction!
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed(
                'Node<{}> is already stored, but this method can only be called for unstored nodes'.format(self.pk))

        for link_triple in self._incoming_cache:
            if not link_triple.node.is_stored:
                link_triple.node.store(with_transaction=False)

    def _check_are_parents_stored(self):
        """
        Check if all parents are already stored, otherwise raise.

        :raise ModificationNotAllowed: if one of the input nodes is not already stored.
        """
        for link_triple in self._incoming_cache:
            if not link_triple.node.is_stored:
                raise exceptions.ModificationNotAllowed(
                    "Cannot store the incoming link triple {} because the source node is not stored. Either store it "
                    "first, or call _store_input_links with `store_parents` set to True".format(link_triple.link_label))

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
        self._check_are_parents_stored()

        # I have to store only those links where the source is already stored
        for link_triple in self._incoming_cache:
            self.backend_entity.add_link_from(*link_triple)

        # If everything went smoothly, clear the entries from the cache.
        # I do it here because I delete them all at once if no error
        # occurred; otherwise, links will not be stored and I
        # should not delete them from the cache (but then an exception
        # would have been raised, and the following lines are not executed)
        self._incoming_cache = list()

    def store(self, with_transaction=True, use_cache=None):
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

        # As a first thing, I check if the data is storable
        if not self._storable:
            raise exceptions.StoringNotAllowed("You are not allowed to store a base Node or ProcessNode, you can "
                                               "only store Data, WorkflowNode, CalculationNode or their subclasses")
        # Second thing: check if it's valid
        self._validate()

        if not self.is_stored:

            # Verify that parents are already stored. Raises if this is not the case.
            self._check_are_parents_stored()

            # Get default for use_cache if it's not set explicitly.
            if use_cache is None:
                use_cache = get_use_cache(type(self))
            # Retrieve the cached node.
            same_node = self._get_same_node() if use_cache else None
            if same_node is not None:
                self._store_from_cache(same_node, with_transaction=with_transaction)
                self._add_outputs_from_cache(same_node)
            else:
                # call implementation-dependent store method
                self._db_store(with_transaction)

            # Set up autogrouping used by verdi run
            from aiida.orm.autogroup import current_autogroup, Autogroup, VERDIAUTOGROUP_TYPE

            if current_autogroup is not None:
                if not isinstance(current_autogroup, Autogroup):
                    raise exceptions.ValidationError("current_autogroup is not an AiiDA Autogroup")

                if current_autogroup.is_to_be_grouped(self):
                    group_name = current_autogroup.get_group_name()
                    if group_name is not None:
                        group = groups.Group.objects(self._backend).get_or_create(
                            name=group_name, type_string=VERDIAUTOGROUP_TYPE)[0]
                        group.add_nodes(self)

        return super(Node, self).store()

    def _store_from_cache(self, cache_node, with_transaction):
        from aiida.orm.mixins import Sealable
        assert self.type == cache_node.type

        self.label = cache_node.label
        self.description = cache_node.description

        for key, value in cache_node.iterattrs():
            if key != Sealable.SEALED_KEY:
                self._set_attr(key, value)

        self.folder.replace_with_folder(cache_node.folder.abspath, move=False, overwrite=True)

        # Make sure the node doesn't have any RETURN links
        if cache_node.get_outgoing(link_type=LinkType.RETURN).all():
            raise ValueError('Cannot use cache from nodes with RETURN links.')

        self.store(with_transaction=with_transaction, use_cache=False)
        self.set_extra('_aiida_cached_from', cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node):
        # Add CREATE links
        for entry in cache_node.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    @abstractmethod
    def _db_store(self, with_transaction=True):
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
        pass

    def get_hash(self, ignore_errors=True, **kwargs):
        """
        Making a hash based on my attributes
        """
        from aiida.common.hashing import make_hash
        try:
            return make_hash(self._get_objects_to_hash(), **kwargs)
        except Exception:  # pylint: disable=broad-except
            if ignore_errors:
                return None
            else:
                raise

    def _get_objects_to_hash(self):
        """
        Return a list of objects which should be included in the hash.
        """
        computer = self.get_computer()
        return [
            importlib.import_module(self.__module__.split('.', 1)[0]).__version__, {
                key: val
                for key, val in self.get_attrs().items()
                if (key not in self._hash_ignored_attributes and
                    key not in getattr(self, '_updatable_attributes', tuple()))
            }, self.folder, computer.uuid if computer is not None else None
        ]

    def rehash(self):
        """
        Re-generates the stored hash of the Node.
        """
        self.set_extra(_HASH_EXTRA_KEY, self.get_hash())

    def clear_hash(self):
        """
        Sets the stored hash of the Node to None.
        """
        self.set_extra(_HASH_EXTRA_KEY, None)

    def get_cache_source(self):
        """
        Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached

        :return: the UUID of the node from which this node was cached, or None if it was not created through the cache
        """
        return self.get_extra('_aiida_cached_from', None)

    @property
    def is_created_from_cache(self):
        """
        Return whether this node was created from a cached node.cached

        :return: boolean, True if the node was created by cloning a cached node, False otherwise
        """
        return self.get_cache_source() is not None

    def _get_same_node(self):
        """
        Returns a stored node from which the current Node can be cached, meaning that the returned Node is a valid
        cache, and its ``_aiida_hash`` attribute matches ``self.get_hash()``.

        If there are multiple valid matches, the first one is returned. If no matches are found, ``None`` is returned.

        Note that after ``self`` is stored, this function can return ``self``.
        """
        try:
            return next(self._iter_all_same_nodes())
        except StopIteration:
            return None

    def get_all_same_nodes(self):
        """
        Return a list of stored nodes which match the type and hash of the current node. For the stored nodes, the
        ``_aiida_hash`` extra is checked to determine the hash, while ``self.get_hash()`` is executed on the current
        node.

        Only nodes which are a valid cache are returned. If the current node is already stored, it can be included in
        the returned list if ``self.get_hash()`` matches its ``_aiida_hash``.
        """
        return list(self._iter_all_same_nodes())

    def _iter_all_same_nodes(self):
        """
        Returns an iterator of all same nodes.
        """
        if not self._cacheable:
            return iter(())

        hash_ = self.get_hash()
        if not hash_:
            return iter(())

        builder = querybuilder.QueryBuilder()
        builder.append(self.__class__, filters={'extras._aiida_hash': hash_}, project='*', subclassing=False)
        same_nodes = (n[0] for n in builder.iterall())
        return (n for n in same_nodes if n._is_valid_cache())  # pylint: disable=protected-access

    def _is_valid_cache(self):  # pylint: disable=no-self-use
        """
        Subclass hook to exclude certain Nodes (e.g. failed calculations) from being considered in the caching process.
        """
        return True

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

    @property
    def has_children(self):
        """
        Property to understand if children are attached to the node
        :return: a boolean
        """
        first_desc = querybuilder.QueryBuilder().append(
            Node, filters={
                'id': self.pk
            }, tag='self').append(
                Node, with_ancestors='self', project='id').first()
        return bool(first_desc)

    @property
    def has_parents(self):
        """
        Property to understand if parents are attached to the node
        :return: a boolean
        """
        first_ancestor = querybuilder.QueryBuilder().append(
            Node, filters={
                'id': self.pk
            }, tag='self').append(
                Node, with_descendants='self', project='id').first()
        return bool(first_ancestor)

    def load_process_class(self):
        """
        For nodes that were ran by a Process, the process_type will be set. This can either be an entry point
        string or a module path, which is the identifier for that Process. This method will attempt to load
        the Process class and return
        """
        from aiida.plugins.entry_point import load_entry_point_from_string, is_valid_entry_point_string

        if self.process_type is None:
            return None

        if is_valid_entry_point_string(self.process_type):
            process_class = load_entry_point_from_string(self.process_type)
        else:
            class_module, class_name = self.process_type.rsplit('.', 1)
            module = importlib.import_module(class_module)
            process_class = getattr(module, class_name)

        return process_class

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: get schema of the node
        """
        return {
            "attributes": {
                "display_name": "Attributes",
                "help_text": "Attributes of the node",
                "is_foreign_key": False,
                "type": "dict"
            },
            "attributes.state": {
                "display_name": "State",
                "help_text": "AiiDA state of the calculation",
                "is_foreign_key": False,
                "type": ""
            },
            "ctime": {
                "display_name": "Creation time",
                "help_text": "Creation time of the node",
                "is_foreign_key": False,
                "type": "datetime.datetime"
            },
            "extras": {
                "display_name": "Extras",
                "help_text": "Extras of the node",
                "is_foreign_key": False,
                "type": "dict"
            },
            "id": {
                "display_name": "Id",
                "help_text": "Id of the object",
                "is_foreign_key": False,
                "type": "int"
            },
            "label": {
                "display_name": "Label",
                "help_text": "User-assigned label",
                "is_foreign_key": False,
                "type": "str"
            },
            "mtime": {
                "display_name": "Last Modification time",
                "help_text": "Last modification time",
                "is_foreign_key": False,
                "type": "datetime.datetime"
            },
            "type": {
                "display_name": "Type",
                "help_text": "Code type",
                "is_foreign_key": False,
                "type": "str"
            },
            "user_id": {
                "display_name": "Id of creator",
                "help_text": "Id of the user that created the node",
                "is_foreign_key": True,
                "related_column": "id",
                "related_resource": "_dbusers",
                "type": "int"
            },
            "uuid": {
                "display_name": "Unique ID",
                "help_text": "Universally Unique Identifier",
                "is_foreign_key": False,
                "type": "unicode"
            },
            "nodeversion": {
                "display_name": "Node version",
                "help_text": "Version of the node",
                "is_foreign_key": False,
                "type": "int"
            },
            "process_type": {
                "display_name": "Process type",
                "help_text": "Process type",
                "is_foreign_key": False,
                "type": "str"
            }
        }

    # region Deprecated

    @classmethod
    def get_subclass_from_uuid(cls, uuid):
        """
        Get a node object from the uuid, with the proper subclass of Node.
        (if Node(uuid=...) is called, only the Node class is loaded).

        :param uuid: a string with the uuid of the object to be loaded.
        :return: the object of the proper subclass.
        :raise: NotExistent: if there is no entry of the desired
                             object kind with the given uuid.

        .. deprecated:: 1.0.0b1
            Use :meth:`aiida.orm.Node.objects.get` instead.
        """
        warnings.warn("use aidia.orm.Node.objects.get instead", DeprecationWarning)
        return cls.objects.get(uuid=uuid)

    @classmethod
    def get_subclass_from_pk(cls, pk):
        """
        Get a node object from the pk, with the proper subclass of Node.
        (integer primary key used in this database),
        but loading the proper subclass where appropriate.

        :param pk: a string with the pk of the object to be loaded.
        :return: the object of the proper subclass.
        :raise: NotExistent: if there is no entry of the desired
                             object kind with the given pk.

        .. deprecated:: 1.0.0b1
            Use :meth:`aiida.orm.Node.objects.get` instead.
        """
        warnings.warn("use aidia.orm.Node.objects.get instead", DeprecationWarning)
        return cls.objects.get(id=pk)

    def __int__(self):
        """
        .. deprecated:: 1.0.0b1
            It will no longer be possible to get the ID this way, it's a dangerous method to have that
            was only there for legacy query reasons
        """
        if not self.is_stored:
            return None

        return self.id

    @classmethod
    def query(cls, *_args, **_kwargs):
        """
        Query for nodes of this type

        .. deprecated:: 1.0.0b1
            Use :meth:`aiida.orm.Node.objects.query` instead.
        """
        warnings.warn("use aidia.orm.Node.objects.query instead", DeprecationWarning)
        raise NotImplementedError("This method is no longer available, use Node.objects.query()")

    @combomethod
    def querybuild(self_or_cls, **kwargs):  # pylint: disable=no-self-argument
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

        .. deprecated:: 1.0.0b1
            Use :meth:`aiida.orm.Node.objects.query` instead.
        """
        warnings.warn("use aidia.orm.Node.objects.query instead", DeprecationWarning)

        isclass = kwargs.pop('isclass')
        query = querybuilder.QueryBuilder()
        if isclass:
            query.append(self_or_cls, **kwargs)
        else:
            filters = kwargs.pop('filters', {})
            filters.update({'id': self_or_cls.pk})
            query.append(self_or_cls.__class__, filters=filters, **kwargs)
        return query

    # endregion
