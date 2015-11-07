# -*- coding: utf-8 -*-

from sqlalchemy.exc import SQLAlchemyError


from aiida.orm.implementation.general.group import AbstractGroup
from aiida.backends.sqlalchemy import session


class Group(AbstractGroup):

    def __init__(self, **kwargs):
        dbgroup = kwargs.pop('dbgroup', None)

        if dbgroup is not None:
            if isinstance(dbgroup, (int, long)):
                dbgroup = DbGroup.query.filter_by(id=dbgroup).first()
                if not dbgroup:
                    raise NotExistent("Group with pk={} does not exist".format(
                        dbgroup))

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
            group_type = kwargs.pop('type_string', "")  # By default, an user group
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
        return self.dbgroup.name

    @property
    def description(self):
        return self.dbgroup.description

    @description.setter
    def description(self, value):
        self.dbgroup.description = value

        # Update the entry in the DB, if the group is already stored
        if self._is_stored:
            self.dbgroup.save()


    @property
    def type_string(self):
        return self.dbgroup.type

    @property
    def user(self):
        return self.dbgroup.user

    @property
    def dbgroup(self):
        return self._dbgroup

    @property
    def pk(self):
        return self._dbgroup.id

    @property
    def uuid(self):
        return unicode(self.dbgroup.uuid)

    def __int__(self):
        if self._to_be_stored:
            return None
        else:
            return self._dbnode.id

    @property
    def _is_stored(self):
        return self.id is not None

    def store(self):
        if self._is_stored:
            raise ModificationNotAllowed("Cannot restore a group that was "
                                         "already stored")
        else:
            try:
                with session.begin_nested():
                    self.dbgroup.save(commit=False)
            except SQLAlchemyError:
                raise UniquenessError("A group with the same name (and of the "
                                      "same type) already "
                                      "exists, unable to store")

        return self

    def add_nodes(self, nodes):
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
            if node.id is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            list_pk.append(node.id)

        self.dbgroup.dbnodes.extend(list_pk)

    @property
    def nodes(self):
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

        list(map(lambda _id: self.dbgroup.dbnodes.remove, list_pk))


    @classmethod
    def query(cls, name=None, type_string="", pk = None, uuid=None, nodes=None,
              user=None, node_attributes=None, past_days=None, **kwargs):
        # TODO SP: query method

    def delete(self):
        if self.id is not None:
            session.delete(self.dbgroup)
