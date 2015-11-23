# -*- coding: utf-8 -*-

import math

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, subqueryload, joinedload
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql.expression import func

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.utils import load_dbenv, is_dbenv_loaded


# Note that we can't use `DbAttribute.query` here because we didn't import it
# in load_dbenv.
class DbAttribute(Base):
    __tablename__ = "db_dbattribute"

    id = Column(Integer, primary_key=True)

    key = Column(String(1024), nullable=False)
    datatype = Column(String(10), nullable=False)

    tval = Column(Text, nullable=False)
    fval = Column(Float)
    ival = Column(Integer)
    bval = Column(Boolean)
    dval = Column(DateTime(timezone=True))

    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'), nullable=False)
    dbnode = relationship('DbNode', backref='old_attrs')

class DbExtra(Base):
    __tablename__ = "db_dbextra"

    id = Column(Integer, primary_key=True)

    key = Column(String(1024), nullable=False)
    datatype = Column(String(10), nullable=False)

    tval = Column(Text, nullable=False)
    fval = Column(Float)
    ival = Column(Integer)
    bval = Column(Boolean)
    dval = Column(DateTime(timezone=True))

    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'), nullable=False)
    dbnode = relationship('DbNode', backref='old_extras')


def attributes_to_dict(attr_list):
    """
    Transform the attributes of a node into a dictionnary. It assumes the key
    are ordered alphabetically, and that they all belong to the same node.
    """
    d = {}

    error = False
    for a in attr_list:
        try:
            tmp_d = select_from_key(a.key, d)
        except Exception:
            # TODO SP: handle this correctly. At least log them
            print("Couldn't transfer attribute {} with key {} for dbnode {}"
                  .format(a.id, a.key, a.dbnode_id))
            error = True
            continue
        key = a.key.split('.')[-1]

        if key.isdigit():
            key = int(key)

        dt = a.datatype

        if dt == "dict":
            tmp_d[key] = {}
        elif dt == "list":
            tmp_d[key] = [None] * a.ival
        else:
            val = None
            if dt == "txt":
                val = a.tval
            elif dt == "float":
                val = a.fval
                if math.isnan(val):
                    val = 'NaN'
            elif dt == "int":
                val = a.ival
            elif dt == "bool":
                val = a.bval
            elif dt == "date":
                val = a.dval

            if isinstance(tmp_d, list):
                tmp_d.append(val)
            else:
                tmp_d[key] = val

    return (d, error)

def select_from_key(key, d):
    """
    Return element of the dict to do the insertion on. If it is foo.1.bar, it
    will return d["foo"][1]. If it is only foo, it will return d directly.
    """
    path = key.split('.')[:-1]

    tmp_d = d
    for p in path:
        if p.isdigit():
            tmp_d = tmp_d[int(p)]
        else:
            tmp_d = tmp_d[p]

    return tmp_d


def migrate_extras(create_column=False, profile=None):
    if not is_dbenv_loaded():
        load_dbenv(profile=profile)
    from aiida.backends.sqlalchemy.models.node import DbNode

    with sa.session.begin(subtransactions=True):
        if create_column:
            sa.session.execute('ALTER TABLE db_dbnode ADD COLUMN extras JSONB DEFAULT \'{}\'')
        nodes = DbNode.query.options(subqueryload('old_extras')).all()

        error = False
        for node in nodes:
            attrs, err_ = attributes_to_dict(sorted(node.old_extras, key=lambda a: a.key))
            error |= err_

            node.extras = attrs
            sa.session.add(node)

        if error:
            cont_s = raw_input("There has been some errors during the migration. Do you want to continue ? [y/N] ")
            cont = cont_s.lower() == "y"
            if not cont:
                sa.session.rollback()
                return

    sa.session.commit()


def migrate_attributes(create_column=False, profile=None):
    if not is_dbenv_loaded():
        load_dbenv(profile=profile)
    from aiida.backends.sqlalchemy.models.node import DbNode

    with sa.session.begin(subtransactions=True):
        if create_column:
            sa.session.execute('ALTER TABLE db_dbnode ADD COLUMN attributes JSONB DEFAULT \'{}\'')
        nodes = DbNode.query.options(subqueryload('old_attrs')).all()

        error = False
        for node in nodes:
            attrs, err_ = attributes_to_dict(sorted(node.old_attrs, key=lambda a: a.key))
            error |= err_

            node.attributes = attrs
            sa.session.add(node)

        if error:
            cont_s = raw_input("There has been some errorss during the migration. Do you want to continue ? [y/N] ")
            cont = cont_s.lower() == "y"
            if not cont:
                sa.session.rollback()
                return

    sa.session.commit()

def migrate_json_column():
    """
    Migrate the TEXT column containing JSON into JSON columns
    """
    if not is_dbenv_loaded():
        load_dbenv()

    table_col = [
        ('db_dbauthinfo', 'metadata'),
        ('db_dbauthinfo', 'auth_params'),
        ('db_dbcomputer', 'metadata'),
        ('db_dblog', 'metadata')
    ]

    sql = "ALTER TABLE {table} ALTER COLUMN {column} TYPE JSONB USING {column}::JSONB"

    with sa.session.begin(subtransactions=True):

        for table, col in table_col:
            sa.session.execute(sql.format(table=table, column=col))


    sa.session.commit()
