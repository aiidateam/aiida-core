# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class Group(object):
    """
    An AiiDA ORM implementation of group of nodes.
    """
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
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.models import DbGroup
        
        dbgroup = kwargs.pop('dbgroup', None)
                
        if dbgroup is not None:
            if isinstance(dbgroup, (int,long)):
                dbgroup = DbGroup.objects.get(pk=dbgroup)
            if not isinstance(dbgroup, DbGroup):
                raise TypeError("dbgroup is not a DbGroup instance, it is "
                                "instead {}".format(str(type(dbgroup))))
            if kwargs:
                raise ValueError("If you pass a dbgroups, you cannot pass any "
                                 "further parameter")
            
            self._dbgroup = dbgroup
        else: 
            name = kwargs.pop('name', None)           
            if name is None:
                raise ValueError("You have to specify a group name")
            group_type = kwargs.pop('type_string', "") # By default, an user group
            user = kwargs.pop('user', get_automatic_user())
            description = kwargs.pop('description', "")
            self._dbgroup = DbGroup(name=name, description=description,
                                    user=user, type=group_type)
            if kwargs:
                raise ValueError("Too many parameters passed to Group, the "
                                 "unknown parameters are: {}".format(
                                    ", ".join(kwargs.keys())))
            
    @property
    def name(self):        
        """
        :return: the name of the group as a string
        """
        return self.dbgroup.name

    @property
    def description(self):        
        """
        :return: the description of the group as a string
        """
        return self.dbgroup.description

    @description.setter
    def description(self, value):        
        """
        :return: the description of the group as a string
        """
        self.dbgroup.description = value

        # Update the entry in the DB, if the group is already stored
        if self._is_stored:
            self.dbgroup.save()


    @property
    def type_string(self):        
        """
        :return: the string defining the type of the group
        """
        return self.dbgroup.type

    @property
    def user(self):
        """
        :return: a Django DbUser object, representing the user associated to 
          this group.
        """
        return self.dbgroup.user

    @property
    def dbgroup(self):
        """
        :return: the corresponding Django DbGroup object.
        """
        return self._dbgroup

    @property
    def pk(self):
        """
        :return: the principal key (the ID) as an integer, or None if the
           node was not stored yet
        """
        return self._dbgroup.pk

    @property
    def uuid(self):
        """
        :return: a string with the uuid
        """
        return unicode(self.dbgroup.uuid)
    
    @classmethod
    def get_or_create(cls,*args,**kwargs):
        """
        Try to retrieve a group from the DB with the given arguments; 
        create (and store) a new group if such a group was not present yet.
        
        :return: (group, created) where group is the group (new or existing,
          in any case already stored) and created is a boolean saying 
        """
        from aiida.common.exceptions import UniquenessError
        try:
            # Try to create and store a new class
            return (cls(*args, **kwargs).store(), True)
        except UniquenessError:
            group = cls.get(*args, **kwargs)
            return (group, False)
    
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying
        with Django. Be careful, though, not to pass it to a wrong field!
        This only returns the local DB principal key (pk) value.
        
        :return: the integer pk of the node or None if not stored.
        """
        if self._to_be_stored:
            return None
        else:
            return self._dbnode.pk

    @property
    def _is_stored(self):
        """
        :return: True if the respective DbNode has been already saved in the
          DB, False otherwise
        """
        return self.pk is not None

    def store(self):
        from django.db import transaction, IntegrityError
        
        from aiida.common.exceptions import (
            ModificationNotAllowed, UniquenessError)
        
        if self._is_stored:
            raise ModificationNotAllowed("Cannot restore a group that was "
                                         "already stored")
        else:
            sid = transaction.savepoint()
            try:
                self.dbgroup.save()
            except IntegrityError:
                transaction.savepoint_rollback(sid)
                raise UniquenessError("A group with the same name (and of the "
                                      "same type) already "
                                      "exists, unable to store")

        # To allow to do directly g = Group(...).store()
        return self
        
    def add_nodes(self, nodes):
        """
        Add a node or a set of nodes to the group.
        
        :note: The group must be already stored.
        
        :note: each of the nodes passed to add_nodes must be already stored.
        
        :param nodes: a Node or DbNode object to add to the group, or 
          a list of Nodes or DbNodes to add.
        """
        import collections
        
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.djsite.db.models import DbNode
        from aiida.orm import Node

        if not self._is_stored:
            raise ModificationNotAllowed("Cannot add nodes to a group before "
                                         "storing")
        
        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, basestring) or not isinstance(
                nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "add_nodes, can only be a Node, DbNode, or a list "
                            "of such objects, it is instead {}".format(
                                str(type(nodes))))

        list_pk = []
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(
                                    str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            list_pk.append(node.pk)

        self.dbgroup.dbnodes.add(*list_pk)
    
    @property
    def nodes(self):
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for 
        the number of nodes in the group using len().
        """
    
        class iterator(object):
            def __init__(self, dbnodes):
                self.dbnodes = dbnodes
                self.generator = self._genfunction()
                
            def _genfunction(self):
                for n in self.dbnodes:
                    yield n.get_aiida_class()
                
            def __iter__(self):
                return self
            
            def __len__(self):
                return self.dbnodes.count()
            
            # For future python-3 compatibility
            def __next__(self):
                return self.next()
            
            def next(self):
                return next(self.generator)
                
        return iterator(self.dbgroup.dbnodes.all())
    
    def remove_nodes(self, nodes):
        """
        Remove a node or a set of nodes to the group.
        
        :note: The group must be already stored.
        
        :note: each of the nodes passed to add_nodes must be already stored.
        
        :param nodes: a Node or DbNode object to add to the group, or 
          a list of Nodes or DbNodes to add.
        """
        import collections
        
        from aiida.djsite.db.models import DbNode
        from aiida.orm import Node
        from aiida.common.exceptions import ModificationNotAllowed

        if not self._is_stored:
            raise ModificationNotAllowed("Cannot remove nodes from a group "
                                         "before storing")
        
        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, basestring) or not isinstance(
                nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "remove_nodes, can only be a Node, DbNode, or a "
                            "list of such objects, it is instead {}".format(
                                str(type(nodes))))
            
        list_pk = []
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(
                                    str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            list_pk.append(node.pk)

        self.dbgroup.dbnodes.remove(*list_pk)

    
    @classmethod
    def query(cls, name=None, type_string="", uuid=None, nodes=None, user=None,
              node_attributes=None):
        """
        Query for groups. 
        :note:  By default, query for user-defined groups only (type_string=="").
          If you want to query for all type of groups, pass type_string=None.
          If you want to query for a specific type of groups, pass a specific
          string as the type_string argument.
        
        :param name: the name of the group
        :param dbnodes: a node, list of nodes, or of pks (alternatively, you 
          can also pass a DbNode or list of DbNodes)
        :param uuid: the uuid of the node
        :param type_string: the string for the type of node; by default, look
          only for user-defined groups (see note above).
        :param user: by default, query for groups of all users; if specified,
          must be a DbUser object, or a string for the user email.
        :param node_attributes: if not None, must be a dictionary with
          format {k: v}. It will filter and return only groups where there
          is at least a node with an attribute with key=k and value=v.
          Different keys of the dictionary are joined with AND (that is, the
          group should satisfy all requirements.
          v can be a base data type (str, bool, int, float, ...)
          If it is a list or iterable, that the condition is checked so that
          there should be at least a node in the group with key=k and
          value=each of the values of the iterable.

          Example: if ``node_attributes = {'elements': ['Ba', 'Ti'],
             'md5sum': 'xxx'}``, it will find groups that contain the node
             with md5sum = 'xxx', and moreover contain at least one node for
             element 'Ba' and one node for element 'Ti'.
        """
        import collections
        
        from django.db.models import Q
        
        from aiida.djsite.db.models import DbGroup, DbNode, DbAttribute
        from aiida.orm import Node

        # Analyze args and kwargs to create the query        
        queryobject = Q()
        if name is not None:
            queryobject &= Q(name=name)

        if type_string is not None:
            queryobject &= Q(type=type_string)

        if uuid is not None:
            queryobject &= Q(uuid=uuid)
        
        if nodes is not None:
            pk_list = []
            
            if not isinstance(nodes, collections.Iterable):
                nodes = [nodes]
                
            for node in nodes:
                if not isinstance(node, (Node, DbNode)):
                    raise TypeError("At least one of the elements passed as "
                                    "nodes for the query on Group is neither "
                                    "a Node nor a DbNode")
                pk_list.append(node.pk)
            
            queryobject &= Q(dbnodes__in=pk_list)

        if user is not None:
            if isinstance(user, basestring):
                queryobject &= Q(user__email=user)
            else:
                queryobject &= Q(user=user)
    
        groups_pk = set(DbGroup.objects.filter(queryobject).values_list(
            'pk', flat=True))
    
        if node_attributes is not None:
            for k, vlist in node_attributes.iteritems():
                if isinstance(vlist, basestring) or not isinstance(
                    vlist, collections.Iterable):
                    vlist = [vlist]
                                    
                for v in vlist:
                    # This will be a dictionary of the type
                    # {'datatype': 'txt', 'tval': 'xxx') for instance, if
                    # the passed data is a string
                    base_query_dict = DbAttribute.get_query_dict(v)
                    # prepend to the key the right django string to SQL-join
                    # on the right table
                    query_dict = {'dbnodes__dbattributes__{}'.format(k2): v2 
                                  for k2, v2 in base_query_dict.iteritems()}
                    
                    # I narrow down the list of groups.
                    # I had to do it in this way, with multiple DB hits and
                    # not a single, complicated query because in SQLite
                    # there is a maximum of 64 tables in a join.
                    # Since typically one requires a small number of filters,
                    # this should be ok.
                    groups_pk = groups_pk.intersection(DbGroup.objects.filter(
                        pk__in=groups_pk, dbnodes__dbattributes__key=k,
                        **query_dict).values_list('pk', flat=True))
    
        retlist = []
        # Return sorted by pk
        for dbgroup in sorted(groups_pk):
            retlist.append(cls(dbgroup=dbgroup))
            
        return retlist
    
    @classmethod
    def get(cls, *args, **kwargs):
        from aiida.common.exceptions import NotExistent, MultipleObjectsError
        
        queryresults = cls.query(*args, **kwargs)
        
        if len(queryresults) == 1:
            return queryresults[0]
        elif len(queryresults) == 0:
            raise NotExistent("No Group matching the query found")
        else:
            raise MultipleObjectsError("More than one Group found -- "
                                       "I found {}".format(len(queryresults)))
    
    def is_user_defined(self):
        """
        :return: True if the group is user defined, False otherwise
        """
        return not self.type_string
    
    def delete(self):
        """
        Delete the group from the DB
        """
        if self.pk is not None:
            self.dbgroup.delete()
    
    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))
    
    def __str__(self):
        if self.type_string:
            return '"{}" [type {}], of user {}'.format(
                self.name, self.type_string, self.user.email)
        else:
            return '"{}" [user-defined], of user {}'.format(
                self.name, self.user.email)
    
