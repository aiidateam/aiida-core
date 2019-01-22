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

from . import backends

__all__ = 'BackendNode', 'BackendNodeCollection'


@six.add_metaclass(abc.ABCMeta)
class BackendNode(backends.BackendEntity):
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

        self._temp_folder = None
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

        # TODO: decide what to do with _init_internal_params

    # region db_columns

    @abc.abstractproperty
    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """

    @abc.abstractmethod
    def increment_version_number(self):
        """
        Increment the version number of this node by one
        """

    @abc.abstractproperty
    def uuid(self):
        """
        The node UUID

        :return: the uuid
        """

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

    @property
    @abc.abstractmethod
    def mtime(self):
        """
        Return the modification time of the node.
        """

    @property
    @abc.abstractmethod
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """

    @property
    @abc.abstractmethod
    def nodeversion(self):
        """
        Return the version of the 
        :return: A version integer
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """

    @label.setter
    @abc.abstractmethod
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """

    @property
    @abc.abstractmethod
    def description(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """

    @description.setter
    @abc.abstractmethod
    def description(self, description):
        """
        Set the description of the node

        :param desc: a string
        """

    # endregion

    # region Attributes

    def attritems(self):
        """
        Iterator over the attributes, returning tuples (key, value)
        """
        if not self.is_stored:
            for key, value in self._attrs_cache.items():
                yield (key, value)
        else:
            for key, value in self.backend_entity.iterattrs():
                yield key, value

    @abc.abstractmethod
    def attrs(self):
        """
        The attribute keys

        :return: a generator of the keys
        """

    @abc.abstractmethod
    def iterattrs(self):
        """
        Get an iterator to all the attributes

        :return: the attributes iterator
        """

    @abc.abstractmethod
    def get_attrs(self):
        """
        Return a dictionary with all attributes of this node.
        """

    @abc.abstractmethod
    def set_attr(self, key, value):
        """
        Set an attribute on this node

        :param key: key name
        :type key: str
        :param value: the value
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
    def del_attr(self, key):
        """
        Delete an attribute from this node

        :param key: the attribute key
        :type key: str
        """

    @abc.abstractmethod
    def del_all_attrs(self):
        """
        Delete all attributes associated to this node.

        :raise ModificationNotAllowed: if the Node was already stored.
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

    # pylint: disable=unused-variable
    def extras_keys(self):
        """
        Get the keys of the extras.

        :return: a list of strings
        """
        for key, value in self.iterextras():
            yield key

    # pylint: disable=unreachable
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
            yield  # Needed after return to convert it to a generator
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

    def has_cached_links(self):
        """
        Return whether there are unstored incoming links in the cache.

        :return: boolean, True when there are links in the incoming cache, False otherwise
        """
        return bool(self._incoming_cache)

    @abc.abstractmethod
    def get_input_links(self, link_type):
        """
        Get the inputs linked by the given link type

        :param link_type: the input links type
        :return: a list of input backend entities
        """

    @abc.abstractmethod
    def get_output_links(self, link_type):
        """
        Get the outputs linked by the given link type

        :param link_type: the output links type
        :return: a list of output backend entities
        """

    @abc.abstractmethod
    def add_link_from(self, src, link_type, label):
        """
        Add an incoming link from a given source node

        :param src: the source node
        :type src: :class:`aiida.orm.implementation.Node`
        :param link_type: the link type
        :param label: the link label
        """

    @abc.abstractmethod
    def remove_link_from(self, label):
        """
        Remove an incoming link with the given label

        :param label: the label of the link to remove
        """

    @abc.abstractmethod
    def replace_link_from(self, src, link_type, label):
        """
        Replace an existing link

        :param src: the source node
        :type src: :class:`aiida.orm.implementation.Node`
        :param link_type: the link type
        :param label: the link label
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


@six.add_metaclass(abc.ABCMeta)
class BackendNodeCollection(backends.BackendCollection[BackendNode]):
    """The collection of Node entries."""

    # pylint: disable=too-few-public-methods

    ENTITY_CLASS = BackendNode
