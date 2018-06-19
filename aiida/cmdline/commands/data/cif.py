# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.orm.data.cif import CifData
from aiida.utils import timezone
import datetime


@verdi_data.group('cif')
@click.pass_context
def cif(ctx):
    """help"""
    pass
    

@click.option('--vseparator', default="\t",
    help="specify vertical separator for fields. Default '\\t'.")
@click.option('--header/--no-header', default=True,
    help="print a header with column names. Default option is with header "
         "enabled.")
@click.option('-p', '--past-days', type=click.INT,
             default=None,
             help="Add a filter to show only bandsdatas"
                  " created in the past N days")
@click.option('-A', '--all-users', is_flag=True, default=False,
             help="show groups for all users, rather than only for the"
                  "current user")
@options.GROUPS()
@cif.command('list')
def list(vseparator, header, past_days, all_users, groups):

    entry_list = query(past_days, all_users, groups)

    if entry_list:
        to_print = ""
        if header:
            to_print += vseparator.join(get_column_names()) + "\n"
        for entry in sorted(entry_list, key=lambda x: int(x[0])):
            to_print += vseparator.join(entry) + "\n"
        echo.echo(to_print)


def get_column_names():
    """
    Return the list with column names.

    :note: neither the number nor correspondence of column names and
        actual columns in the output from the query() are checked.
    """
    return ["ID", "formulae", "source_uri"]

def query(past_days, all_users, groups):
    """
    Perform the query and return information for the list.

    :param args: a namespace with parsed command line parameters.
    :return: table (list of lists) with information, describing nodes.
        Each row describes a single hit.
    """
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.implementation import Group
    from aiida.orm.user import User
    from aiida.orm.backend import construct_backend

    backend = construct_backend()

    qb = QueryBuilder()
    if all_users is False:
        user = backend.users.get_automatic_user()
        qb.append(User, tag="creator", filters={"email": user.email})
    else:
        qb.append(User, tag="creator")

    st_data_filters = {}

    if past_days is not None:
        now = timezone.now()
        n_days_ago = now - datetime.timedelta(days=past_days)
        st_data_filters.update({"ctime": {'>=': n_days_ago}})

    qb.append(CifData, tag="struc", created_by="creator",
              filters=st_data_filters,
              project=["*"])

    if groups is not None and len(groups) != 0:
        group_filters = {}
        group_filters.update({"name": {"in": [g.pk for g in groups]}})
        qb.append(Group, tag="group", filters=group_filters, group_of="struc")

    qb.order_by({CifData: {'ctime': 'asc'}})
    res = qb.distinct()

    entry_list = []
    if res.count() > 0:
        for [obj] in res.iterall():
            formulae = '?'
            try:
                formulae = ",".join(obj.get_attr('formulae'))
            except AttributeError:
                pass
            except TypeError:
                pass
            source_uri = '?'
            try:
                source_uri = obj.get_attr('source')['uri']
            except AttributeError:
                pass
            except KeyError:
                pass
            entry_list.append([str(obj.pk), formulae, source_uri])
    return entry_list

@cif.command()
def show():
    """help"""
    click.echo("Test")
