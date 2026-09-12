###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module provides list functionality to all data types."""

from aiida.cmdline.params import options

LIST_OPTIONS = [
    options.GROUPS,
    options.PAST_DAYS,
    options.ALL_USERS,
    options.RAW,
]


def list_options(func):
    """Creates a decorator with all the options."""
    for option in reversed(LIST_OPTIONS):
        func = option()(func)

    return func


def query(datatype, project, past_days, group_pks, all_users):
    """Perform the query"""
    import datetime

    from aiida import orm
    from aiida.common import timezone

    qbl = orm.QueryBuilder()
    if all_users is False:
        user = orm.User.collection.get_default()
        if user is None:
            # TODO: Print warning
            qbl.append(orm.User, tag='creator')
        else:
            qbl.append(orm.User, tag='creator', filters={'email': user.email})
    else:
        qbl.append(orm.User, tag='creator')

    # If there is a time restriction
    data_filters = {}
    if past_days is not None:
        now = timezone.now()
        n_days_ago = now - datetime.timedelta(days=past_days)
        data_filters.update({'ctime': {'>=': n_days_ago}})

    # Since the query results are sorted on ``ctime`` it has to be projected on. If it doesn't exist, append it to the
    # projections, but make sure to pop it again from the final results since it wasn't part of the original projections
    if 'ctime' in project:
        pop_ctime = False
    else:
        project.append('ctime')
        pop_ctime = True

    qbl.append(datatype, tag='data', with_user='creator', filters=data_filters, project=project)

    # If there is a group restriction
    if group_pks is not None:
        group_filters = {}
        group_filters.update({'id': {'in': group_pks}})
        qbl.append(orm.Group, tag='group', filters=group_filters, with_node='data')

    qbl.order_by({datatype: {'ctime': 'asc'}})

    object_list = qbl.distinct()
    results = object_list.all()

    if pop_ctime:
        return [element[:-1] for element in results]

    return results


def data_list(datatype, columns, elements, elements_only, formula_mode, past_days, groups, all_users):
    """List stored objects"""
    columns_dict = {
        'ID': 'id',
        'Id': 'id',
        'Ctime': 'ctime',
        'Label': 'label',
        'Formula': 'attributes.formula',
        'Kinds': 'attributes.kinds',
        'Sites': 'attributes.sites',
        'Formulae': 'attributes.formulae',
        'Source': 'attributes.source',
        'Source.URI': 'attributes.source.uri',
    }
    project = [columns_dict[k] for k in columns]
    group_pks = None
    if groups is not None:
        group_pks = [g.pk for g in groups]
    return query(datatype, project, past_days, group_pks, all_users)
