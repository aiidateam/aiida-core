# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend specific computer objects and methods"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import abc
import six

from aiida.backends.utils import validate_attribute_key
from aiida.common import exceptions
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.lang import type_check
from aiida.orm.utils.node import clean_value
from . import backends

__all__ = ('BackendNode', 'BackendNodeCollection', '_NO_DEFAULT')

_NO_DEFAULT = tuple()


class RepositoryMixin(object):
    """
    A mixin class that knows about file repositories, to mix in
    with the BackendNode class
    """

    # Name to be used for the Repository section
    _section_name = 'node'

    # The name of the subfolder in which to put the files/directories
    # added with add_path
    _path_subfolder_name = 'path'

    # Flag that says if the node is storable or not.
    # By default, bare nodes (and also ProcessNodes) are not storable,
    # all subclasses (WorkflowNode, CalculationNode, Data and their subclasses)
    # are storable. This flag is checked in store()
    _storable = False
    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    def _init_repository(self):
        """
        Initializes the repository variables and classes.
        Should ALWAYS be called in the init (it is typically
        called directly inside ``_init_backend_node`` of the
        BackendNode class, that in tun should be called by the __init__
        of each implementation)
        """
        self._temp_folder = None
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

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
        return self.folder.get_subfolder(self._path_subfolder_name, reset_limit=True)

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
            raise ModificationNotAllowed("Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path " "must be a relative path")
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
            raise ModificationNotAllowed("Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a" "filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs, dst_path)

    ## TODO: for now this is left here for reference, but this
    ## functionality should not be exposed, since in the future
    ## the concept of an 'abs_path' might not exist anymore
    ## (files inside a zip, in a object store, ...)
    ## We should make sure instead that we expose e.g. a
    ## file_open() functionality and a get_file_content() functionality

    # def get_abs_path(self, path=None, section=None):
    #     """
    #     Get the absolute path to the folder associated with the
    #     Node in the AiiDA repository.

    #     :param str path: the name of the subfolder inside the section. If None
    #                      returns the abspath of the folder. Default = None.
    #     :param section: the name of the subfolder ('path' by default).
    #     :return: a string with the absolute path

    #     For the moment works only for one kind of files, 'path' (internal files)
    #     """
    #     if path is None:
    #         return self.folder.abspath
    #     if section is None:
    #         section = self._path_subfolder_name
    #     if os.path.isabs(path):
    #         raise ValueError("The path in get_abs_path must be relative")
    #     return self.folder.get_subfolder(section, reset_limit=True).get_abs_path(path, check_existence=True)


@six.add_metaclass(abc.ABCMeta)
class BackendNode(backends.BackendEntity, RepositoryMixin):
    """
    Backend node class
    """

    # pylint: disable=too-many-public-methods

    def _init_backend_node(self):
        """
        Initialize internal variables for the backend node
        
        This needs to be called explicitly in each specific
        subclass implementation of the init.
        """
        self._attrs_cache = {}

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = list()

        # Calls the initialisation from the RepositoryMixin
        self._init_repository()

        # TODO: decide what to do with _init_internal_params

    # region db_columns

    @property
    @abc.abstractmethod
    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """
        pass

    @abc.abstractmethod
    def _increment_version_number(self):
        """
        Increment the node version number of this node by one
        directly in the database
        """
    @property
    @abc.abstractmethod
    def uuid(self):
        """
        The node UUID

        :return: the uuid
        """

    @property
    @abc.abstractmethod
    def process_type(self):
        """
        The node process_type

        :return: the process type
        """

    @property
    @abc.abstractmethod
    def public(self):
        """
        Return the value of the 'public' field in the DB
        """
        self._ensure_model_uptodate(attribute_names=['public'])
        return self._dbmodel.public

    @abc.abstractmethod
    def _ensure_model_uptodate(self, attribute_names=None):
        """
        Expire specific fields of the dbmodel (or, if attribute_names
        is not specified, all of them), so they will be re-fetched
        from the DB.

        :param attribute_names: by default, expire all columns.
             If you want to expire only specific columns, pass
             a list of strings with the column names.
        """
        pass

    @abc.abstractmethod
    def get_computer(self):
        """
        Get the computer associated to the node.
	    For a CalcJobNode, this represents the computer on which the calculation was run.
 	    However, this can be used also for (some) data nodes, like RemoteData, to indicate
	    on which computer the data is sitting.

        :return: the Computer object or None.
        """
        pass

    def set_computer(self, computer):
        """
        Set the computer to be used by the node.

        Note that the computer makes sense only for some nodes: Calculation,
        RemoteData, ...

        :param computer: the computer object
        """
        from aiida import orm

        if self._to_be_stored:
            if not computer.is_stored:
                raise ValueError("The computer instance has not yet been stored")
            if isinstance(computer, orm.Computer):
                computer = computer.backend_entity
            self._set_db_computer(computer)
        else:
            raise ModificationNotAllowed("Node with uuid={} was already stored".format(self.uuid))

    @abc.abstractmethod
    def _set_db_computer(self, computer):
        """
        Set the computer directly inside the dbnode member, in the DB.

        DO NOT USE DIRECTLY.

        :param computer: the computer object
        """
        pass

    @abstractmethod
    def get_user(self):
        """
        Get the user.

        :return: a User model object
        :rtype: :class:`aiida.orm.User`
        """
        pass

    @abstractmethod
    def set_user(self, user):
        """
        Set the user

        :param user: The new user
        """
        pass

    @property
    @abc.abstractmethod
    def ctime(self):
        """
        Return the creation time of the node.
        """
        pass

    @property
    @abc.abstractmethod
    def mtime(self):
        """
        Return the modification time of the node.
        """
        pass

    @property
    @abc.abstractmethod
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        pass

    @property
    @abc.abstractmethod
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """
        return self._get_db_label_field()


    @label.setter
    @abc.abstractmethod
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """
        self._update_db_label_field()

    @abstractmethod
    def _get_db_label_field(self):
        """
        Get the label field acting directly on the DB

        :return: a string.
        """
        pass

    @abstractmethod
    def _update_db_label_field(self, field_value):
        """
        Set the label field acting directly on the DB
        """
        pass

    @property
    @abc.abstractmethod
    def description(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """
        return self._get_db_description_field()
        
    @description.setter
    @abc.abstractmethod
    def description(self, description):
        """
        Set the description of the node

        :param desc: a string
        """
        self._update_db_label_field(label)

    @abstractmethod
    def _get_db_description_field(self):
        """
        Get the description of this node, acting directly at the DB level
        """
        pass

    @abstractmethod
    def _update_db_description_field(self, field_value):
        """
        Update the description of this node, acting directly at the DB level

        :param field_value: the new value of the description field
        """
        pass

    # endregion

    # region Attributes

    @property
    def attrs_items(self):
        """
        Iterator over the attributes, returning tuples (key, value)

        :return: a generator of the (key, value) pairs
        """
        if not self.is_stored:
            for key, value in self._attrs_cache.items():
                yield (key, value)
        else:
            for key, value in self._get_db_attrs_items():
                yield (key, value)

    @abc.abstractmethod
    def _get_db_attrs_items(self):
        """
        Iterator over the attributes, returning tuples (key, value),
        that actually performs the job directly on the DB.

        :return: a generator of the (key, value) pairs
        """

    @property
    def attrs_keys(self):
        """
        Iterator over the attributes, returning keys
        
        Note: It is independent of the attrs_items
        because it is typically faster to retrieve only the keys
        from the database, especially if the values are big.

        :return: a generator of the keys
        """
        if not self.is_stored:
            for key, value in self._attrs_cache.items():
                yield (key, value)
        else:
            for key, value in self._get_db_attrs_keys():
                yield (key, value)

    @abc.abstractmethod
    def _get_db_attrs_keys(self):
        """
        Iterator over the attributes, returning the attribute keys only,
        that actually performs the job directly on the DB.

        Note: It is independent of the _get_db_attrs_items
        because it is typically faster to retrieve only the keys
        from the database, especially if the values are big.    

        :return: a generator of the keys
        """

    def set_attr(self, key, value, clean=True, stored_check=True):
        """
        Set an attribute on this node

        :param key: key name
        :type key: str
        :param value: the value
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
            self._set_db_attr(key, clean_value(value))
            self._increment_version_number()

    @abc.abstractmethod
    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        :param key: key name
        :param value: its value
        """

    def append_to_attr(self, key, value, clean=True):
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

        self.set_attr(key, values, clean=False)

    def del_attr(self, key, stored_check=True):
        """
        Delete an attribute from this node

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
            self._del_db_attr(key)
            self._increment_version_number()

    @abc.abstractmethod
    def _del_db_attr(self, key):
        """
        Delete an attribute directly from the DB

        :param key: The key of the attribute to delete
        """

    def del_all_attrs(self):
        """
        Delete all attributes associated to this node.

        :raise ModificationNotAllowed: if the Node was already stored.
        """
        # I have to convert the attrs in a list, because the list will change
        # while deleting elements
        for attr_name in list(self.attrs_keys):
            self.del_attr(attr_name)

    def get_attr(self, key, default=_NO_DEFAULT):
        """
        Get one attribute.

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
                return self._get_db_attr(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            return default

    @abc.abstractmethod
    def _get_db_attr(self, key):
        """
        Return the attribute value, directly from the DB.

        :param key: the attribute key
        :return: the attribute value
        :raise AttributeError: if the attribute does not exist.
        """

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

        if self._to_be_stored:
            raise ModificationNotAllowed("The extras of a node can be set only after " "storing the node")
        self._set_db_extra(key, clean_value(value), exclusive)
        self._increment_version_number()

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

        if self._to_be_stored:
            raise ModificationNotAllowed("The extras of a node can be set only after " "storing the node")

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
            if not self.is_stored:
                raise AttributeError("DbExtra '{}' does not exist yet, the " "node is not stored".format(key))
            else:
                return self._get_db_extra(key)
        except AttributeError as error:
            try:
                return args[0]
            except IndexError:
                raise error

    @abstractmethod
    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
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
        return dict(self.extras_items)

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
        if self._to_be_stored:
            raise ModificationNotAllowed("The extras of a node can be set and deleted " "only after storing the node")
        self._del_db_extra(key)
        self._increment_version_number()

    @abstractmethod
    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        pass

    @property
    def extras_keys(self):
        """
        Get the keys of the extras.

        :return: a list of strings
        """
        for key, value in self.extras_items:
            yield key

    @property
    def extras_items(self):
        """
        Iterator over the extras, returning tuples (key, value)

        :todo: verify that I am not creating a list internally
        """
        if self._to_be_stored:
            # If it is not stored yet, there are no extras that can be
            # added (in particular, we do not even have an ID to use!)
            # Return without value, meaning that this is an empty generator
            return
            yield  # Needed after return to convert it to a generator # pylint: disable=unreachable
        for extra in self._db_extras_items():
            yield extra

    @abstractmethod
    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        pass

    # endregion

    # region Links

    @property
    def has_cached_links(self):
        """
        Return whether there are unstored incoming links in the cache.

        :return: boolean, True when there are links in the incoming cache, False otherwise
        """
        return bool(self._incoming_cache)

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
            self._add_db_link_from(source, link_type, link_label)
        else:
            self._add_cachelink_from(source, link_type, link_label)

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
        type_check(link_type, LinkType, 'the link_type should be a value from the LinkType enum')
        type_check(source, Node, 'the source should be a Node instance')

        from aiida.orm.utils.links import validate_link
        validate_link(source, self, link_type, link_label)

    def validate_outgoing(self, target, link_type, link_label):  # pylint: disable=unused-argument
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
        type_check(link_type, LinkType, 'the link_type should be a value from the LinkType enum')
        type_check(target, Node, 'the target should be a Node instance')

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

    @abc.abstractmethod
    def _add_db_link_from(self, src, link_type, label):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)

        :note: this function should not be called directly; it acts directly on
            the database.

        :param src: the source object
        :param str label: the name of the label to set the link from src.
        """

    # endregion

    # region Comments

    def add_comment(self, content, user=None):
        """
        Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """
        from aiida import orm
        from aiida.orm.comments import Comment

        user = user or orm.User.objects.get_default()
        return Comment(node=self, user=user, content=content).store()

    def get_comment(self, identifier):
        """
        Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """
        from aiida.orm.comments import Comment
        return Comment.objects.get(comment=identifier)

    def get_comments(self):
        """
        Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """
        from aiida.orm.comments import Comment
        return Comment.objects.find(filters={'dbnode_id': self.pk}, order_by=[{'id': 'asc'}])

    def update_comment(self, identifier, content):
        """
        Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """
        from aiida.orm.comments import Comment
        comment = Comment.objects.get(comment=identifier)
        comment.set_content(content)

    def remove_comment(self, identifier):
        """
        Delete an existing comment.

        :param identifier: the comment pk
        """
        from aiida.orm.comments import Comment
        Comment.objects.delete(comment=identifier)

    # endregion

    # region PythonMethods

    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust
        too much this function!
        """
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    # endregion

    # region Deprecated
    ## While we're striving to avoid duplication of deprecated
    ## methods, in this specific case it is simple to just keep
    ## these functions here (as the logic is backend-specific)
    @abc.abstractmethod
    def _get_db_output_links(self, link_type):
        """
        Return a list of tuples (label, aiida_class) for each output link,
        possibly filtering only by those of a given type.

        :param link_type: if not None, a link type to filter results
        :return:  a list of tuples (label, aiida_class)
        """
        pass

    @abc.abstractclassmethod
    def _get_db_input_links(self, link_type):
        """
        Return a list of tuples (label, aiida_class) for each input link,
        possibly filtering only by those of a given type.

        :param link_type: if not None, a link type to filter results
        :return:  a list of tuples (label, aiida_class)
        """
        pass

    # endregion

    def store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, no transaction is used. This is meant to be used ONLY if the outer
            calling function has already a transaction open!
        """
        if self.is_stored:
            raise ModificationNotAllowed('Node<{}> is already stored'.format(self.id))

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self._incoming_cache:
            try:
                link_triple.node._check_are_parents_stored()
            except ModificationNotAllowed:
                raise ModificationNotAllowed(
                    'source Node<{}> has unstored parents, cannot proceed (only direct parents can be unstored and '
                    'will be stored by store_all, not grandparents or other ancestors'.format(link_triple.node.pk))

        self._db_store_all(with_transaction, use_cache=use_cache)
        return self

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
        # TODO: with_transaction is currently ignored
        with self.backend.transaction():
            self._store_input_nodes()
            self.store()
            # TODO: check if this is called automatically in .store()
            #self._store_cached_input_links(with_transaction=False)

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
            raise exceptions.StoringNotAllowed(self._unstorable_message)

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
                raise ModificationNotAllowed(
                    "Cannot store the incoming link triple {} because the source node is not stored. Either store it "
                    "first, or call _store_input_links with `store_parents` set to True".format(link_triple.link_label))

    # TODO: check this implementation, before it was backend-specific!
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
        # TODO: there used to be a self.is_stored check here, see
        # if it is still needed

        # TODO: with_transaction ignored here. Probably use this pattern:
        #if with_transaction:
        #    context_man = self.backend.transaction()
        #else:
        #    context_man = EmptyContextManager()
        # AND THEN
        # with context_man:
        # below. to decide if this is the correct way of doing it.

        self._check_are_parents_stored()

        # I have to store only those links where the source is already stored
        for link_triple in self._incoming_cache:
            self._add_db_link_from(*link_triple)

        # If everything went smoothly, clear the entries from the cache.
        # I do it here because I delete them all at once if no error
        # occurred; otherwise, links will not be stored and I
        # should not delete them from the cache (but then an exception
        # would have been raised, and the following lines are not executed)
        self._incoming_cache = list()

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


@six.add_metaclass(abc.ABCMeta)
class BackendNodeCollection(backends.BackendCollection[BackendNode]):
    """The collection of Node entries."""

    # pylint: disable=too-few-public-methods

    ENTITY_CLASS = BackendNode
