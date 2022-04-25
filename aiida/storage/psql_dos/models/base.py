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
from sqlalchemy import MetaData, event, inspect
from sqlalchemy.orm import declarative_base


class Model:
    """Base ORM model."""

    def __repr__(self) -> str:
        """Return a representation of the row columns"""
        string = f'<{self.__class__.__name__}'
        for col in self.__table__.columns:  # type: ignore[attr-defined] # pylint: disable=no-member
            col_name = col.name
            if col_name == 'metadata':
                col_name = '_metadata'
            val = f'{getattr(self, col_name)!r}'
            if len(val) > 10:  # truncate long values
                val = val[:10] + '...'
            string += f' {col_name}={val},'
        return string + '>'


def instant_defaults_listener(target, args, kwargs):
    """Loop over the columns of the target model instance and populate defaults.

    SqlAlchemy does not set default values for table columns upon construction of a new instance,
    but will only do so when storing the instance.
    Any attributes that do not have a value but have a defined default,
    will be populated with this default.
    This does mean however, that before the instance is stored, these attributes are undefined, for example the UUID.

    This should be used as: https://docs.sqlalchemy.org/en/14/orm/events.html#sqlalchemy.orm.InstanceEvents.init
    """
    # using args would break this logic
    assert not args, f'args are not allowed in {target} instantiation'
    # If someone passes metadata in **kwargs we change it to _metadata
    if 'metadata' in kwargs:
        kwargs['_metadata'] = kwargs.pop('metadata')
    # don't allow certain JSON fields to be null
    for col in ('attributes', 'extras', '_metadata'):
        if col in kwargs and kwargs[col] is None:
            kwargs[col] = {}
    columns = inspect(target.__class__).columns
    # The only time that we allow mtime not to be non-null is when we explicitly pass it as a kwarg.
    # This covers the case that a node is constructed based on some very predefined data,
    # like when we create nodes in the AiiDA import functions
    if 'mtime' in columns and 'mtime' not in kwargs:
        kwargs['mtime'] = None
    for key, column in columns.items():
        if key in kwargs:
            continue
        if hasattr(column, 'default') and column.default is not None:
            if callable(column.default.arg):
                kwargs[key] = column.default.arg(target)
            else:
                kwargs[key] = column.default.arg


# see https://alembic.sqlalchemy.org/en/latest/naming.html
naming_convention = (
    ('pk', '%(table_name)s_pkey'),  # this is identical to the default PSQL convention
    ('ix', 'ix_%(table_name)s_%(column_0_N_label)s'),
    # note, indexes using varchar_pattern_ops should be named: 'ix_pat_%(table_name)s_%(column_0_N_label)s'
    ('uq', 'uq_%(table_name)s_%(column_0_N_name)s'),
    ('ck', 'ck_%(table_name)s_%(constraint_name)s'),
    ('fk', 'fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s'),
    # note, ideally we may also append with '_%(referred_column_0_N_name)s', but this causes ORM construction errors:
    # https://github.com/sqlalchemy/sqlalchemy/issues/5350
)

Base = declarative_base(cls=Model, name='Model', metadata=MetaData(naming_convention=dict(naming_convention)))  # pylint: disable=invalid-name
event.listen(Base, 'init', instant_defaults_listener, propagate=True)


def get_orm_metadata() -> MetaData:
    """Return the populated metadata object."""
    # we must load all models, to populate the ORM metadata
    from aiida.storage.psql_dos.models import (  # pylint: disable=unused-import
        authinfo,
        comment,
        computer,
        group,
        log,
        node,
        settings,
        user,
    )
    return Base.metadata
