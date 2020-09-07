# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementation of the `BackendNode` and `BackendNodeCollection` classes."""

# pylint: disable=no-name-in-module,import-error
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models import node as models
from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm.utils.node import clean_value

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils as sqla_utils
from .computers import SqlaComputer
from .users import SqlaUser


class SqlaNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """SQLA Node backend entity"""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = models.DbNode

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
            'node_type': node_type,
            'process_type': process_type,
            'user': user.dbmodel,
            'label': label,
            'description': description,
        }

        type_check(user, SqlaUser)

        if computer:
            type_check(computer, SqlaComputer, 'computer is of type {}'.format(type(computer)))
            arguments['dbcomputer'] = computer.dbmodel

        if ctime:
            type_check(ctime, datetime, 'the given ctime is of type {}'.format(type(ctime)))
            arguments['ctime'] = ctime

        if mtime:
            type_check(mtime, datetime, 'the given mtime is of type {}'.format(type(mtime)))
            arguments['mtime'] = mtime

        self._dbmodel = sqla_utils.ModelWrapper(models.DbNode(**arguments))

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
            'attributes': self._dbmodel.attributes,
            'extras': self._dbmodel.extras,
        }

        clone = self.__class__.__new__(self.__class__)  # pylint: disable=no-value-for-parameter
        clone.__init__(self.backend, self.node_type, self.user)
        clone._dbmodel = sqla_utils.ModelWrapper(models.DbNode(**arguments))  # pylint: disable=protected-access
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
        type_check(computer, SqlaComputer, allow_none=True)

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
        type_check(user, SqlaUser)
        self._dbmodel.user = user.dbmodel

    @property
    def attributes(self):
        """Return the complete attributes dictionary.

        .. warning:: While the node is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :return: the attributes as a dictionary
        """
        return self._dbmodel.attributes

    def get_attribute(self, key):
        """Return the value of an attribute.

        .. warning:: While the node is unstored, this will return a reference of the attribute on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            attribute will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            return self._dbmodel.attributes[key]
        except KeyError as exception:
            raise AttributeError('attribute `{}` does not exist'.format(exception)) from exception

    def get_attribute_many(self, keys):
        """Return the values of multiple attributes.

        .. warning:: While the node is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :param keys: a list of attribute names
        :return: a list of attribute values
        :raises AttributeError: if at least one attribute does not exist
        """
        try:
            return [self.get_attribute(key) for key in keys]
        except KeyError as exception:
            raise AttributeError('attribute `{}` does not exist'.format(exception)) from exception

    def set_attribute(self, key, value):
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        """
        if self.is_stored:
            value = clean_value(value)

        self._dbmodel.attributes[key] = value
        self._flush_if_stored({'attributes'})

    def set_attribute_many(self, attributes):
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """
        if self.is_stored:
            attributes = {key: clean_value(value) for key, value in attributes.items()}

        for key, value in attributes.items():
            # We need to use `self.dbmodel` without the underscore, because otherwise the second iteration will refetch
            # what is in the database and we lose the initial changes.
            self.dbmodel.attributes[key] = value
        self._flush_if_stored({'attributes'})

    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """
        if self.is_stored:
            attributes = clean_value(attributes)

        self.dbmodel.attributes = attributes
        self._flush_if_stored({'attributes'})

    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            self._dbmodel.attributes.pop(key)
        except KeyError as exception:
            raise AttributeError('attribute `{}` does not exist'.format(exception)) from exception
        else:
            self._flush_if_stored({'attributes'})

    def delete_attribute_many(self, keys):
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        """
        non_existing_keys = [key for key in keys if key not in self._dbmodel.attributes]

        if non_existing_keys:
            raise AttributeError('attributes `{}` do not exist'.format(', '.join(non_existing_keys)))

        for key in keys:
            self.dbmodel.attributes.pop(key)

        self._flush_if_stored({'attributes'})

    def clear_attributes(self):
        """Delete all attributes."""
        self._dbmodel.attributes = {}
        self._flush_if_stored({'attributes'})

    def attributes_items(self):
        """Return an iterator over the attributes.

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

    @property
    def extras(self):
        """Return the complete extras dictionary.

        .. warning:: While the node is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            extras will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :return: the extras as a dictionary
        """
        return self._dbmodel.extras

    def get_extra(self, key):
        """Return the value of an extra.

        .. warning:: While the node is unstored, this will return a reference of the extra on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            extra will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods.

        :param key: name of the extra
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            return self._dbmodel.extras[key]
        except KeyError as exception:
            raise AttributeError('extra `{}` does not exist'.format(exception)) from exception

    def get_extra_many(self, keys):
        """Return the values of multiple extras.

        .. warning:: While the node is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            extras will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :param keys: a list of extra names
        :return: a list of extra values
        :raises AttributeError: if at least one extra does not exist
        """
        return [self.get_extra(key) for key in keys]

    def set_extra(self, key, value):
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        """
        if self.is_stored:
            value = clean_value(value)

        self._dbmodel.extras[key] = value
        self._flush_if_stored({'extras'})

    def set_extra_many(self, extras):
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        """
        if self.is_stored:
            extras = {key: clean_value(value) for key, value in extras.items()}

        for key, value in extras.items():
            self.dbmodel.extras[key] = value

        self._flush_if_stored({'extras'})

    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        """
        if self.is_stored:
            extras = clean_value(extras)

        self.dbmodel.extras = extras
        self._flush_if_stored({'extras'})

    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            self._dbmodel.extras.pop(key)
        except KeyError as exception:
            raise AttributeError('extra `{}` does not exist'.format(exception)) from exception
        else:
            self._flush_if_stored({'extras'})

    def delete_extra_many(self, keys):
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """
        non_existing_keys = [key for key in keys if key not in self._dbmodel.extras]

        if non_existing_keys:
            raise AttributeError('extras `{}` do not exist'.format(', '.join(non_existing_keys)))

        for key in keys:
            self.dbmodel.extras.pop(key)

        self._flush_if_stored({'extras'})

    def clear_extras(self):
        """Delete all extras."""
        self._dbmodel.extras = {}
        self._flush_if_stored({'extras'})

    def extras_items(self):
        """Return an iterator over the extras.

        :return: an iterator with extra key value pairs
        """
        for key, value in self._dbmodel.extras.items():
            yield key, value

    def extras_keys(self):
        """Return an iterator over the extra keys.

        :return: an iterator with extra keys
        """
        for key in self._dbmodel.extras.keys():
            yield key

    def _flush_if_stored(self, fields):
        if self._dbmodel.is_saved():
            self._dbmodel._flush(fields)  # pylint: disable=protected-access

    def add_incoming(self, source, link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :return: True if the proposed link is allowed, False otherwise
        :raise aiida.common.ModificationNotAllowed: if either source or target node is not stored
        """
        session = get_scoped_session()

        type_check(source, SqlaNode)

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('node has to be stored when adding an incoming link')

        if not source.is_stored:
            raise exceptions.ModificationNotAllowed('source node has to be stored when adding a link from it')

        self._add_link(source, link_type, link_label)
        session.commit()

    def _add_link(self, source, link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        """
        from aiida.backends.sqlalchemy.models.node import DbLink

        session = get_scoped_session()

        try:
            with session.begin_nested():
                link = DbLink(input_id=source.id, output_id=self.id, label=link_label, type=link_type.value)
                session.add(link)
        except SQLAlchemyError as exception:
            raise exceptions.UniquenessError('failed to create the link: {}'.format(exception)) from exception

    def clean_values(self):
        self._dbmodel.attributes = clean_value(self._dbmodel.attributes)
        self._dbmodel.extras = clean_value(self._dbmodel.extras)

    def store(self, links=None, with_transaction=True, clean=True):  # pylint: disable=arguments-differ
        """Store the node in the database.

        :param links: optional links to add before storing
        :param with_transaction: if False, do not use a transaction because the caller will already have opened one.
        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """
        session = get_scoped_session()

        if clean:
            self.clean_values()

        session.add(self._dbmodel)

        if links:
            for link_triple in links:
                self._add_link(*link_triple)

        if with_transaction:
            try:
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise

        return self


class SqlaNodeCollection(BackendNodeCollection):
    """The collection of Node entries."""

    ENTITY_CLASS = SqlaNode

    def get(self, pk):
        """Return a Node entry from the collection with the given id

        :param pk: id of the node
        """
        session = get_scoped_session()

        try:
            return self.ENTITY_CLASS.from_dbmodel(session.query(models.DbNode).filter_by(id=pk).one(), self.backend)
        except NoResultFound:
            raise exceptions.NotExistent("Node with pk '{}' not found".format(pk)) from NoResultFound

    def delete(self, pk):
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
        session = get_scoped_session()

        try:
            session.query(models.DbNode).filter_by(id=pk).one().delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent("Node with pk '{}' not found".format(pk)) from NoResultFound
