# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common procedure to get the list of groups required both by the command and the parameter."""

__all__ = ('get_group_list_builder',)


def get_group_list_builder(
    group_partial=None,
    all_users=False,
    user=None,
    all_entries=False,
    type_string=None,
    past_days=None,
    startswith=None,
    endswith=None,
    contains=None,
    order_by='label',
    order_dir='asc',
    node=None,
    project_labels=False,
):
    # pylint: disable=too-many-branches
    """Returns a querybuilder ready to use."""
    import datetime

    from aiida import orm
    from aiida.common import timezone
    from aiida.common.escaping import escape_for_sql_like

    builder = orm.QueryBuilder()
    filters = {}

    # Have to specify the default for `type_string` here instead of directly in the option otherwise it will always
    # raise above if the user specifies just the `--group-type` option. Once that option is removed, the default can
    # be moved to the option itself.
    if type_string is None:
        type_string = 'core'

    if not all_entries:
        if '%' in type_string or '_' in type_string:
            filters['type_string'] = {'like': type_string}
        else:
            filters['type_string'] = type_string

    # Creation time
    if past_days:
        filters['time'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

    # Query for specific group labels
    filters['or'] = []
    if startswith:
        filters['or'].append({'label': {'like': f'{escape_for_sql_like(startswith)}%'}})
    if endswith:
        filters['or'].append({'label': {'like': f'%{escape_for_sql_like(endswith)}'}})
    if contains:
        filters['or'].append({'label': {'like': f'%{escape_for_sql_like(contains)}%'}})
    if group_partial is not None:
        filters['or'].append({'label': {'like': f'{escape_for_sql_like(group_partial)}%'}})

    if project_labels:
        builder.append(orm.Group, filters=filters, tag='group', project='label')
    else:
        builder.append(orm.Group, filters=filters, tag='group', project='*')

    # Query groups that belong to specific user
    if user:
        user_email = user.email
    else:
        # By default: only groups of this user
        user_email = orm.User.collection.get_default().email

    # Query groups that belong to all users
    if not all_users:
        builder.append(orm.User, filters={'email': {'==': user_email}}, with_group='group')

    # Query groups that contain a particular node
    if node:
        builder.append(orm.Node, filters={'id': {'==': node.pk}}, with_group='group')

    builder.order_by({orm.Group: {order_by: order_dir}})
    return builder
