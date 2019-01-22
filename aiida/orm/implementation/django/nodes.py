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

from aiida.backends.djsite.db import models
from aiida.common.hashing import _HASH_EXTRA_KEY

from .. import BackendNode, BackendNodeCollection
from . import entities


class DjangoNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """Django Node backend entity"""

    MODEL_CLASS = models.DbNode
    ATTRIBUTE_CLASS = models.DbAttribute
    EXTRA_CLASS = models.DbExtra
    LINK_CLASS = models.DbLink

    # TODO: check how many parameters we want to expose in the init
    # and if we need to define here some defaults
    def __init__(self, backend, type, process_type, label, description):
        # pylint: disable=too-many-arguments
        super(DjangoNode, self).__init__(backend)
        self._dbmodel = models.DbNode(
            type=type,
            process_type=process_type,
            label=label,
            description=description,
        )
        self._init_backend_node()

    def _increment_version_number(self):
        """
        Increment the node version number of this node by one
        directly in the database
        """
        from django.db.models import F

        # I increment the node number using a filter
        self._dbmodel.nodeversion = F('nodeversion') + 1
        self._dbmodel.save()

        # This reload internally the node of self._dbmodel
        # Note: I have to reload the object (to have the right values in memory),
        # otherwise I only get the Django Field F object as a result!
        self._dbmodel = self.MODEL_CLASS.objects.get(pk=self._dbmodel.pk)

    def _ensure_model_uptodate(self, attribute_names=None):
        """
        Expire specific fields of the dbmodel (or, if attribute_names
        is not specified, all of them), so they will be re-fetched
        from the DB.

        :param attribute_names: by default, expire all columns.
             If you want to expire only specific columns, pass
             a list of strings with the column names.
        """
        pass

    def _get_db_attrs_items(self):
        """
        Iterator over the attributes, returning tuples (key, value),
        that actually performs the job directly on the DB.

        :return: a generator of the (key, value) pairs
        """
        all_attrs = self.ATTRIBUTE_CLASS.get_all_values_for_node(self._dbmodel)
        for attr in all_attrs:
            yield (attr, all_attrs[attr])

    def _get_db_attrs_keys(self):
        """
        Iterator over the attributes, returning the attribute keys only,
        that actually performs the job directly on the DB.

        Note: It is independent of the _get_db_attrs_items
        because it is typically faster to retrieve only the keys
        from the database, especially if the values are big.    

        :return: a generator of the keys
        """
        attrlist = self.ATTRIBUTE_CLASS.list_all_node_elements(self._dbmodel)
        for attr in attrlist:
            yield attr.key

    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        :param key: key name
        :param value: its value
        """
        self.ATTRIBUTE_CLASS.set_value_for_node(self._dbmodel, key, value)

    def _del_db_attr(self, key):
        """
        Delete an attribute directly from the DB

        :param key: The key of the attribute to delete
        """
        if not self.ATTRIBUTE_CLASS.has_key(self._dbmodel, key):
            raise AttributeError("DbAttribute {} does not exist".format(key))
        self.ATTRIBUTE_CLASS.del_value_for_node(self._dbmodel, key)

    def _get_db_attr(self, key):
        """
        Return the attribute value, directly from the DB.

        :param key: the attribute key
        :return: the attribute value
        :raise AttributeError: if the attribute does not exist.
        """
        return self.ATTRIBUTE_CLASS.get_value_for_node(dbnode=self._dbmodel, key=key)

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
        return self._dbmodel.process_type

    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """
        return self._dbmodel.nodeversion

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        return self._dbmodel.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        return self._dbmodel.mtime

    @property
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        return self._dbmodel.type

    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """
        from aiida import orm

        if self._dbmodel.dbcomputer is None:
            return None

        return orm.Computer.from_backend_entity(self._backend.computers.from_dbmodel(self._dbmodel.dbcomputer))

    def _set_db_computer(self, computer):
        """
        Set the computer directly inside the dbnode member, in the DB.

        DO NOT USE DIRECTLY.

        :param computer: the computer object
        """
        type_check(computer, computers.DjangoComputer)
        self._dbmodel.dbcomputer = computer.dbmodel

    def get_user(self):
        """
        Get the user.

        :return: a User model object
        :rtype: :class:`aiida.orm.User`
        """
        from aiida import orm

        return orm.User.from_backend_entity(self._backend.users.from_dbmodel(self._dbmodel.user))

    def set_user(self, user):
        """
        Set the user

        :param user: The new user
        """
        type_check(user, user.User)
        assert user.backend == self.backend, "Passed user from different backend"
        self._dbmodel.user = user.backend_entity.dbmodel

    def _get_db_label_field(self):
        """
        Get the label field acting directly on the DB

        :return: a string.
        """
        return self._dbmodel.label

    def _update_db_label_field(self, field_value):
        """
        Set the label field acting directly on the DB

        :param field_value: the new value of the label field
        """
        self._dbmodel.label = field_value
        if self.is_stored:
            with transaction.atomic():
                self._dbmodel.save()
                self._increment_version_number()

    def _get_db_description_field(self):
        """
        Get the description of this node, acting directly at the DB level
        """
        return self._dbmodel.description

    def _update_db_description_field(self, field_value):
        """
        Update the description of this node, acting directly at the DB level

        :param field_value: the new value of the description field
        """
        self._dbmodel.description = field_value
        if self.is_stored:
            with transaction.atomic():
                self._dbmodel.save()
                self._increment_version_number()

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
        self.EXTRA_CLASS.set_value_for_node(self._dbmodel, key, value, stop_if_existing=exclusive)

    def _reset_db_extras(self, new_extras):
        """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        raise NotImplementedError("Reset of extras has not been implemented" "for Django backend.")

    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """
        return self.EXTRA_CLASS.get_value_for_node(dbnode=self._dbmodel, key=key)

    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        if not self.EXTRA_CLASS.has_key(self._dbmodel, key):
            raise AttributeError("DbExtra {} does not exist".format(key))
        return self.EXTRA_CLASS.del_value_for_node(self._dbmodel, key)

    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        extraslist = self.EXTRA_CLASS.list_all_node_elements(self._dbmodel)
        for e in extraslist:
            yield (e.key, e.getvalue())

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

        if not isinstance(src, Node):
            raise ValueError("src must be a Node instance")
        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        if not src.is_stored:
            raise ModificationNotAllowed("Cannot call the internal _add_dblink_from if the "
                                         "source node is not stored")

        if not self.is_stored:
            raise ModificationNotAllowed("Cannot call the internal _add_dblink_from if the "
                                         "destination node is not stored")

        if link_type is LinkType.CREATE or link_type is LinkType.INPUT_CALC or link_type is LinkType.INPUT_WORK:
            # Check for cycles. This works if the transitive closure is enabled; if it
            # isn't, this test will never fail, but then having a circular link is not
            # meaningful but does not pose a huge threat
            #
            # I am linking src->self; a loop would be created if a DbPath exists already
            # in the TC table from self to src
            if QueryBuilder().append(
                    Node, filters={
                        'id': self.pk
                    }, tag='parent').append(
                        Node, filters={
                            'id': src.pk
                        }, tag='child', with_ancestors='parent').count() > 0:
                raise ValueError("The link you are attempting to create would generate a loop")

        self._do_create_link(src, label, link_type)

    def _do_create_link(self, src, label, link_type):
        """
        Create a link from a source node with label and a link type

        :param src: The source node
        :type src: :class:`~aiida.orm.implementation.sqlalchemy.node.Node`
        :param label: The link label
        :param link_type: The link type
        """
        sid = None
        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            sid = transaction.savepoint()
            self.LINK_CLASS.objects.create(input=src._dbnode, output=self._dbnode, label=label, type=link_type.value)
            transaction.savepoint_commit(sid)
        except IntegrityError as exc:
            transaction.savepoint_rollback(sid)
            raise UniquenessError("There is already a link with the same " "name (raw message was {})" "".format(exc))

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
        # TODO: This needs to be generalized, allowing for flexible methods
        # for storing data and its attributes.
        from django.db import transaction
        from aiida.common.lang import EmptyContextManager
        from aiida.backends.djsite.db.models import DbAttribute

        if with_transaction:
            context_man = transaction.atomic()
        else:
            context_man = EmptyContextManager()

        # I save the corresponding django entry
        # I set the folder
        # NOTE: I first store the files, then only if this is successful,
        # I store the DB entry. In this way,
        # I assume that if a node exists in the DB, its folder is in place.
        # On the other hand, periodically the user might need to run some
        # bookkeeping utility to check for lone folders.
        self._repository_folder.replace_with_folder(self._get_temp_folder().abspath, move=True, overwrite=True)

        # I do the transaction only during storage on DB to avoid timeout
        # problems, especially with SQLite
        try:
            with context_man:
                # Save the row
                self._dbmodel.save()
                # Save its attributes 'manually' without incrementing
                # the version for each add.
                self.ATTRIBUTE_CLASS.reset_values_for_node(
                    self._dbmodel, attributes=self._attrs_cache, with_transaction=False)
                # This should not be used anymore: I delete it to
                # possibly free memory
                ## TODO: this should not be done probably, in case
                ## of a failed transaction!
                del self._attrs_cache

                self._temp_folder = None
                self._to_be_stored = False

                # Here, I store those links that were in the cache and
                # that are between stored nodes.
                self._store_cached_input_links()

        # This is one of the few cases where it is ok to do a 'global'
        # except, also because I am re-raising the exception
        except:
            # I put back the files in the sandbox folder since the
            # transaction did not succeed
            self._get_temp_folder().replace_with_folder(self._repository_folder.abspath, move=True, overwrite=True)

            ## TODO: check if this is the right thing to do, not only
            ## when .store() fails (e.g. for we are setting self._temp_folder
            ## to None) but also when multiple nodes are stored in the same
            ## transaction and only one fails
            raise

        # I store the hash without cleaning and without incrementing the nodeversion number
        self.EXTRA_CLASS.set_value_for_node(self._dbmodel, _HASH_EXTRA_KEY, self.get_hash())

        return self

    # region Deprecated

    def _get_db_input_links(self, link_type):
        from aiida.orm.convert import get_orm_entity
        from aiida.backends.djsite.db.models import DbLink

        link_filter = {'output': self._dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return [(i.label, get_orm_entity(i.input)) for i in DbLink.objects.filter(**link_filter).distinct()]

    def _get_db_output_links(self, link_type):
        from aiida.orm.convert import get_orm_entity
        from aiida.backends.djsite.db.models import DbLink

        link_filter = {'input': self._dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return ((i.label, get_orm_entity(i.output)) for i in DbLink.objects.filter(**link_filter).distinct())

    # endregion


class DjangoNodeCollection(BackendNodeCollection):
    """The Django collection for nodes"""

    ENTITY_CLASS = DjangoNode
