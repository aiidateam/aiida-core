# -*- coding: utf-8 -*-

from sqlalchemy import or_


from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.backends.sqlalchemy.models.group import DbGroup

from aiida.orm import DataFactory, CalculationFactory
from aiida.orm.implementation.general.calculation.inline import InlineCalculation


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


BEGIN_GROUP = 'N_elements_'
END_GROUP = '_clean_cif_primitive_dup_filtered'

def build_query_attr(filter_):
    q = DbNode.query.join(DbGroup, DbNode.dbgroups).filter(
        DbNode.attributes.has_key(filter_),
        DbGroup.name.like("{}%{}".format(BEGIN_GROUP, END_GROUP))
    )

    return lambda: q.all()

def build_query_attr_only(filter_):
    q = (sa.session.query(DbNode.attributes[filter_])
         .join(DbGroup, DbNode.dbgroups)
         .filter(DbGroup.name.like("{}%{}".format(BEGIN_GROUP, END_GROUP)))
         .filter(DbNode.attributes.has_key(filter_)))

    return lambda: q.all()

def complex_query():
    RemoteData = DataFactory('remote')
    PwCalculation = CalculationFactory('quantumespresso.pw')

    pws = sa.session.query(DbNode.id).filter(
        DbNode.type == PwCalculation._plugin_type_string).cte()

    scratchremotes = sa.session.query(DbNode.id).filter(
        DbNode.type == RemoteData._plugin_type_string
    ).join(pws, DbNode.inputs).cte()

    inlines = sa.session.query(DbNode.id).filter(
        DbNode.type == InlineCalculation._plugin_type_string
    ).join(scratchremotes, DbNode.inputs).cte()

    storeremotes = sa.session.query(DbNode.uuid).filter(
        DbNode.type == RemoteData._plugin_type_string
    ).join(inlines, DbNode.inputs)

    return lambda: storeremotes.all()

def list_data_structure(element=None):
    q = (sa.session.query(DbNode.id, DbNode.attributes['kinds'], DbNode.attributes['sites'])
         .filter(DbNode.type.like("data.structure.%"),
                 or_(DbNode.attributes.has_key('kinds'),
                     DbNode.attributes.has_key('sites'))
                 ).order_by(DbNode.ctime))
    if element:
        d = {"kinds": [{"symbols": [element]}]}
        q = q.filter(DbNode.attributes.contains(d))

    return lambda: q.all()


queries = {
    "attributes": {
        'kinds': build_query_attr('kinds'),
        'sites': build_query_attr('sites'),
        'cell': build_query_attr('cell'),
    },
    "attributes_only": {
        'kinds': build_query_attr_only('kinds'),
        'sites': build_query_attr_only('sites'),
        'cell': build_query_attr_only('cell'),
    },
    "complex": {
        "1": complex_query()
    },
    "verdi": {
        "list_data": list_data_structure(),
        "list_element": list_data_structure(element="C")
    }
}

