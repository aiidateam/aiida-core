# -*- coding: utf-8 -*-

from sqlalchemy import or_
from sqlalchemy.orm import defer


from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.node import DbNode, DbPath
from aiida.backends.sqlalchemy.models.group import DbGroup

from aiida.orm import DataFactory, CalculationFactory
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
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

_jsonb_func_sql = """
CREATE OR REPLACE FUNCTION jsonb_merge(JSONB, JSONB)
RETURNS JSONB AS $$
WITH json_union AS (
    SELECT * FROM JSONB_EACH($1)
    UNION ALL
    SELECT * FROM JSONB_EACH($2)
) SELECT JSON_OBJECT_AGG(key, value)::JSONB FROM json_union;
$$ LANGUAGE SQL;
"""

def _add_random_number():
    """
    Add a key random to each attributes, with a random value from 0 to 100.
    """
    sa.session.execute(_jsonb_func_sql)
    sa.session.commit()

    q = ("UPDATE db_dbnode SET attributes = jsonb_merge(attributes, "
         "('{\"random\": ' || random() * 100 || '}')::jsonb)")
    sa.session.execute(q)
    sa.session.commit()


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

def get_farthest_cif(with_attr=False):

    nodes = ParameterData.query().with_entities('id')
    cif_type = CifData._query_type_string

    depth = (sa.session.query(DbPath.depth)
             .filter(DbPath.child_id.in_(nodes))
             .join(DbNode, DbPath.parent)
             .filter(DbNode.type.like("%{}%".format(cif_type)))
             .order_by(DbPath.depth.desc())
             .distinct()
             [0])[0]

    q = (DbPath.query.filter(DbPath.child_id.in_(nodes))
         .join(DbNode, DbPath.parent)
         .filter(DbNode.type.like("%{}%".format(cif_type)))
         .filter(DbPath.depth == depth)
         .distinct().with_entities(DbPath.id)
         )

    res = (CifData.query(children__id__in=nodes, child_paths__id__in=q)
           .distinct().order_by(DbNode.ctime))

    if not with_attr:
           res = res.options(defer(DbNode.attributes), defer(DbNode.extras))

    return res.all()

def get_closest_struc(with_attr=False):
    nodes = ParameterData.query().with_entities('id')
    struc_type = StructureData._query_type_string

    depth = (sa.session.query(DbPath.depth)
             .filter(DbPath.child_id.in_(nodes))
             .join(DbNode, DbPath.parent)
             .filter(DbNode.type.like("%{}%".format(struc_type)))
             .order_by(DbPath.depth)
             .distinct()
             [0])[0]

    q = (DbPath.query.filter(DbPath.child_id.in_(nodes))
         .join(DbNode, DbPath.parent)
         .filter(DbNode.type.like("%{}%".format(struc_type)))
         .filter(DbPath.depth == depth)
         .distinct().with_entities(DbPath.id)
         )

    res = (StructureData.query()
           .join(DbPath, DbNode.child_paths)
           .filter(DbPath.child_id.in_(nodes))
           .filter(DbPath.id.in_(q))
           .distinct().order_by(DbNode.ctime))

    if not with_attr:
           res = res.options(defer(DbNode.attributes), defer(DbNode.extras))

    return res.all()

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
    "paths": {
        "farthest_cif": get_farthest_cif,
        "closest_struc": get_closest_struc,
    },
    "paths_with_attr": {
        "farthest_cif": lambda: get_farthest_cif(with_attr=True),
        "closest_struc": lambda: get_closest_struc(with_attr=True),
    },
    "verdi": {
        "list_data": list_data_structure(),
        "list_element": list_data_structure(element="C")
    }
}

