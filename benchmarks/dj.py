# -*- coding: utf-8 -*-

from collections import defaultdict

from functools import partial


from aiida.backends.profile import load_profile
from aiida.backends.djsite.utils import load_dbenv
from aiida.backends.djsite.db import models

from aiida.common.utils import grouper

from aiida.orm import DataFactory, CalculationFactory, Group, JobCalculation, load_node
from aiida.orm.implementation.general.calculation.inline import InlineCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData


from django.db.models import Q


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

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

def build_query_attr(filter_, distinct=True):
    nodes = models.DbNode.objects.filter(
        dbgroups__name__startswith='N_elements_',
        dbgroups__name__endswith='_clean_cif_primitive_dup_filtered'
    )
    if distinct:
        nodes = nodes.distinct()

    pks = models.DbAttribute.objects.filter(
        dbnode__in=nodes, key__startswith=filter_
    ).values_list(
        'dbnode__pk', 'key', 'datatype', 'tval', 'fval', 'ival', 'bval', 'dval')
    if distinct:
        pks = pks.distinct()

    return lambda: build_deserialized_dict(pks.all())

def get_farthest_cif():

    nodes = ParameterData.query()
    cif_type = CifData._query_type_string

    depth = models.DbPath.objects.filter(
        child__in=nodes, parent__type__contains=cif_type
    ).distinct().order_by('-depth').values_list('depth')[0][0]

    q = models.DbPath.objects.filter(
        parent__type__contains=cif_type, child__in=nodes,depth=depth
    ).distinct()

    res = CifData.query(
        children__in=nodes, child_paths__in=q
    ).distinct().order_by('ctime')

    return list(res)

def get_closest_struc():
    nodes = ParameterData.query()
    struc_type = StructureData._query_type_string

    depth = models.DbPath.objects.filter(
        child__in=nodes, parent__type__contains=struc_type
    ).distinct().order_by('depth').values_list('depth')[0][0]

    q = models.DbPath.objects.filter(
        parent__type__contains=struc_type, child__in=nodes,depth=depth
    ).distinct()

    res = StructureData.query(
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

    return lambda: list(q.all())

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

def mounet1(with_key_filter=False):
    pw_calc = Group.get(pk=1139193).nodes.next()
    structure = pw_calc.out.output_structure
    qstruc = StructureData.query(children__pk=structure.pk)
    attr_filters = models.DbAttribute.objects.filter(tval__endswith='alvarez')

    # Because we can't reproduce a filter on the value only with a JSON table,
    # a fairer comparison would be with a filter on the key too.
    if with_key_filter:
        attr_filters = attr_filters.filter(Q(key="radii_source") | Q(key="lowdim_dict.radii_source"))

    qic = InlineCalculation.query(inputs__in=qstruc).filter(
        inputs__dbattributes__in=attr_filters).distinct()

    return qic.count()

def mounet2(with_key_filter=False):
    StructureData = DataFactory('structure')
    structure = load_node(2304207)
    qstruc = StructureData.query(children__pk=structure.pk)
    qattr = models.DbAttribute.objects.filter(
        key='function_name', tval='lowdimfinder_inline', dbnode__inputs__in=qstruc
    )

    attr_filters = models.DbAttribute.objects.filter(tval__endswith='alvarez')

    if with_key_filter:
        attr_filters = attr_filters.filter(Q(key="radii_source") | Q(key="lowdim_dict.radii_source"))

    qic = InlineCalculation.query(
        inputs__in=qstruc,
        dbattributes__in=qattr
    ).filter(inputs__dbattributes__in=attr_filters).distinct()

    return qic.count()

def mounet_daemon():
    return JobCalculation.query(
        dbattributes__key='state', dbattributes__tval='WITHSCHEDULER'
    ).count()


queries = {
    "attributes": {
        'kinds': build_query_attr('kinds'),
        'sites': build_query_attr('sites'),
        'cell': build_query_attr('cell')
    },
    "attributes_no_distinct": {
        'kinds': build_query_attr('kinds', distinct=False),
        'sites': build_query_attr('sites', distinct=False),
        'cell': build_query_attr('cell', distinct=False)
    },
    "paths": {
        "farthest_cif": get_farthest_cif,
        "closest_struc": get_closest_struc,
    },
    "complex": {
        "1": complex_query()
    },
    "verdi": {
        "list_element": list_data_structure(element="C"),
        "list_data": list_data_structure(),
    },
    "mounet": {
        "1": mounet1,
        "1_key_filter": partial(mounet1, with_key_filter=True),
        "2": mounet2,
        "2_key_filter": partial(mounet2, with_key_filter=True),
        "daemon": mounet_daemon
    }
}

for i in [100, 250, 500, 750, 1000]:
    queries["verdi"]["list_data_{}".format(i)] = list_data_structure(query_group_size=i)
