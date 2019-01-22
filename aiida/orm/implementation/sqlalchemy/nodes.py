# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from sqlalchemy.exc import SQLAlchemyError

from aiida.backends.sqlalchemy.models import node as models
from aiida.backends.sqlalchemy.models import link as link_models
from aiida.backends.sqlalchemy import get_scoped_session
from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.common.hashing import _HASH_EXTRA_KEY

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils


class SqlaNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """SQLA Node backend entity"""

    MODEL_CLASS = models.DbNode
    LINK_CLASS = link_models.DbLink

    # TODO: check how many parameters we want to expose in the init
    # and if we need to define here some defaults
    def __init__(self, backend, type, process_type, label, description):
        super(SqlaNode, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(
            models.DbNode(
                type=type,
                process_type=process_type,
                label=label,
                description=description,
            ))
        self._init_backend_node()

    def _increment_version_number(self):
        """
        Increment the node version number of this node by one
        directly in the database
        """
        self._dbmodel.nodeversion = self.nodeversion + 1
        try:
            self._dbmodel.save()
        except:
            session = get_scoped_session()
            session.rollback()
            raise

    def _ensure_model_uptodate(self, attribute_names=None):
        """
        Expire specific fields of the dbmodel (or, if attribute_names
        is not specified, all of them), so they will be re-fetched
        from the DB.

        :param attribute_names: by default, expire all columns.
             If you want to expire only specific columns, pass
             a list of strings with the column names.
        """
        if self.is_stored:
            self._dbmodel.session.expire(self._dbmodel, attribute_names=attribute_names)

    def _attributes(self):
        """
        Return the attributes, ensuring first that the model
        is up to date.
        """
        self._ensure_model_uptodate(['attributes'])
        return self._dbmodel.attributes

    def _extras(self):
        """
        Return the extras, ensuring first that the model
        is up to date.
        """
        self._ensure_model_uptodate(['extras'])
        return self._dbmodel.extras

    def _get_db_attrs_items(self):
        """
        Iterator over the attributes, returning tuples (key, value),
        that actually performs the job directly on the DB.

        :return: a generator of the (key, value) pairs
        """
        for key, val in self._attributes().items():
            yield (key, val)

    def _get_db_attrs_keys(self):
        """
        Iterator over the attributes, returning the attribute keys only,
        that actually performs the job directly on the DB.

        Note: It is independent of the _get_db_attrs_items
        because it is typically faster to retrieve only the keys
        from the database, especially if the values are big.

        :return: a generator of the keys
        """
        for key in self._attributes().keys():
            yield key

    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        :param key: key name
        :param value: its value
        """
        try:
            self._dbmodel.set_attr(key, value)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _del_db_attr(self, key):
        """
        Delete an attribute directly from the DB

        :param key: The key of the attribute to delete
        """
        try:
            self._dbmodel.del_attr(key)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_attr(self, key):
        """
        Return the attribute value, directly from the DB.

        :param key: the attribute key
        :return: the attribute value
        :raise AttributeError: if the attribute does not exist.
        """
        try:
            return utils.get_attr(self._attributes(), key)
        except (KeyError, IndexError):
            raise AttributeError("Attribute '{}' does not exist".format(key))

    @property
    def uuid(self):
        """
        Get the UUID of the log entry
        """
        return six.text_type(self._dbmodel.uuid)

    def process_type(self):
        """
        The node process_type

        :return: the process type
        """

    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """
        self._ensure_model_uptodate(attribute_names=['nodeversion'])
        return self._dbmodel.nodeversion

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['ctime'])
        return self._dbmodel.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['mtime'])
        return self._dbmodel.mtime

    @property
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        # Type is immutable so no need to ensure the model is up to date
        return self._dbmodel.type

    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """
        from aiida import orm

        self._ensure_model_uptodate(attribute_names=['dbcomputer'])
        if self._dbmodel.dbcomputer is None:
            return None

        return orm.Computer.from_backend_entity(self.backend.computers.from_dbmodel(self._dbmodel.dbcomputer))

    def _set_db_computer(self, computer):
        """
        Set the computer directly inside the dbnode member, in the DB.

        DO NOT USE DIRECTLY.

        :param computer: the computer object
        """
        type_check(computer, computers.SqlaComputer)
        self._dbmodel.dbcomputer = computer.dbmodel

    def get_user(self):
        """
        Get the user.

        :return: an aiida user model object
        """
        from aiida import orm

        self._ensure_model_uptodate(attribute_names=['user'])
        backend_user = self._backend.users.from_dbmodel(self._dbmodel.user)
        return orm.User.from_backend_entity(backend_user)

    def set_user(self, user):
        """
        Set the user

        :param user: The new user
        """
        from aiida import orm

        type_check(user, orm.User)
        backend_user = user.backend_entity
        self._dbmodel.user = backend_user.dbmodel

    def _get_db_label_field(self):
        """
        Get the label field acting directly on the DB

        :return: a string.
        """
        self._ensure_model_uptodate(attribute_names=['label'])
        return self._dbmodel.label

    def _update_db_label_field(self, field_value):
        """
        Set the label field acting directly on the DB

        :param field_value: the new value of the label field
        """
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        self._dbmodel.label = field_value
        if self.is_stored:
            session.add(self._dbmodel)
            self._increment_version_number_db()

    def _get_db_description_field(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """
        self._ensure_model_uptodate(attribute_names=['description'])
        return self._dbmodel.description

    def _update_db_description_field(self, field_value):
        """
        Update the description of this node, acting directly at the DB level

        :param field_value: the new value of the description field
        """
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        self._dbmodel.description = field_value
        if self.is_stored:
            session.add(self._dbmodel)
            self._increment_version_number_db()


    def _set_db_extra(self, key, value, exclusive=False):
        """
        Store extra directly in the DB, without checks.

        DO NOT USE DIRECTLY.

        :param key: key name
        :param value: key value
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).
        """
        if exclusive:
            raise NotImplementedError("exclusive=True not implemented yet in SQLAlchemy backend")

        try:
            self._dbmodel.set_extra(key, value)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _reset_db_extras(self, new_extras):
        """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        try:
            self._dbmodel.reset_extras(new_extras)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """
        try:
            return utils.get_attr(self._extras(), key)
        except (KeyError, AttributeError):
            raise AttributeError("DbExtra {} does not exist".format(key))

    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        try:
            self._dbmodel.del_extra(key)
        except:
            session = get_scoped_session()
            session.rollback()
            raise

    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        extras = self._extras()
        if extras is None:
            return iter(dict().items())

        return iter(extras.items())

    def _add_db_link_from(self, src, link_type, label):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)

        :note: this function should not be called directly; it acts directly on
            the database.

        :param src: the source object
        :param str label: the name of the label to set the link from src.
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.nodes import Node

        session = get_scoped_session()
        utils.type_check(src, Node)
        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed("Cannot call the internal _add_dblink_from if the "
                                                    "destination node is not stored")
        if not src.is_stored:
            raise exceptions.ModificationNotAllowed("Cannot call the internal _add_dblink_from if the "
                                                    "source node is not stored")

        # Check for cycles. This works if the transitive closure is enabled; if
        # it isn't, this test will never fail, but then having a circular link
        # is not meaningful but does not pose a huge threat
        #
        # I am linking src->self; a loop would be created if a DbPath exists
        # already in the TC table from self to src
        if link_type is LinkType.CREATE or link_type is LinkType.INPUT_CALC or link_type is LinkType.INPUT_WORK:
            if QueryBuilder().append(
                    Node, filters={
                        'id': self.pk
                    }, tag='parent').append(
                        Node, filters={
                            'id': src.pk
                        }, tag='child', with_ancestors='parent').count() > 0:
                raise ValueError("The link you are attempting to create would generate a loop")

        self._do_create_link(src, label, link_type)
        session.commit()

    def _do_create_link(self, src, label, link_type):
        """
        Create a link from a source node with label and a link type

        :param src: The source node
        :type src: :class:`~aiida.orm.implementation.sqlalchemy.node.Node`
        :param label: The link label
        :param link_type: The link type
        """
        session = get_scoped_session()
        try:
            with session.begin_nested():
                link = self.LINK_CLASS(input_id=src.id, output_id=self.id, label=label, type=link_type.value)
                session.add(link)
        except SQLAlchemyError as exc:
            raise exceptions.UniquenessError(
                "There is already a link with the same name (raw message was {})".format(exc))

    def _db_store(self, with_transaction=True):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        # TODO: unify as much as possible the logic.
        ## This probably should only be a "DBSTORE", not dealing
        ## with how the repository is stored. See also notes
        ## in the django case.

        # I save the corresponding model entry
        # I set the folder
        # NOTE: I first store the files, then only if this is successful,
        # I store the DB entry. In this way,
        # I assume that if a node exists in the DB, its folder is in place.
        # On the other hand, periodically the user might need to run some
        # bookkeeping utility to check for lone folders.
        self._repository_folder.replace_with_folder(self._get_temp_folder().abspath, move=True, overwrite=True)

        try:
            session.add(self._dbmodel)
            # Save its attributes 'manually' without incrementing
            # the version for each add.
            self._dbmodels.attributes = self._attrs_cache
            flag_modified(self._dbnode, "attributes")
            # This should not be used anymore: I delete it to
            # possibly free memory
            del self._attrs_cache

            self._temp_folder = None
            self._to_be_stored = False

            # Here, I store those links that were in the cache and
            # that are between stored nodes.
            self._store_cached_input_links(with_transaction=False)

            if with_transaction:
                try:
                    # aiida.backends.sqlalchemy.get_scoped_session().commit()
                    session.commit()
                except SQLAlchemyError:
                    # print "Cannot store the node. Original exception: {" \
                    #      "}".format(e)
                    session.rollback()
                    raise

        # This is one of the few cases where it is ok to do a 'global'
        # except, also because I am re-raising the exception
        except:
            # I put back the files in the sandbox folder since the
            # transaction did not succeed
            self._get_temp_folder().replace_with_folder(self._repository_folder.abspath, move=True, overwrite=True)
            raise

        self._dbmodel.set_extra(_HASH_EXTRA_KEY, self.get_hash())
        return self

    # region Deprecated
    def _get_db_input_links(self, link_type):
        from aiida.orm.convert import get_orm_entity

        link_filter = {'output': self._dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return [
            (i.label, get_orm_entity(i.input)) for i in self.LINK_CLASS.query.filter_by(**link_filter).distinct().all()
        ]

    def _get_db_output_links(self, link_type):
        from aiida.orm.convert import get_orm_entity

        link_filter = {'input': self._dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return ((i.label, get_orm_entity(i.output))
                for i in self.LINK_CLASS.query.filter_by(**link_filter).distinct().all())

    # endregion


class SqlaNodeCollection(BackendNodeCollection):
    """The SQLA collection for nodes"""

    ENTITY_CLASS = SqlaNode
