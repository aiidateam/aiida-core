# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import orm
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.ext.declarative import declarative_base

from aiida.backends import sqlalchemy as sa
from aiida.common.exceptions import InvalidOperation

# Taken from
# https://github.com/mitsuhiko/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L491


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

class _QueryProperty(object):

    def __init__(self, query_class=orm.Query):
        self.query_class = query_class

    def __get__(self, obj, _type):
        try:
            mapper = orm.class_mapper(_type)
            if mapper:
                return self.query_class(mapper, session=sa.session)
        except UnmappedClassError:
            return None


class _SessionProperty(object):
    def __get__(self, obj, _type):
        if not sa.session:
            raise InvalidOperation("You need to call load_dbenv before "
                                   "accessing the session of SQLALchemy.")
        return sa.session

class _AiidaQuery(orm.Query):

    def __init__(self, *args, **kwargs):
            super(_AiidaQuery, self).__init__(*args, **kwargs)

    def __iter__(self):
        iterator = super(_AiidaQuery, self).__iter__()
        for r in iterator:
            # Allow the use of with_entities
            if issubclass(type(r), Model):
                yield r.get_aiida_class()
            else:
                yield r


class Model(object):

    query = _QueryProperty()

    session = _SessionProperty()

    def save(self, commit=True):
        self.session.add(self)
        if commit:
            self.session.commit()
        return self

    def delete(self, commit=True):
        self.session.delete(self)
        if commit:
            self.session.commit()

Base = declarative_base(cls=Model, name='Model')
