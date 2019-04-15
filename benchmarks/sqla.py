# -*- coding: utf-8 -*-

from functools import partial

from sqlalchemy import or_, and_, func, Float
from sqlalchemy.orm import defer, aliased


from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.node import DbNode, DbPath, DbLink
from aiida.backends.sqlalchemy.models.group import DbGroup

from aiida.orm import DataFactory, CalculationFactory, Group, JobCalculation, load_node
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.orm.implementation.general.calculation.inline import InlineCalculation


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

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

def farthest_cif_django(distinct=True):
    nodes = ParameterData.query().with_entities('id')
    cif_type = CifData._query_type_string

    depth = (sa.session.query(DbPath.depth)
             .filter(DbPath.child_id.in_(nodes))
             .join(DbNode, DbPath.parent)
             .filter(DbNode.type.like("%{}%".format(cif_type)))
             .order_by(DbPath.depth.desc()))

    if distinct:
        depth = depth.distinct()

    depth = depth[0][0]

    q = (DbPath.query.filter(DbPath.child_id.in_(nodes))
         .join(DbNode, DbPath.parent)
         .filter(DbNode.type.like("%{}%".format(cif_type)))
         .filter(DbPath.depth == depth)
         .distinct().with_entities(DbPath.id)
         )

    res = (DbNode.query.filter(DbNode.type.like("%{}%".format(cif_type)))
          .join(DbPath, DbPath.parent_id == DbNode.id)
           .filter(DbPath.child_id.in_(nodes))
           .filter(DbPath.id.in_(q))
           .options(defer(DbNode.attributes), defer(DbNode.extras))
           .distinct()
           )

    return res.all()


def get_closest_struc(with_attr=False, distinct=True):
    nodes = ParameterData.query().with_entities('id')
    struc_type = StructureData._query_type_string

    depth = (sa.session.query(DbPath.depth)
             .filter(DbPath.child_id.in_(nodes))
             .join(DbNode, DbPath.parent)
             .filter(DbNode.type.like("{}%".format(struc_type)))
             .order_by(DbPath.depth))

    if distinct:
        depth = depth.distinct()

    depth = depth[0][0]

    q = (DbPath.query.filter(DbPath.child_id.in_(nodes))
         .join(DbNode, DbPath.parent)
         .filter(DbNode.type.like("{}%".format(struc_type)))
         .filter(DbPath.depth == depth)
         )

    q = q.distinct()

    q = q.with_entities(DbPath.id)

    res = (StructureData.query()
           .join(DbPath, DbNode.child_paths)
           .filter(DbPath.child_id.in_(nodes))
           .filter(DbPath.id.in_(q))
          )

    res = res.distinct()

    res = res.order_by(DbNode.ctime)

    if not with_attr:
        res = res.options(defer(DbNode.attributes), defer(DbNode.extras))

    return res.all()

def get_closest_struc_django(distinct=True):
    nodes = ParameterData.query().with_entities('id')
    struc_type = StructureData._query_type_string

    depth = (sa.session.query(DbPath.depth)
             .filter(DbPath.child_id.in_(nodes))
             .join(DbNode, DbPath.parent)
             .filter(DbNode.type.like("{}%".format(struc_type)))
             .order_by(DbPath.depth))

    if distinct:
        depth = depth.distinct()

    depth = depth[0][0]

    q = (DbPath.query.filter(DbPath.child_id.in_(nodes))
         .join(DbNode, DbPath.parent)
         .filter(DbNode.type.like("{}%".format(struc_type)))
         .filter(DbPath.depth == depth)
         )

    q = q.distinct()

    q = q.with_entities(DbPath.id)

    res = (StructureData.query()
           .join(DbPath, DbNode.child_paths)
           .filter(DbPath.child_id.in_(nodes))
           .filter(DbPath.id.in_(q))
          )

    res = res.distinct()

    res = res.order_by(DbNode.ctime)

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

def complex_query_no_cte():
    RemoteData = DataFactory('remote')
    PwCalculation = CalculationFactory('quantumespresso.pw')

    pws = sa.session.query(DbNode.id).filter(
        DbNode.type == PwCalculation._plugin_type_string
    )

    scratchremotes = sa.session.query(DbNode.id).filter(
        DbNode.type == RemoteData._plugin_type_string
    ).join(DbNode, DbNode.inputs, aliased=True).filter(
        DbNode.id.in_(pws)
    )

    inlines = sa.session.query(DbNode.id).filter(
        DbNode.type == InlineCalculation._plugin_type_string
    ).join(DbNode, DbNode.inputs, aliased=True).filter(
        DbNode.id.in_(scratchremotes)
    )

    storeremotes = sa.session.query(DbNode.uuid).filter(
        DbNode.type == RemoteData._plugin_type_string
    ).join(DbNode, DbNode.inputs, aliased=True).filter(
        DbNode.id.in_(inlines)
    )

    return lambda: storeremotes.all()

