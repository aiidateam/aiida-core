# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for the implementation of the SqlAlchemy backend."""

import contextlib

# pylint: disable=import-error,no-name-in-module
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.common import exceptions

IMMUTABLE_MODEL_FIELDS = {'id', 'pk', 'uuid', 'node_type'}


class ModelWrapper:
    """Wrap a database model instance to correctly update and flush the data model when getting or setting a field.

    If the model is not stored, the behavior of the get and set attributes is unaltered. However, if the model is
    stored, which is to say, it has a primary key, the `getattr` and `setattr` are modified as follows:

    * `getattr`: if the item corresponds to a mutable model field, the model instance is refreshed first
    * `setattr`: if the item corresponds to a mutable model field, changes are flushed after performing the change
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, model, auto_flush=()):
        """Construct the ModelWrapper.

        :param model: the database model instance to wrap
        :param auto_flush: an optional tuple of database model fields that are always to be flushed, in addition to
            the field that corresponds to the attribute being set through `__setattr__`.
        """
        super().__init__()
        # Have to do it this way because we overwrite __setattr__
        object.__setattr__(self, '_model', model)
        object.__setattr__(self, '_auto_flush', auto_flush)

    def __getattr__(self, item):
        """Get an attribute of the model instance.

        If the model is saved in the database, the item corresponds to a mutable model field and the current scope is
        not in an open database connection, then the field's value is first refreshed from the database.

        :param item: the name of the model field
        :return: the value of the model's attribute
        """
        # Python 3's implementation of copy.copy does not call __init__ on the new object
        # but manually restores attributes instead. Make sure we never get into a recursive
        # loop by protecting the only special variable here: _model
        if item == '_model':
            raise AttributeError()

        if self.is_saved() and self._is_mutable_model_field(item) and not self._in_transaction():
            self._ensure_model_uptodate(fields=(item,))

        return getattr(self._model, item)

    def __setattr__(self, key, value):
        """Set the attribute on the model instance.

        If the field being set is a mutable model field and the model is saved, the changes are flushed.

        :param key: the name of the model field
        :param value: the value to set
        """
        setattr(self._model, key, value)
        if self.is_saved() and self._is_mutable_model_field(key):
            fields = set((key,) + self._auto_flush)
            self._flush(fields=fields)

    def is_saved(self):
        """Retun whether the wrapped model instance is saved in the database.

        :return: boolean, True if the model is saved in the database, False otherwise
        """
        return self._model.id is not None

    def save(self):
        """Store the model instance.

        .. note:: If one is currently in a transaction, this method is a no-op.

        :raises `aiida.common.IntegrityError`: if a database integrity error is raised during the save.
        """
        try:
            commit = not self._in_transaction()
            self._model.save(commit=commit)
        except IntegrityError as exception:
            self._model.session.rollback()
            raise exceptions.IntegrityError(str(exception))

    def _is_mutable_model_field(self, field):
        """Return whether the field is a mutable field of the model.

        :return: boolean, True if the field is a model field and is not in the `IMMUTABLE_MODEL_FIELDS` set.
        """
        if field in IMMUTABLE_MODEL_FIELDS:
            return False

        return self._is_model_field(field)

    def _is_model_field(self, field):
        """Return whether the field is a field of the model.

        :return: boolean, True if the field is a model field, False otherwise.
        """
        return inspect(self._model.__class__).has_property(field)

    def _flush(self, fields=()):
        """Flush the fields of the model to the database.

        .. note:: If the wrapped model is not actually save in the database yet, this method is a no-op.

        :param fields: the model fields whose currently value to flush to the database
        """
        if self.is_saved():
            for field in fields:
                flag_modified(self._model, field)

            self.save()

    def _ensure_model_uptodate(self, fields=None):
        """Refresh all fields of the wrapped model instance by fetching the current state of the database instance.

        :param fields: optionally refresh only these fields, if `None` all fields are refreshed.
        """
        self._model.session.expire(self._model, attribute_names=fields)

    @staticmethod
    def _in_transaction():
        """Return whether the current scope is within an open database transaction.

        :return: boolean, True if currently in open transaction, False otherwise.
        """
        return get_scoped_session().transaction.nested


@contextlib.contextmanager
def disable_expire_on_commit(session):
    """Context manager that disables expire_on_commit and restores the original value on exit

    :param session: The SQLA session
    :type session: :class:`sqlalchemy.orm.session.Session`
    """
    current_value = session.expire_on_commit
    session.expire_on_commit = False
    try:
        yield session
    finally:
        session.expire_on_commit = current_value
