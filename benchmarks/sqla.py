# -*- coding: utf-8 -*-


from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.backends.sqlalchemy.models.group import DbGroup


def build_query_attr(filter_):
    begin_group = 'N_elements_'
    end_group = '_clean_cif_primitive_dup_filtered'

    q = DbNode.query.join(DbGroup, DbNode.dbgroups).filter(
        DbNode.attributes.has_key(filter_),
        DbGroup.name.like("{}%{}".format(begin_group, end_group))
    )

    return lambda : q.all()

INDEX_NAME = "dbnode_attributes_idx"

def delete_gin_index():
    delete = "DROP INDEX IF EXISTS {};".format(INDEX_NAME)
    sa.session.execute(delete)
    sa.session.commit()
    _vacuum_analyaze()

def create_gin_index():
    insert = "CREATE INDEX {} ON db_dbnode USING gin(attributes);".format(INDEX_NAME)
    sa.session.execute(insert)
    sa.session.commit()
    _vacuum_analyaze()

def _vacuum_analyaze():
    raw_conn = sa.session.connection().engine.raw_connection().connection
    isolation_level = raw_conn.isolation_level
    raw_conn.set_isolation_level(0)
    raw_conn.cursor().execute("VACUUM ANALYZE")
    raw_conn.set_isolation_level(isolation_level)


queries = {
    "attributes": {
        'kinds': build_query_attr('kinds'),
        'sites': build_query_attr('sites'),
        'cell:': build_query_attr('cell')
    }
}

