# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementation of the `BackendNode` and `BackendNodeCollection` classes."""

# pylint: disable=import-error,no-name-in-module
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError

from aiida.backends.djsite.db import models
from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm.implementation.utils import clean_value

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils as dj_utils
from .computers import DjangoComputer
from .users import DjangoUser


class DjangoNode(entities.DjangoModelEntity[models.DbNode], BackendNode):
    """Django Node backend entity"""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = models.DbNode
    LINK_CLASS = models.DbLink

    def __init__(
        self,
        backend,
        node_type,
        user,
        computer=None,
        process_type=None,
        label='',
        description='',
        ctime=None,
        mtime=None
    ):
        """Construct a new `BackendNode` instance wrapping a new `DbNode` instance.

        :param backend: the backend
        :param node_type: the node type string
        :param user: associated `BackendUser`
        :param computer: associated `BackendComputer`
        :param label: string label
        :param description: string description
        :param ctime: The creation time as datetime object
        :param mtime: The modification time as datetime object
        """
        # pylint: disable=too-many-arguments
        super().__init__(backend)

        arguments = {
            'user': user.dbmodel,
            'node_type': node_type,
            'process_type': process_type,
            'label': label,
            'description': description,
        }

        type_check(user, DjangoUser)

        if computer:
            type_check(computer, DjangoComputer, f'computer is of type {type(computer)}')
            arguments['dbcomputer'] = computer.dbmodel

        if ctime:
            type_check(ctime, datetime, f'the given ctime is of type {type(ctime)}')
            arguments['ctime'] = ctime

        if mtime:
            type_check(mtime, datetime, f'the given mtime is of type {type(mtime)}')
            arguments['mtime'] = mtime

        self._dbmodel = dj_utils.ModelWrapper(models.DbNode(**arguments))

    def clone(self):
        """Return an unstored clone of ourselves.

        :return: an unstored `BackendNode` with the exact same attributes and extras as self
        """
        arguments = {
            'node_type': self._dbmodel.node_type,
            'process_type': self._dbmodel.process_type,
            'user': self._dbmodel.user,
            'dbcomputer': self._dbmodel.dbcomputer,
            'label': self._dbmodel.label,
            'description': self._dbmodel.description,
        }

        clone = self.__class__.__new__(self.__class__)  # pylint: disable=no-value-for-parameter
        clone.__init__(self.backend, self.node_type, self.user)
        clone._dbmodel = dj_utils.ModelWrapper(models.DbNode(**arguments))  # pylint: disable=protected-access
        return clone

    @property
    def computer(self):
        """Return the computer of this node.

        :return: the computer or None
        :rtype: `BackendComputer` or None
        """
        try:
            return self.backend.computers.from_dbmodel(self._dbmodel.dbcomputer)
        except TypeError:
            return None

    @computer.setter
    def computer(self, computer):
        """Set the computer of this node.

        :param computer: a `BackendComputer`
        """
        type_check(computer, DjangoComputer, allow_none=True)

        if computer is not None:
            computer = computer.dbmodel

        self._dbmodel.dbcomputer = computer

    @property
    def user(self):
        """Return the user of this node.

        :return: the user
        :rtype: `BackendUser`
        """
        return self.backend.users.from_dbmodel(self._dbmodel.user)

    @user.setter
    def user(self, user):
        """Set the user of this node.

        :param user: a `BackendUser`
        """
        type_check(user, DjangoUser)
        self._dbmodel.user = user.dbmodel

    def add_incoming(self, source, link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :return: True if the proposed link is allowed, False otherwise
        :raise aiida.common.ModificationNotAllowed: if either source or target node is not stored
        """
        type_check(source, DjangoNode)

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('node has to be stored when adding an incoming link')

        if not source.is_stored:
            raise exceptions.ModificationNotAllowed('source node has to be stored when adding a link from it')

        self._add_link(source, link_type, link_label)

    def _add_link(self, source, link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        """
        savepoint_id = None

        try:
            # Transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            savepoint_id = transaction.savepoint()
            self.LINK_CLASS(input_id=source.id, output_id=self.id, label=link_label, type=link_type.value).save()
            transaction.savepoint_commit(savepoint_id)
        except IntegrityError as exception:
            transaction.savepoint_rollback(savepoint_id)
            raise exceptions.UniquenessError(f'failed to create the link: {exception}') from exception

    def clean_values(self):
        self._dbmodel.attributes = clean_value(self._dbmodel.attributes)
        self._dbmodel.extras = clean_value(self._dbmodel.extras)

    def store(self, links=None, with_transaction=True, clean=True):  # pylint: disable=arguments-differ
        """Store the node in the database.

        :param links: optional links to add before storing
        :param with_transaction: if False, do not use a transaction because the caller will already have opened one.
        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """
        import contextlib
        from aiida.backends.djsite.db.models import suppress_auto_now

        if clean:
            self.clean_values()

        with transaction.atomic() if with_transaction else contextlib.nullcontext():
            with suppress_auto_now([(models.DbNode, ['mtime'])]) if self.mtime else contextlib.nullcontext():
                # We need to save the node model instance itself first such that it has a pk
                # that can be used in the foreign keys that will be needed for setting the
                # attributes and links
                self.dbmodel.save()

                if links:
                    for link_triple in links:
                        self._add_link(*link_triple)

        return self


class DjangoNodeCollection(BackendNodeCollection):
    """The collection of Node entries."""

    ENTITY_CLASS = DjangoNode

    def get(self, pk):
        """Return a Node entry from the collection with the given id

        :param pk: id of the node
        """
        try:
            return self.ENTITY_CLASS.from_dbmodel(models.DbNode.objects.get(pk=pk), self.backend)
        except ObjectDoesNotExist:
            raise exceptions.NotExistent(f"Node with pk '{pk}' not found") from ObjectDoesNotExist

    def delete(self, pk):
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
        try:
            models.DbNode.objects.filter(pk=pk).delete()  # pylint: disable=no-member
        except ObjectDoesNotExist:
            raise exceptions.NotExistent(f"Node with pk '{pk}' not found") from ObjectDoesNotExist
