# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-member
"""Django Group entity"""
from collections.abc import Iterator, Sized

# pylint: disable=no-name-in-module,import-error
from django.db import transaction

from aiida.backends.djsite.db import models
from aiida.common.lang import type_check
from aiida.orm.implementation.groups import BackendGroup, BackendGroupCollection

from . import entities, users, utils

__all__ = ('DjangoGroup', 'DjangoGroupCollection')


class DjangoGroup(entities.DjangoModelEntity[models.DbGroup], BackendGroup):  # pylint: disable=abstract-method
    """The Django group object"""
    MODEL_CLASS = models.DbGroup

    def __init__(self, backend, label, user, description='', type_string=''):
        """Construct a new Django group"""
        type_check(user, users.DjangoUser)
        super().__init__(backend)

        self._dbmodel = utils.ModelWrapper(
            models.DbGroup(label=label, description=description, user=user.dbmodel, type_string=type_string)
        )

    @property
    def label(self):
        return self._dbmodel.label

    @label.setter
    def label(self, label):
        """
        Attempt to change the label of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired label, a
        UniquenessError will be raised

        :param label : the new group label
        :raises aiida.common.UniquenessError: if another group of same type and label already exists
        """
        self._dbmodel.label = label

    @property
    def description(self):
        return self._dbmodel.description

    @description.setter
    def description(self, value):
        self._dbmodel.description = value

    @property
    def type_string(self):
        return self._dbmodel.type_string

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbmodel.user)

    @user.setter
    def user(self, new_user):
        type_check(new_user, users.DjangoUser)
        assert new_user.backend == self.backend, 'User from a different backend'
        self._dbmodel.user = new_user.dbmodel

    @property
    def uuid(self):
        return str(self._dbmodel.uuid)

    def __int__(self):
        if not self.is_stored:
            return None

        return self._dbnode.pk

    def store(self):
        if not self.is_stored:
            with transaction.atomic():
                if self.user is not None and not self.user.is_stored:
                    self.user.store()
                    # We now have to reset the model's user entry because
                    # django will have assigned the user an ID but this
                    # is not automatically propagated to us
                    self._dbmodel.user = self.user.dbmodel
                self._dbmodel.save()

        # To allow to do directly g = Group(...).store()
        return self

    def count(self):
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """
        return self._dbmodel.dbnodes.count()

    def clear(self):
        """Remove all the nodes from this group."""
        self._dbmodel.dbnodes.clear()

    @property
    def nodes(self):
        """Get an iterator to the nodes in the group"""

        class NodesIterator(Iterator, Sized):
            """The nodes iterator"""

            def __init__(self, dbnodes, backend):
                super().__init__()
                self._backend = backend
                self._dbnodes = dbnodes
                self.generator = self._genfunction()

            def _genfunction(self):
                # Best to use dbnodes.iterator() so we load entities from the database as we need them
                # see: http://blog.etianen.com/blog/2013/06/08/django-querysets/
                for node in self._dbnodes.iterator():
                    yield self._backend.get_backend_entity(node)

            def __iter__(self):
                return self

            def __len__(self):
                return len(self._dbnodes)

            def __getitem__(self, value):
                if isinstance(value, slice):
                    return [self._backend.get_backend_entity(n) for n in self._dbnodes[value]]

                return self._backend.get_backend_entity(self._dbnodes[value])

            def __next__(self):
                return next(self.generator)

        return NodesIterator(self._dbmodel.dbnodes.all(), self._backend)

    def add_nodes(self, nodes, **kwargs):
        from .nodes import DjangoNode

        super().add_nodes(nodes)

        node_pks = []

        for node in nodes:

            if not isinstance(node, DjangoNode):
                raise TypeError(f'invalid type {type(node)}, has to be {DjangoNode}')

            if not node.is_stored:
                raise ValueError('At least one of the provided nodes is unstored, stopping...')

            node_pks.append(node.pk)

        self._dbmodel.dbnodes.add(*node_pks)

    def remove_nodes(self, nodes):
        from .nodes import DjangoNode

        super().remove_nodes(nodes)

        node_pks = []

        for node in nodes:

            if not isinstance(node, DjangoNode):
                raise TypeError(f'invalid type {type(node)}, has to be {DjangoNode}')

            if not node.is_stored:
                raise ValueError('At least one of the provided nodes is unstored, stopping...')

            node_pks.append(node.pk)

        self._dbmodel.dbnodes.remove(*node_pks)


class DjangoGroupCollection(BackendGroupCollection):
    """The Django Group collection"""

    ENTITY_CLASS = DjangoGroup

    def delete(self, id):  # pylint: disable=redefined-builtin
        models.DbGroup.objects.filter(id=id).delete()
