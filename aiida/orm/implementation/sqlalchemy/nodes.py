# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementation of the `BackendNode` and `BackendNodeCollection` classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=no-name-in-module,import-error
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models import node as models
from aiida.common import exceptions
from aiida.common.lang import type_check

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils
from .computers import SqlaComputer
from .users import SqlaUser


class SqlaNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """SQLA Node backend entity"""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = models.DbNode

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
        super(SqlaNode, self).__init__(backend)

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
            'attributes': self._dbmodel.attributes,
            'extras': self._dbmodel.extras,
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

    def get_attribute(self, key):
        """Return an attribute.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            return utils.get_attr(self._dbmodel.attributes, key)
        except (KeyError, IndexError):
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
        try:
            self.dbmodel.set_attr(key, value)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

    def set_attributes(self, attributes):
        """Set attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: the new attributes to set
        """
        try:
            self.dbmodel.set_attributes(attributes)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely reset any existing attributes and replace them with the new dictionary.

        :param attributes: the new attributes to set
        """
        try:
            self.dbmodel.reset_attributes(attributes)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            self._dbmodel.del_attr(key)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

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
            return utils.get_attr(self._dbmodel.extras, key)
        except (KeyError, IndexError):
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
        try:
            self._dbmodel.set_extra(key, value)
            if increase_version:
                self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

    def set_extras(self, extras):
        """Set extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: the new extras to set
        """
        try:
            self.dbmodel.set_extras(extras)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely reset any existing extras and replace them with the new dictionary.

        :param extras: the new extras to set
        """
        try:
            self._dbmodel.reset_extras(extras)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            self._dbmodel.del_extra(key)
            self._increment_version_number()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise

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
            raise exceptions.UniquenessError('failed to create the link: {}'.format(exception))

    def store(self, attributes=None, links=None, with_transaction=True):
        """Store the node in the database.

        :param attributes: optional attributes to set before storing, will override any existing attributes
        :param links: optional links to add before storing
        """
        session = get_scoped_session()

        session.add(self._dbmodel)

        if attributes:
            self._dbmodel.attributes = attributes

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

    def _increment_version_number(self):
        """Increment the node version number of this node by one directly in the database."""
        self._dbmodel.nodeversion = self.version + 1
        try:
            self._dbmodel.save()
        except Exception:  # pylint: disable=bare-except
            session = get_scoped_session()
            session.rollback()
            raise


class SqlaNodeCollection(BackendNodeCollection):
    """The collection of Node entries."""

    ENTITY_CLASS = SqlaNode

    def delete(self, pk):
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
        session = get_scoped_session()

        try:
            session.query(models.DbNode).filter_by(id=pk).one().delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent("Node with pk '{}' not found".format(pk))
