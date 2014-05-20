class Group(object):
    """
    An AiiDA ORM implementation of group of nodes.
    """
    def __init__(self, **kwargs):
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.models import DbGroup
        
        dbgroup = kwargs.pop('dbgroup', None)
                
        if dbgroup is not None:
            if not isinstance(dbgroup, DbGroup):
                raise TypeError("dbgroup is not a DbGroup instance")
            if kwargs:
                raise ValueError("If you pass a dbgroups, you cannot pass any "
                                 "further parameter")
            
            self._dbgroup = dbgroup
        else: 
            name = kwargs.pop('name', None)           
            if name is None:
                raise ValueError("You have to specify a group name")
            group_type = kwargs.pop('type', "") # By default, an user group
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

    @property
    def type_string(self):        
        """
        :return: the string defining the type of the group
        """
        return self.dbgroup.type


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
            
    def add_nodes(self, nodes):
        from aiida.common.exceptions import ModificationNotAllowed, InternalError
        from aiida.djsite.db.models import DbNode
        from aiida.orm import Node

        if not self._is_stored:
            raise ModificationNotAllowed("Cannot add nodes to a group before "
                                         "storing")
        
        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if not isinstance(nodes, (list, tuple)):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "add_nodes, can only be a Node, DbNode, or a list "
                            "of such objects")

        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(
                                    str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            
        for node in nodes:
            if isinstance(node, DbNode):
                self.dbgroup.dbnodes.add(node)
            elif isinstance(node, Node):
                self.dbgroup.dbnodes.add(node.dbnode)
            else:
                raise InternalError("Should not be in this part of code... "
                                    "Found type {}".format(type(node)))
    
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
        raise NotImplementedError
    
    @classmethod
    def query(cls, name=None, typestring="", uuid=None, nodes=None):
        """
        Query for groups. 
        :note:  By default, query for user-defined groups only (typestring=="").
          If you want to query for all type of groups, pass typestring=None.
          If you want to query for a specific type of groups, pass a specific
          string as the typestring argument.
        
        :param name: the name of the group
        :param dbnodes: a node, list of nodes, or of pks (alternatively, you 
          can also pass a DbNode or list of DbNodes)
        :param uuid: the uuid of the node
        :param typestring: the string for the type of node; by default, look
          only for user-defined groups (see note above).
        """
        from django.db.models import Q
        
        from aiida.djsite.db.models import DbGroup, DbNode
        from aiida.orm import Node

        # Analyze args and kwargs to create the query        
        queryobject = Q()
        if name is not None:
            queryobject &= Q(name=name)

        if typestring is not None:
            queryobject &= Q(type=typestring)


        if uuid is not None:
            queryobject &= Q(uuid=uuid)
        
        if nodes is not None:
            pk_list = []
            
            if not isinstance(nodes, (list, tuple)):
                nodes = [nodes]
                
            for node in nodes:
                if not isinstance(node, (Node, DbNode)):
                    raise TypeError("At least one of the elements passed as "
                                    "nodes for the query on Group is neither "
                                    "a Node nor a DbNode")
                pk_list.append(node.pk)
            
            queryobject &= Q(dbnodes__in=pk_list)
    
        retlist = []
        for dbgroup in DbGroup.objects.filter(queryobject):
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
    
    def __str__(self):
        if self.type_string:
            return '<Group [type: {}] "{}">'.format(self.type_string, self.name)
        else:
            return '<Group [user-defined] "{}">'.format(self.name)
    