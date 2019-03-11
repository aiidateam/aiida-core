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
import contextlib

import six
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.types import Integer, Boolean
import sqlalchemy.exc

from aiida.common import exceptions
from aiida.backends.sqlalchemy import get_scoped_session

__all__ = ('django_filter', 'get_attr')


class ModelWrapper(object):
    """
    This wraps a SQLA model delegating all get/set attributes to the
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
        # Python 3's implementation of copy.copy does not call __init__ on the new object
        # but manually restores attributes instead. Make sure we never get into a recursive
        # loop by protecting the only special variable here: _model
        if item == '_model':
            raise AttributeError()

        if self.is_saved() and not self._in_transaction() and self._is_model_field(item):
            self._ensure_model_uptodate(fields=(item,))

        return getattr(self._model, item)

    def __setattr__(self, key, value):
        setattr(self._model, key, value)
        if self.is_saved() and self._is_model_field(key):
            fields = set((key,) + self._auto_flush)
            self._flush(fields=fields)

    def is_saved(self):
        return self._model.id is not None

    def save(self):
        """Store the model (possibly updating values if changed)."""
        try:
            commit = not self._in_transaction()
            self._model.save(commit=commit)
        except sqlalchemy.exc.IntegrityError as e:
            self._model.session.rollback()
            raise exceptions.IntegrityError(str(e))

    def _is_model_field(self, name):
        return inspect(self._model.__class__).has_property(name)

    def _flush(self, fields=()):
        """If the model is stored then save the current value."""
        if self.is_saved():
            for field in fields:
                flag_modified(self._model, field)

            self.save()

    def _ensure_model_uptodate(self, fields=None):
        if self.is_saved():
            self._model.session.expire(self._model, attribute_names=fields)

    @staticmethod
    def _in_transaction():
        return get_scoped_session().transaction.nested


@contextlib.contextmanager
def disable_expire_on_commit(session):
    """
    Context manager that disables expire_on_commit and restores the original value on exit

    :param session: The SQLA session
    :type session: :class:`sqlalchemy.orm.session.Session`
    """
    current_value = session.expire_on_commit
    session.expire_on_commit = False
    try:
        yield session
    finally:
        session.expire_on_commit = current_value


def iter_dict(attrs):
    if isinstance(attrs, dict):
        for key in sorted(attrs.keys()):
            it = iter_dict(attrs[key])
            for k, v in it:
                new_key = key
                if k:
                    new_key += "." + str(k)
                yield new_key, v
    elif isinstance(attrs, list):
        for i, val in enumerate(attrs):
            it = iter_dict(val)
            for k, v in it:
                new_key = str(i)
                if k:
                    new_key += "." + str(k)
                yield new_key, v
    else:
        yield "", attrs


def get_attr(attrs, key):
    path = key.split('.')

    d = attrs
    for p in path:
        if p.isdigit():
            p = int(p)
        # Let it raise the appropriate exception
        d = d[p]

    return d


def _create_op_func(op):
    def f(attr, val):
        return getattr(attr, op)(val)

    return f


_from_op = {
    'in': _create_op_func('in_'),
    'gte': _create_op_func('__ge__'),
    'gt': _create_op_func('__gt__'),
    'lte': _create_op_func('__le__'),
    'lt': _create_op_func('__lt__'),
    'eq': _create_op_func('__eq__'),
    'startswith': lambda attr, val: attr.like('{}%'.format(val)),
    'contains': lambda attr, val: attr.like('%{}%'.format(val)),
    'endswith': lambda attr, val: attr.like('%{}'.format(val)),
    'istartswith': lambda attr, val: attr.ilike('{}%'.format(val)),
    'icontains': lambda attr, val: attr.ilike('%{}%'.format(val)),
    'iendswith': lambda attr, val: attr.ilike('%{}'.format(val))
}


def django_filter(cls_query, **kwargs):
    # Pass the query object you want to use.
    # This also assume a AND between each arguments

    cls = inspect(cls_query)._entity_zero().class_
    q = cls_query

    # We regroup all the filter on a relationship at the same place, so that
    # when a join is done, we can filter it, and then reset to the original
    # query.
    current_join = None

    tmp_attr = dict(key=None, val=None)
    tmp_extra = dict(key=None, val=None)

    for key in sorted(kwargs.keys()):
        val = kwargs[key]

        join, field, op = [None] * 3

        splits = key.split("__")
        if len(splits) > 3:
            raise ValueError("Too many parameters to handle.")
        # something like "computer__id__in"
        elif len(splits) == 3:
            join, field, op = splits
        # we have either "computer__id", which means join + field quality or
        # "id__gte" which means field + op
        elif len(splits) == 2:
            if splits[1] in _from_op.keys():
                field, op = splits
            else:
                join, field = splits
        else:
            field = splits[0]

        if "dbattributes" == join:
            if "val" in field:
                field = "val"
            if field in ["key", "val"]:
                tmp_attr[field] = val
            continue
        elif "dbextras" == join:
            if "val" in field:
                field = "val"
            if field in ["key", "val"]:
                tmp_extra[field] = val
            continue

        current_cls = cls
        if join:
            if current_join != join:
                q = q.join(join, aliased=True)
                current_join = join

            current_cls = [r for r in inspect(cls).relationships.items() if r[0] == join][0][1].argument
            if isinstance(current_cls, Mapper):
                current_cls = current_cls.class_
            else:
                current_cls = current_cls()

        else:
            if current_join is not None:
                # Filter on the queried class again
                q = q.reset_joinpoint()
                current_join = None

        if field == "pk":
            field = "id"

        filtered_field = getattr(current_cls, field)
        if not op:
            op = "eq"
        f = _from_op[op]

        q = q.filter(f(filtered_field, val))

    # We reset one last time
    q.reset_joinpoint()

    key = tmp_attr["key"]
    if key:
        val = tmp_attr["val"]
        if val:
            q = q.filter(apply_json_cast(cls.attributes[key], val) == val)
        else:
            q = q.filter(tmp_attr["key"] in cls.attributes)
    key = tmp_extra["key"]
    if key:
        val = tmp_extra["val"]
        if val:
            q = q.filter(apply_json_cast(cls.extras[key], val) == val)
        else:
            q = q.filter(tmp_extra["key"] in cls.extras)

    return q


def apply_json_cast(attr, val):
    if isinstance(val, six.string_types):
        attr = attr.astext
    if isinstance(val, six.integer_types):
        attr = attr.astext.cast(Integer)
    if isinstance(val, bool):
        attr = attr.astext.cast(Boolean)

    return attr
