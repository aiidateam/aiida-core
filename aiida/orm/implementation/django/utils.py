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

from django.db import transaction, IntegrityError
from django.db.models.fields import FieldDoesNotExist

from aiida.common import exceptions


class ModelWrapper(object):
    """
    This wraps a Django model delegating all get/set attributes to the
    underlying model class, BUT it will make sure that if the model is
    stored then:
    * before every read it has the latest value from the database, and,
    * after ever write the updated value is flushed to the database.
    """

    def __init__(self, model, auto_flush=()):
        """Construct the ModelWrapper.

        :param model: the database model instance to wrap
        :param auto_flush: an optional tuple of database model fields that are always to be flushed, in addition to
            the field that corresponds to the attribute being set through `__setattr__`.
        """
        super(ModelWrapper, self).__init__()
        # Have to do it this way because we overwrite __setattr__
        object.__setattr__(self, '_model', model)
        object.__setattr__(self, '_auto_flush', auto_flush)

    def __getattr__(self, item):
        if self.is_saved() and self._is_model_field(item):
            self._ensure_model_uptodate(fields=(item,))

        return getattr(self._model, item)

    def __setattr__(self, key, value):
        setattr(self._model, key, value)
        if self.is_saved() and self._is_model_field(key):
            fields = set((key,) + self._auto_flush)
            self._flush(fields=fields)

    def is_saved(self):
        return self._model.pk is not None

    def save(self):
        """ Save the model (possibly updating values if changed) """
        # transactions are needed here for Postgresql:
        # https://docs.djangoproject.com/en/1.7/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
        with transaction.atomic():
            try:
                self._model.save()
            except IntegrityError as e:
                # Convert to one of our exceptions
                raise exceptions.IntegrityError(str(e))

    def _is_model_field(self, name):
        try:
            # Check if it's a field
            self._model.__class__._meta.get_field(name)
            return True
        except FieldDoesNotExist:
            return False

    def _flush(self, fields=None):
        """ If the user is stored then save the current value """
        if self.is_saved():
            try:
                # Manually append the `mtime` to fields to update, because when using the `update_fields` keyword of the
                # `save` method, the `auto_now` property of `mtime` column is not triggered. If `update_fields` is None
                # everything is updated, so we do not have to add anything
                if fields is not None and self._is_model_field('mtime'):
                    fields.add('mtime')
                self._model.save(update_fields=fields)
            except IntegrityError as e:
                # Convert to one of our exceptions
                raise exceptions.IntegrityError(str(e))

    def _ensure_model_uptodate(self, fields=None):
        if self.is_saved():
            self._model.refresh_from_db(fields=fields)

    @staticmethod
    def _in_transaction():
        return not transaction.get_autocommit()
