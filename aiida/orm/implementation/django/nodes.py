# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementation of the `BackendNode` and `BackendNodeCollection` classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=import-error,no-name-in-module
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError

from aiida.backends.djsite.db import models
from aiida.common import exceptions
from aiida.common.lang import type_check

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils
from .computers import DjangoComputer
from .users import DjangoUser


class DjangoNode(entities.DjangoModelEntity[models.DbNode], BackendNode):
    """Django Node backend entity"""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = models.DbNode
    ATTRIBUTE_CLASS = models.DbAttribute
    EXTRA_CLASS = models.DbExtra
    LINK_CLASS = models.DbLink

    def __init__(self,
                 backend,
                 node_type,
                 user,
                 computer=None,
                 process_type=None,
                 label='',
                 description='',
                 ctime=None,
                 mtime=None):
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
        super(DjangoNode, self).__init__(backend)

        arguments = {
            'user': user.dbmodel,
            'node_type': node_type,
            'process_type': process_type,
            'label': label,
            'description': description,
        }

        type_check(user, DjangoUser)

        if computer:
            type_check(computer, DjangoComputer, 'computer is of type {}'.format(type(computer)))
            arguments['dbcomputer'] = computer.dbmodel

        if ctime:
            type_check(ctime, datetime, 'the given ctime is of type {}'.format(type(ctime)))
            arguments['ctime'] = ctime

        if mtime:
            type_check(mtime, datetime, 'the given mtime is of type {}'.format(type(mtime)))
            arguments['mtime'] = mtime

        self._dbmodel = utils.ModelWrapper(models.DbNode(**arguments))

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
        clone._dbmodel = utils.ModelWrapper(models.DbNode(**arguments))  # pylint: disable=protected-access
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

    def get_attribute(self, key):
        """Return an attribute.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            return self.ATTRIBUTE_CLASS.get_value_for_node(dbnode=self.dbmodel, key=key)
        except AttributeError:
            raise AttributeError('Attribute `{}` does not exist'.format(key))

    def get_attributes(self, keys):
        """Return a set of attributes.

        :param keys: names of the attributes
        :return: the values of the attributes
        :raises AttributeError: if at least one attribute does not exist
        """
        raise NotImplementedError

    def set_attribute(self, key, value):
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        """
        self.ATTRIBUTE_CLASS.set_value_for_node(self.dbmodel, key, value)
        self._increment_version_number()

    def set_attributes(self, attributes):
        """Set attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: the new attributes to set
        """
        for key, value in attributes.items():
            self.ATTRIBUTE_CLASS.set_value_for_node(self.dbmodel, key, value)
        self._increment_version_number()

    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely reset any existing attributes and replace them with the new dictionary.

        :param attributes: the new attributes to set
        """
        self.ATTRIBUTE_CLASS.reset_values_for_node(self.dbmodel, attributes)
        self._increment_version_number()

    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        if not self.ATTRIBUTE_CLASS.has_key(self.dbmodel, key):
            raise AttributeError('Attribute `{}` does not exist'.format(key))

        self.ATTRIBUTE_CLASS.del_value_for_node(self.dbmodel, key)

    def delete_attributes(self, keys):
        """Delete multiple attributes.

        .. note:: The implementation should guarantee that all the keys that are to be deleted actually exist or the
            entire operation should be canceled without any change and an ``AttributeError`` should be raised.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least on of the attribute does not exist
        """
        raise NotImplementedError

    def clear_attributes(self):
        """Delete all attributes."""
        raise NotImplementedError

    def attributes_items(self):
        """Return an iterator over the attribute items.

        :return: an iterator with attribute key value pairs
        """
        for key, value in self._dbmodel.attributes.items():
            yield key, value

    def attributes_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        for key in self._dbmodel.attributes.keys():
            yield key

    def get_extra(self, key):
        """Return an extra.

        :param key: name of the extra
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            return self.EXTRA_CLASS.get_value_for_node(dbnode=self.dbmodel, key=key)
        except AttributeError:
            raise AttributeError('Extra `{}` does not exist'.format(key))

    def get_extras(self, keys):
        """Return a set of extras.

        :param keys: names of the extras
        :return: the values of the extras
        :raises AttributeError: if at least one extra does not exist
        """
        raise NotImplementedError

    def set_extra(self, key, value, increase_version=True):
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        :param increase_version: boolean, if True will increase the node version upon successfully setting the extra
        """
        self.EXTRA_CLASS.set_value_for_node(self.dbmodel, key, value)
        if increase_version:
            self._increment_version_number()

    def set_extras(self, extras):
        """Set extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: the new extras to set
        """
        for key, value in extras.items():
            self.EXTRA_CLASS.set_value_for_node(self.dbmodel, key, value)
        self._increment_version_number()

    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely reset any existing extras and replace them with the new dictionary.

        :param extras: the new extras to set
        """
        raise NotImplementedError

    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        if not self.EXTRA_CLASS.has_key(self.dbmodel, key):
            raise AttributeError('Extra `{}` does not exist'.format(key))

        self.EXTRA_CLASS.del_value_for_node(self.dbmodel, key)

    def delete_extras(self, keys):
        """Delete multiple extras.

        .. note:: The implementation should guarantee that all the keys that are to be deleted actually exist or the
            entire operation should be canceled without any change and an ``AttributeError`` should be raised.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least on of the extra does not exist
        """
        raise NotImplementedError

    def clear_extras(self):
        """Delete all extras."""
        raise NotImplementedError

    def extras_items(self):
        """Return an iterator over the extra items.

        :return: an iterator with extra key value pairs
        """
        for key, value in self._dbmodel.extras.items():
            yield key, value

    def extras_keys(self):
        """Return an iterator over the extras keys.

        :return: an iterator with extras keys
        """
        for key in self._dbmodel.extras.keys():
            yield key

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
            raise exceptions.UniquenessError('failed to create the link: {}'.format(exception))

    def store(self, attributes=None, links=None, with_transaction=True):
        """Store the node in the database.

        :param attributes: optional attributes to set before storing, will override any existing attributes
        :param links: optional links to add before storing
        """
        from aiida.common.lang import EmptyContextManager
        from aiida.backends.djsite.db.models import suppress_auto_now

        with transaction.atomic() if with_transaction else EmptyContextManager():
            with suppress_auto_now([(models.DbNode, ['mtime'])]) if self.mtime else EmptyContextManager():
                # We need to save the node model instance itself first such that it has a pk
                # that can be used in the foreign keys that will be needed for setting the
                # attributes and links
                self.dbmodel.save()

                if attributes:
                    self.ATTRIBUTE_CLASS.reset_values_for_node(self.dbmodel, attributes, with_transaction=False)

                if links:
                    for link_triple in links:
                        self._add_link(*link_triple)

        return self

    def _increment_version_number(self):
        """Increment the node version number of this node by one directly in the database."""
        self._dbmodel.nodeversion = self.version + 1
        self._dbmodel.save()


class DjangoNodeCollection(BackendNodeCollection):
    """The collection of Node entries."""

    ENTITY_CLASS = DjangoNode

    def delete(self, pk):
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
        try:
            models.DbNode.objects.filter(pk=pk).delete()  # pylint: disable=no-member
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("Node with pk '{}' not found".format(pk))
