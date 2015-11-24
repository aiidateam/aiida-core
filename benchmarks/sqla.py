# -*- coding: utf-8 -*-


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

queries = {
    "attributes": {
        'kinds': build_query_attr('kinds'),
        'sites': build_query_attr('sites'),
        'cell:': build_query_attr('cell')
    }
}
