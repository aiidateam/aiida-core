# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import

from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import UnmappedClassError

import aiida.backends.sqlalchemy
from aiida.common.exceptions import InvalidOperation

# Taken from
# https://github.com/mitsuhiko/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L491




class _QueryProperty(object):

    def __init__(self, query_class=orm.Query):
        self.query_class = query_class

    def __get__(self, obj, _type):
        try:
            mapper = orm.class_mapper(_type)
            if mapper:
                return self.query_class(
                    mapper, session=aiida.backends.sqlalchemy.get_scoped_session())
        except UnmappedClassError:
            return None


class _SessionProperty(object):
    def __get__(self, obj, _type):
        if not aiida.backends.sqlalchemy.get_scoped_session():
            raise InvalidOperation("You need to call load_dbenv before "
                                   "accessing the session of SQLALchemy.")
        return aiida.backends.sqlalchemy.get_scoped_session()


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


from aiida.backends.sqlalchemy import get_scoped_session

class Model(object):

    query = _QueryProperty()

    session = _SessionProperty()

    def save(self, commit=True):
        sess = get_scoped_session()
        sess.add(self)
        if commit:
            sess.commit()
        return self


    def delete(self, commit=True):
        sess = get_scoped_session()
        sess.delete(self)
        if commit:
            sess.commit()

Base = declarative_base(cls=Model, name='Model')
