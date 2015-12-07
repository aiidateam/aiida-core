# -*- coding: utf-8 -*-

from collections import defaultdict


from aiida.backends.profile import load_profile
from aiida.backends.djsite.utils import load_dbenv
from aiida.backends.djsite.db import models

from aiida.common.utils import grouper

from aiida.orm import DataFactory, CalculationFactory
from aiida.orm.implementation.general.calculation.inline import InlineCalculation


from django.db.models import Q


def build_deserialized_dict(query_values):
    first_dict = defaultdict(dict)
    for e in query_values:
        first_dict[e[0]][e[1]] = {
            "datatype": e[2],
            "tval": e[3],
            "fval": e[4],
            "ival": e[5],
            "bval": e[6],
            "dval": e[7]
        }

    result_dict = {}
    for pk in first_dict:
        result_dict[pk] = models.deserialize_attributes(
            first_dict[pk],
            sep=models.DbAttribute._sep)

    return result_dict

def build_query_attr(filter_):
    nodes = models.DbNode.objects.filter(
        dbgroups__name__startswith='N_elements_',
        dbgroups__name__endswith='_clean_cif_primitive_dup_filtered'
    ).distinct()

    pks = models.DbAttribute.objects.filter(
        dbnode__in=nodes, key__startswith=filter_
    ).distinct().values_list(
        'dbnode__pk', 'key', 'datatype', 'tval', 'fval', 'ival', 'bval', 'dval').distinct()
    # Unnecessary distinct at the end ?

    return lambda: build_deserialized_dict(pks)


def get_closest_cif():
    """
    Get closest cif data in the parents of all nodes
    :param nodes: list of nodes
    """

    # Cif nodes are usually the in the root of the graph
    # BandsData are the leaves of the graph
    # This query uses the transitive closure table
    node_type = 'CifData'
    BandsData = DataFactory('array.bands')
    nodes = BandsData.query()

    depth = models.DbPath.objects.filter(
        child__in=nodes, parent__type__contains=node_type
    ).distinct().order_by('depth').values_list('depth')[0][0]

    q = models.DbPath.objects.filter(
        parent__type__contains=node_type, child__in=nodes,depth=depth
    ).distinct()

    res = DataFactory('cif').query(
        children__in=nodes,child_paths__in=q
    ).distinct().order_by('ctime')

    return list(res)


def get_farthest_struc():
    BandsData = DataFactory('array.bands')
    nodes = BandsData.query()
    struc_type = DataFactory('structure')().__class__.__name__

    depth = models.DbPath.objects.filter(
        child__in=nodes, parent__type__contains=struc_type
    ).distinct().order_by('-depth').values_list('depth')[0][0]

    q = models.DbPath.objects.filter(
        parent__type__contains=struc_type, child__in=nodes,depth=depth
    ).distinct()

    res = DataFactory('structure').query(
        children__in=nodes,child_paths__in=q
    ).distinct().order_by('ctime')

    return list(res)

def complex_query():
    RemoteData = DataFactory('remote')
    PwCalculation = CalculationFactory('quantumespresso.pw')

    pws = models.DbNode.objects.filter(type=PwCalculation._plugin_type_string)
    scratchremotes = models.DbNode.objects.filter(type=RemoteData._plugin_type_string,
                                                  inputs__in=pws)
    inlines = models.DbNode.objects.filter(type=InlineCalculation._plugin_type_string,
                                           inputs__in=scratchremotes)
    storeremotes = models.DbNode.objects.filter(type=RemoteData._plugin_type_string,
                                                inputs__in=inlines)

    q = storeremotes.values_list('uuid', flat=True)

    return lambda: list(q)

def list_data_structure(element=None, query_group_size=100):
    struct_list = models.DbNode.objects.filter(type__startswith="data.structure.")
    if element:
        attr_query = models.DbAttribute.objects.filter(
            key__startswith='kinds.',
            key__contains='.symbols.',
            tval=element
        )
        struct_list = struct_list.filter(dbattributes__in=attr_query)
    struct_list = struct_list.distinct().order_by('ctime').values_list('pk', 'label')

    def f():
        struc_list_pks_grouped = grouper(query_group_size,
                                         [_[0] for _ in struct_list])

        d = {}
        for struc_list_pks_part in struc_list_pks_grouped:
            attr_query = Q(key__startswith='kinds') | Q(key__startswith='sites')
            attrs = models.DbAttribute.objects.filter(
                attr_query,
                dbnode__in=struc_list_pks_part).values_list(
                    'dbnode__pk', 'key', 'datatype', 'tval', 'fval',
                    'ival', 'bval', 'dval'
                )

            d.update(build_deserialized_dict(attrs))

        return d

    return f



queries = {
    "attributes": {
        'kinds': build_query_attr('kinds'),
        'sites': build_query_attr('sites'),
        'cell': build_query_attr('cell')
    },
    "paths": {
        "closest_cif": get_closest_cif,
        "farthest_struc": get_farthest_struc,
    },
    "complex": {
        "1": complex_query()
    },
    "verdi": {
        "list_data": list_data_structure(),
        "list_element": list_data_structure(element="C")
    }
}