def complex_query_django_replicate():
    RemoteData = DataFactory('remote')
    PwCalculation = CalculationFactory('quantumespresso.pw')

    pws = sa.session.query(DbNode.id).filter(
        DbNode.type == PwCalculation._plugin_type_string
    )

    scratchremotes = sa.session.query(DbNode.id).filter(
        DbNode.type == RemoteData._plugin_type_string
    ).join(DbLink, DbNode.id == DbLink.output_id).filter(
        DbLink.input_id.in_(pws)
    )

    inlines = sa.session.query(DbNode.id).filter(
        DbNode.type == InlineCalculation._plugin_type_string
    ).join(DbLink, DbNode.id == DbLink.output_id).filter(
        DbLink.input_id.in_(scratchremotes)
    )

    storeremotes = sa.session.query(DbNode.uuid).filter(
        DbNode.type == RemoteData._plugin_type_string
    ).join(DbLink, DbNode.id == DbLink.output_id).filter(
        DbLink.input_id.in_(inlines)
    )

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

def mounet1():
    pw_calc = Group.get(pk=1139193).nodes.next()
    structure = pw_calc.out.output_structure
    qstruc = StructureData.query(children__pk=structure.pk).with_entities(DbNode.id)
    n_children = aliased(DbNode)
    qic = (InlineCalculation.query()
           .join(DbLink, DbNode.id == DbLink.output_id).filter(
               DbLink.input_id.in_(qstruc)
           )
           .join(n_children, DbNode.inputs).filter(
               or_(
                   n_children.attributes["radii_source"].astext.like("%alvarez"),
                   n_children.attributes[("lowdim_dict", "radii_source")].astext.like("%alvarez")
               )
           ).distinct()
        )

    return qic.with_entities(func.count(DbNode.id)).scalar()

def mounet2():
    StructureData = DataFactory('structure')
    structure = load_node(2304207)
    qstruc = StructureData.query(children__pk=structure.pk).with_entities(DbNode.id)

    n_children = aliased(DbNode)
    qic = (InlineCalculation.query()
           .filter(
               DbNode.attributes["function_name"].astext == "lowdimfinder_inline"
           )
           .join(DbLink, DbNode.id == DbLink.output_id).filter(
               DbLink.input_id.in_(qstruc)
           )
           .join(n_children, DbNode.inputs).filter(
               or_(
                   n_children.attributes["radii_source"].astext.like("%alvarez"),
                   n_children.attributes[("lowdim_dict", "radii_source")].astext.like("%alvarez")
               )
           ).distinct()
        )

    return qic.with_entities(func.count(DbNode.id)).scalar()

def mounet_daemon():
    return JobCalculation.query(
        dbattributes__key='state', dbattributes__tval='WITHSCHEDULER'
    ).with_entities(func.count(DbNode.id)).scalar()

def range_queries(percentage):
    return sa.session.query(DbNode.attributes["random"]).filter(
        DbNode.attributes["random"].cast(Float) < percentage
    ).all()

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
        "1": complex_query(),
        "no_cte": complex_query_no_cte(),
        "django_replicate": complex_query_django_replicate()
    },
    "paths": {
        "farthest_cif": get_farthest_cif,
        "closest_struc": get_closest_struc,
        "closest_struc_no_distinct": partial(get_closest_struc, distinct=False),
        "farthest_cif_django": farthest_cif_django,
        "farthest_cif_django_no_distinct": partial(farthest_cif_django, distinct=False)
    },
    "paths_with_attr": {
        "farthest_cif": partial(get_farthest_cif, with_attr=True),
        "closest_struc": partial(get_closest_struc, with_attr=True),
    },
    "verdi": {
        "list_data": list_data_structure(),
        "list_element": list_data_structure(element="C")
    },
    "mounet": {
        "1": mounet1,
        "2": mounet2,
        "daemon": mounet_daemon
    }
}

queries["range"] = dict((i, partial(range_queries, i)) for i in xrange(1, 101))
