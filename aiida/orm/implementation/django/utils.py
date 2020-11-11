# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for the implementation of the Django backend."""

# pylint: disable=import-error,no-name-in-module
from django.db import transaction, IntegrityError
from django.db.models.fields import FieldDoesNotExist

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
        if self.is_saved() and self._is_mutable_model_field(item):
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
        return self._model.pk is not None

    def save(self):
        """Store the model instance.

        :raises `aiida.common.IntegrityError`: if a database integrity error is raised during the save.
        """
        # transactions are needed here for Postgresql:
        # https://docs.djangoproject.com/en/1.7/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
        with transaction.atomic():
            try:
                self._model.save()
            except IntegrityError as exception:
                raise exceptions.IntegrityError(str(exception))

    def _is_mutable_model_field(self, field):
        """Return whether the field is a mutable field of the model.

        :return: boolean, True if the field is a model field and is not in the `IMMUTABLE_MODEL_FIELDS` set.
        """
        if field in IMMUTABLE_MODEL_FIELDS:
            return False

        return self._is_model_field(field)

    def _is_model_field(self, name):
        """Return whether the field is a field of the model.

        :return: boolean, True if the field is a model field, False otherwise.
        """
        try:
            self._model.__class__._meta.get_field(name)  # pylint: disable=protected-access
        except FieldDoesNotExist:
            return False
        else:
            return True

    def _flush(self, fields=None):
        """Flush the fields of the model to the database.

        .. note:: If the wrapped model is not actually saved in the database yet, this method is a no-op.

        :param fields: the model fields whose current value to flush to the database
        """
        if self.is_saved():
            try:
                # Manually append the `mtime` to fields to update, because when using the `update_fields` keyword of the
                # `save` method, the `auto_now` property of `mtime` column is not triggered. If `update_fields` is None
                # everything is updated, so we do not have to add anything
                if fields is not None and self._is_model_field('mtime'):
                    fields.add('mtime')
                self._model.save(update_fields=fields)
            except IntegrityError as exception:
                raise exceptions.IntegrityError(str(exception))

    def _ensure_model_uptodate(self, fields=None):
        """Refresh all fields of the wrapped model instance by fetching the current state of the database instance.

        :param fields: optionally refresh only these fields, if `None` all fields are refreshed.
        """
        if self.is_saved():
            self._model.refresh_from_db(fields=fields)

    @staticmethod
    def _in_transaction():
        """Return whether the current scope is within an open database transaction.

        :return: boolean, True if currently in open transaction, False otherwise.
        """
        return not transaction.get_autocommit()
