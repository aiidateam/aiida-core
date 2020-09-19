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
from aiida.orm.implementation.utils import clean_value

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
