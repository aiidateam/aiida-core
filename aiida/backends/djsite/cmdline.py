# -*- coding: utf-8 -*-

# Regroup Django's specific function needed by the command line.

from aiida.orm.implementation.django.group import Group

def get_group_list(user, type_string, past_days=None,
                   name_filters={}):

    name_filters = { "name__" + k: v for k, v in name_filters }

    groups = Group.query(user=user, type_string=type_string, past_days=past_days,
                        **name_filters)

    return tuple([
        (str(g.pk), g.name, len(g.nodes), g.user.email.strip(), g.description)
        for g in groups
    ])
