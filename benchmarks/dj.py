# -*- coding: utf-8 -*-

from collections import defaultdict


from aiida.backends.profile import load_profile
from aiida.backends.djsite.utils import load_dbenv
from aiida.backends.djsite.db import models


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

queries = {
    "attributes": {
        'kinds': build_query_attr('kinds'),
        'sites': build_query_attr('sites'),
        'cell': build_query_attr('cell')
    }
}
