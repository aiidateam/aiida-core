# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import orm
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.ext.declarative import declarative_base

from aiida.backends.sqlalchemy import _GlobalSession

# Taken from
# https://github.com/mitsuhiko/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L491


class _QueryProperty(object):
    def __get__(self, obj, _type):
        try:
            mapper = orm.class_mapper(_type)
            if mapper:
                return _type.query_class(mapper, session=session)
        except UnmappedClassError:
            return None

class Model(object):

    query = _QueryProperty()
    query_class = orm.Query

    session = _GlobalSession()

    def save(self, commit=True):
        self.session.add(self)
        if commit:
            self.session.commit()

Base = declarative_base(cls=Model, name='Model')
