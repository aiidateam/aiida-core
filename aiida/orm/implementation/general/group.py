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

from aiida.common.exceptions import UniquenessError, NotExistent, MultipleObjectsError
from aiida.common.utils import abstractclassmethod, abstractstaticmethod


def get_group_type_mapping():
    """
    Return a dictionary with ``{short_name: proper_long_name_in_DB}`` format,
    where ``short_name`` is the name to use on the command line, while
    ``proper_long_name_in_DB`` is the string stored in the ``type`` field of the
    DbGroup table.

    It is defined as a function so that the import statements are confined
    inside here.
    """
    from aiida.orm.data.upf import UPFGROUP_TYPE
    from aiida.orm.autogroup import VERDIAUTOGROUP_TYPE
    from aiida.orm.importexport import IMPORTGROUP_TYPE

    return {'data.upf': UPFGROUP_TYPE,
            'import': IMPORTGROUP_TYPE,
            'autogroup.run': VERDIAUTOGROUP_TYPE}


class AbstractGroup(object):
    """
    An AiiDA ORM implementation of group of nodes.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Create a new group. Either pass a dbgroup parameter, to reload
        ad group from the DB (and then, no further parameters are allowed),
        or pass the parameters for the Group creation.

        :param dbgroup: the dbgroup object, if you want to reload the group
          from the DB rather than creating a new one.
        :param name: The group name, required on creation
        :param description: The group description (by default, an empty string)
        :param user: The owner of the group (by default, the automatic user)
        :param type_string: a string identifying the type of group (by default,
           an empty string, indicating an user-defined group.
        """
        pass

    @abstractproperty
    def name(self):
        """
        :return: the name of the group as a string
        """
        pass

    @abstractproperty
    def description(self):
        """
        :return: the description of the group as a string
        """
        pass

    @description.setter
    @abstractmethod
    def description(self, value):
        """
        :return: the description of the group as a string
        """
        pass

    @abstractproperty
    def type_string(self):
        """
        :return: the string defining the type of the group
        """
        pass

    @abstractproperty
    def user(self):
        """
        :return: a Django DbUser object, representing the user associated to
          this group.
        """
        pass

    @abstractproperty
    def dbgroup(self):
        """
        :return: the corresponding Django DbGroup object.
        """
        pass

    @abstractproperty
    def pk(self):
        """
        :return: the principal key (the ID) as an integer, or None if the
           node was not stored yet
        """
        pass

    @abstractproperty
    def id(self):
        """
        :return: the principal key (the ID) as an integer, or None if the
           node was not stored yet
        """
        pass

    @abstractproperty
    def uuid(self):
        """
        :return: a string with the uuid
        """
        pass

    @abstractstaticmethod
    def get_db_columns():
        """
        This method returns a list with the column names and types of the table
        corresponding to this class.
        :return: a list with the names of the columns
        """
        pass

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        """
        Try to retrieve a group from the DB with the given arguments;
        create (and store) a new group if such a group was not present yet.

        :return: (group, created) where group is the group (new or existing,
          in any case already stored) and created is a boolean saying
        """
        res = cls.query(name=kwargs.get("name"),
                        type_string=kwargs.get("type_string"))

        if res is None or len(res) == 0:
            bla = cls(*args, **kwargs).store(), True
            return bla
        elif len(res) > 1:
            raise MultipleObjectsError("More than one groups found in the "
                                       "database")
        else:
            return res[0], False

    @abstractmethod
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying
        with Django. Be careful, though, not to pass it to a wrong field!
        This only returns the local DB principal key (pk) value.

        :return: the integer pk of the node or None if not stored.
        """
        pass

    @abstractproperty
    def is_stored(self):
        """
        :return: True if the respective DbNode has been already saved in the
          DB, False otherwise
        """
        pass

    @abstractmethod
    def store(self):
        pass

    @abstractmethod
    def add_nodes(self, nodes):
        """
        Add a node or a set of nodes to the group.

        :note: The group must be already stored.

        :note: each of the nodes passed to add_nodes must be already stored.

        :param nodes: a Node or DbNode object to add to the group, or
          a list of Nodes or DbNodes to add.
        """
        pass

    @abstractproperty
    def nodes(self):
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().
        """
        pass

    @abstractmethod
    def remove_nodes(self, nodes):
        """
        Remove a node or a set of nodes to the group.

        :note: The group must be already stored.

        :note: each of the nodes passed to add_nodes must be already stored.

        :param nodes: a Node or DbNode object to add to the group, or
          a list of Nodes or DbNodes to add.
        """
        pass

    @abstractclassmethod
    def query(cls, name=None, type_string="", pk=None, uuid=None, nodes=None,
              user=None, node_attributes=None, past_days=None, **kwargs):
        """
        Query for groups.
        :note:  By default, query for user-defined groups only (type_string=="").
          If you want to query for all type of groups, pass type_string=None.
          If you want to query for a specific type of groups, pass a specific
          string as the type_string argument.

        :param name: the name of the group
        :param nodes: a node or list of nodes that belongs to the group (alternatively,
          you can also pass a DbNode or list of DbNodes)
        :param pk: the pk of the group
        :param uuid: the uuid of the group
        :param type_string: the string for the type of node; by default, look
          only for user-defined groups (see note above).
        :param user: by default, query for groups of all users; if specified,
          must be a DbUser object, or a string for the user email.
        :param past_days: by default, query for all groups; if specified, query
          the groups created in the last past_days. Must be a datetime object.
        :param node_attributes: if not None, must be a dictionary with
          format {k: v}. It will filter and return only groups where there
          is at least a node with an attribute with key=k and value=v.
          Different keys of the dictionary are joined with AND (that is, the
          group should satisfy all requirements.
          v can be a base data type (str, bool, int, float, ...)
          If it is a list or iterable, that the condition is checked so that
          there should be at least a node in the group with key=k and
          value=each of the values of the iterable.
        :param kwargs: any other filter to be passed to DbGroup.objects.filter

          Example: if ``node_attributes = {'elements': ['Ba', 'Ti'],
             'md5sum': 'xxx'}``, it will find groups that contain the node
             with md5sum = 'xxx', and moreover contain at least one node for
             element 'Ba' and one node for element 'Ti'.
        """
        pass

    @classmethod
    def get(cls, *args, **kwargs):
        queryresults = cls.query(*args, **kwargs)

        if len(queryresults) == 1:
            return queryresults[0]
        elif len(queryresults) == 0:
            raise NotExistent("No Group matching the query found")
        else:
            raise MultipleObjectsError("More than one Group found -- "
                                       "I found {}".format(len(queryresults)))

    @classmethod
    def get_from_string(cls, string):
        """
        Get a group from a string.
        If only the name is provided, without colons,
        only user-defined groups are searched;
        add ':type_str' after the group name to choose also
        the type of the group equal to 'type_str'
        (e.g. 'data.upf', 'import', etc.)

        :raise ValueError: if the group type does not exist.
        :raise NotExistent: if the group is not found.
        """
        name, sep, typestr = string.rpartition(':')
        if not sep:
            name = typestr
            typestr = ""
        if typestr:
            try:
                internal_type_string = get_group_type_mapping()[typestr]
            except KeyError:
                msg = ("Invalid group type '{}'. Valid group types are: "
                       "{}".format(typestr, ",".join(sorted(
                    get_group_type_mapping().keys()))))
                raise ValueError(msg)
        else:
            internal_type_string = ""

        try:
            group = cls.get(name=name,
                            type_string=internal_type_string)
            return group
        except NotExistent:
            if typestr:
                msg = (
                    "No group of type '{}' with name '{}' "
                    "found.".format(typestr, name))
            else:
                msg = (
                    "No user-defined group with name '{}' "
                    "found.".format(name))
            raise NotExistent(msg)

    def is_user_defined(self):
        """
        :return: True if the group is user defined, False otherwise
        """
        return not self.type_string

    @abstractmethod
    def delete(self):
        """
        Delete the group from the DB
        """
        pass

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.type_string:
            return '"{}" [type {}], of user {}'.format(
                self.name, self.type_string, self.user.email)
        else:
            return '"{}" [user-defined], of user {}'.format(
                self.name, self.user.email)
