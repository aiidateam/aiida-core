# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data upf` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo


@verdi_data.group('upf')
def upf():
    """Manipulation of the upf families."""


@upf.command('uploadfamily')
@click.argument('folder', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument('group_label', type=click.STRING)
@click.argument('group_description', type=click.STRING)
@click.option(
    '--stop-if-existing',
    is_flag=True,
    default=False,
    help='Interrupt pseudos import if a pseudo was already present in the AiiDA database')
@decorators.with_dbenv()
def upf_uploadfamily(folder, group_label, group_description, stop_if_existing):
    """
    Upload a new pseudopotential family.

    Returns the numbers of files found and the number of nodes uploaded.

    Call without parameters to get some help.
    """
    from aiida.orm.nodes.data.upf import upload_upf_family
    files_found, files_uploaded = upload_upf_family(folder, group_label, group_description, stop_if_existing)
    echo.echo_success("UPF files found: {}. New files uploaded: {}".format(files_found, files_uploaded))


@upf.command('listfamilies')
@click.option(
    '-d',
    '--with-description',
    'with_description',
    is_flag=True,
    default=False,
    help="Show also the description for the UPF family")
@options.WITH_ELEMENTS()
@decorators.with_dbenv()
def upf_listfamilies(elements, with_description):
    """
    Print on screen the list of upf families installed
    """
    from aiida import orm
    from aiida.plugins import DataFactory
    from aiida.orm.nodes.data.upf import UPFGROUP_TYPE

    UpfData = DataFactory('upf')  # pylint: disable=invalid-name
    query = orm.QueryBuilder()
    query.append(UpfData, tag='upfdata')
    if elements is not None:
        query.add_filter(UpfData, {'attributes.element': {'in': elements}})
    query.append(
        orm.Group,
        with_node='upfdata',
        tag='group',
        project=["label", "description"],
        filters={"type_string": {
            '==': UPFGROUP_TYPE.value
        }})

    query.distinct()
    if query.count() > 0:
        for res in query.dict():
            group_label = res.get("group").get("label")
            group_desc = res.get("group").get("description")
            query = orm.QueryBuilder()
            query.append(orm.Group, tag='thisgroup', filters={"label": {'like': group_label}})
            query.append(UpfData, project=["id"], with_group='thisgroup')

            if with_description:
                description_string = ": {}".format(group_desc)
            else:
                description_string = ""

            echo.echo_success("* {} [{} pseudos]{}".format(group_label, query.count(), description_string))

    else:
        echo.echo_warning("No valid UPF pseudopotential family found.")


@upf.command('exportfamily')
@click.argument('folder', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@arguments.GROUP()
@decorators.with_dbenv()
def upf_exportfamily(folder, group):
    """
    Export a pseudopotential family into a folder.
    Call without parameters to get some help.
    """
    if group.is_empty:
        echo.echo_critical('Group<{}> contains no pseudos'.format(group.label))

    for node in group.nodes:
        dest_path = os.path.join(folder, node.filename)
        if not os.path.isfile(dest_path):
            with io.open(dest_path, 'w', encoding='utf8') as handle:
                handle.write(node.get_content())
        else:
            echo.echo_warning('File {} is already present in the destination folder'.format(node.filename))


@upf.command('import')
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@decorators.with_dbenv()
def upf_import(filename):
    """
    Import upf data object
    """
    from aiida.orm import UpfData

    node, _ = UpfData.get_or_create(filename)
    echo.echo_success('Imported: {}'.format(node))
