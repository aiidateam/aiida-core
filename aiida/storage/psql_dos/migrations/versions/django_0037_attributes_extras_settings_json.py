# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Move `db_dbattribute`/`db_dbextra` to `db_dbnode.attributes`/`db_dbnode.extras`, and add `dbsetting.val`

Revision ID: django_0037
Revises: django_0036

"""
import math

from alembic import op
import sqlalchemy as sa
from sqlalchemy import cast, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import column, table

from aiida.cmdline.utils import echo
from aiida.common.progress_reporter import get_progress_reporter
from aiida.storage.psql_dos.migrations.utils import ReflectMigrations

revision = 'django_0037'
down_revision = 'django_0036'
branch_labels = None
depends_on = None

node_tbl = table(
    'db_dbnode',
    column('id'),
    column('attributes', postgresql.JSONB(astext_type=sa.Text())),
    column('extras', postgresql.JSONB(astext_type=sa.Text())),
)

attr_tbl = table(
    'db_dbattribute',
    column('id'),
    column('dbnode_id'),
    column('key'),
    column('datatype'),
    column('tval'),
    column('ival'),
    column('fval'),
    column('dval'),
    column('bval'),
)

extra_tbl = table(
    'db_dbextra',
    column('id'),
    column('dbnode_id'),
    column('key'),
    column('datatype'),
    column('tval'),
    column('ival'),
    column('fval'),
    column('dval'),
    column('bval'),
)

setting_tbl = table(
    'db_dbsetting',
    column('id'),
    column('description'),
    column('time'),
    column('key'),
    column('datatype'),
    column('tval'),
    column('ival'),
    column('fval'),
    column('dval'),
    column('bval'),
    column('val'),
)


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    op.add_column('db_dbnode', sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('db_dbnode', sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # transition attributes and extras to node
    node_count = conn.execute(select(func.count()).select_from(node_tbl)).scalar()
    if node_count:
        with get_progress_reporter()(total=node_count, desc='Updating attributes and extras') as progress:
            for node in conn.execute(select(node_tbl)).all():
                attr_list = conn.execute(select(attr_tbl).where(attr_tbl.c.dbnode_id == node.id)).all()
                attributes, _ = attributes_to_dict(sorted(attr_list, key=lambda a: a.key))
                extra_list = conn.execute(select(extra_tbl).where(extra_tbl.c.dbnode_id == node.id)).all()
                extras, _ = attributes_to_dict(sorted(extra_list, key=lambda a: a.key))
                conn.execute(
                    node_tbl.update().where(node_tbl.c.id == node.id).values(attributes=attributes, extras=extras)
                )
                progress.update()

    op.drop_table('db_dbattribute')
    op.drop_table('db_dbextra')

    op.add_column('db_dbsetting', sa.Column('val', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # transition settings
    setting_count = conn.execute(select(func.count()).select_from(setting_tbl)).scalar()
    if setting_count:
        with get_progress_reporter()(total=setting_count, desc='Updating settings') as progress:
            for setting in conn.execute(select(setting_tbl)).all():
                dt = setting.datatype
                val = None
                if dt == 'txt':
                    val = setting.tval
                elif dt == 'float':
                    val = setting.fval
                    if math.isnan(val) or math.isinf(val):
                        val = str(val)
                elif dt == 'int':
                    val = setting.ival
                elif dt == 'bool':
                    val = setting.bval
                elif dt == 'date':
                    if setting.dval is not None:
                        val = setting.dval.isoformat()
                    else:
                        val = setting.dval
                conn.execute(
                    setting_tbl.update().where(setting_tbl.c.id == setting.id
                                               ).values(val=cast(val, postgresql.JSONB(astext_type=sa.Text())))
                )
                progress.update()

    op.drop_column('db_dbsetting', 'tval')
    op.drop_column('db_dbsetting', 'fval')
    op.drop_column('db_dbsetting', 'ival')
    op.drop_column('db_dbsetting', 'bval')
    op.drop_column('db_dbsetting', 'dval')
    op.drop_column('db_dbsetting', 'datatype')

    ReflectMigrations(op).drop_indexes('db_dbsetting', 'key')  # db_dbsetting_key_1b84beb4
    op.create_index(
        'db_dbsetting_key_1b84beb4_like',
        'db_dbsetting',
        ['key'],
        postgresql_using='btree',
        postgresql_ops={'key': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0037.')


def attributes_to_dict(attr_list: list):
    """
    Transform the attributes of a node into a dictionary. It assumes the key
    are ordered alphabetically, and that they all belong to the same node.
    """
    # pylint: disable=too-many-branches
    d: dict = {}

    error = False
    for a in attr_list:
        try:
            tmp_d = select_from_key(a.key, d)
        except ValueError:
            echo.echo_error(f"Couldn't transfer attribute {a.id} with key {a.key} for dbnode {a.dbnode_id}")
            error = True
            continue
        key = a.key.split('.')[-1]

        if isinstance(tmp_d, (list, tuple)):
            key = int(key)

        dt = a.datatype

        if dt == 'dict':
            tmp_d[key] = {}
        elif dt == 'list':
            tmp_d[key] = [None] * a.ival
        else:
            val = None
            if dt == 'txt':
                val = a.tval
            elif dt == 'float':
                val = a.fval
                if math.isnan(val) or math.isinf(val):
                    val = str(val)
            elif dt == 'int':
                val = a.ival
            elif dt == 'bool':
                val = a.bval
            elif dt == 'date':
                if a.dval is not None:
                    val = a.dval.isoformat()
                else:
                    val = a.dval

            tmp_d[key] = val

    return d, error


def select_from_key(key, d):
    """
    Return element of the dict to do the insertion on. If it is foo.1.bar, it
    will return d["foo"][1]. If it is only foo, it will return d directly.
    """
    path = key.split('.')[:-1]

    tmp_d = d
    for p in path:
        if isinstance(tmp_d, (list, tuple)):
            tmp_d = tmp_d[int(p)]
        else:
            tmp_d = tmp_d[p]

    return tmp_d
