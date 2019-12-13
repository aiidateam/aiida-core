# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Base SQLAlchemy models."""

from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import UnmappedClassError

import aiida.backends.sqlalchemy
from aiida.backends.sqlalchemy import get_scoped_session
from aiida.common.exceptions import InvalidOperation

# Taken from
# https://github.com/mitsuhiko/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L491


class _QueryProperty:
    """Query property."""

    def __init__(self, query_class=orm.Query):
        self.query_class = query_class

    def __get__(self, obj, _type):
        """Get property of a query."""
        try:
            mapper = orm.class_mapper(_type)
            if mapper:
                return self.query_class(mapper, session=aiida.backends.sqlalchemy.get_scoped_session())
            return None
        except UnmappedClassError:
            return None


class _SessionProperty:
    """Session Property"""

    def __get__(self, obj, _type):
        if not aiida.backends.sqlalchemy.get_scoped_session():
            raise InvalidOperation('You need to call load_dbenv before ' 'accessing the session of SQLALchemy.')
        return aiida.backends.sqlalchemy.get_scoped_session()


class _AiidaQuery(orm.Query):
    """AiiDA query."""

    def __iter__(self):
        """Iterator."""
        from aiida.orm.implementation.sqlalchemy import convert  # pylint: disable=cyclic-import

        iterator = super().__iter__()
        for result in iterator:
            # Allow the use of with_entities
            if issubclass(type(result), Model):
                yield convert.get_backend_entity(result, None)
            else:
                yield result


class Model:
    """Query model."""
    query = _QueryProperty()

    session = _SessionProperty()

    def save(self, commit=True):
        """Emulate the behavior of Django's save() method

        :param commit: whether to do a commit or just add to the session
        :return: the SQLAlchemy instance"""
        sess = get_scoped_session()
        sess.add(self)
        if commit:
            sess.commit()
        return self

    def delete(self, commit=True):
        """Emulate the behavior of Django's delete() method

        :param commit: whether to do a commit or just remover from the session"""
        sess = get_scoped_session()
        sess.delete(self)
        if commit:
            sess.commit()


Base = declarative_base(cls=Model, name='Model')  # pylint: disable=invalid-name
