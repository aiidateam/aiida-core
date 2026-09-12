###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data core.upf` command."""

import os

import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.commands.cmd_data.cmd_export import data_export, export_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo


@verdi_data.group('core.upf')
def upf():
    """Manipulate UpfData objects (UPF-format pseudopotentials)."""


@upf.command(
    'uploadfamily',
    deprecated='See https://aiida-pseudo.readthedocs.io/en/latest/howto.html#migrate-from-legacy-upfdata-from-aiida-core',
)
@click.argument('folder', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument('group_label', type=click.STRING)
@click.argument('group_description', type=click.STRING)
@click.option(
    '--stop-if-existing',
    is_flag=True,
    default=False,
    help='Interrupt pseudos import if a pseudo was already present in the AiiDA database',
)
@decorators.with_dbenv()
def upf_uploadfamily(folder, group_label, group_description, stop_if_existing):
    """Create a new UPF family from a folder of UPF files.

    Returns the numbers of files found and the number of nodes uploaded.

    Call without parameters to get some help.
    """
    from aiida.orm.nodes.data.upf import upload_upf_family

    files_found, files_uploaded = upload_upf_family(folder, group_label, group_description, stop_if_existing)
    echo.echo_success(f'UPF files found: {files_found}. New files uploaded: {files_uploaded}')


@upf.command(
    'listfamilies',
    deprecated='See https://aiida-pseudo.readthedocs.io/en/latest/howto.html#migrate-from-legacy-upfdata-from-aiida-core',
)
@click.option(
    '-d',
    '--with-description',
    'with_description',
    is_flag=True,
    default=False,
    help='Show also the description for the UPF family',
)
@options.WITH_ELEMENTS()
@decorators.with_dbenv()
def upf_listfamilies(elements, with_description):
    """List all UPF families that exist in the database."""
    from aiida import orm
    from aiida.plugins import DataFactory

    UpfData = DataFactory('core.upf')  # noqa: N806
    query = orm.QueryBuilder()
    query.append(UpfData, tag='upfdata')
    if elements is not None:
        query.add_filter(UpfData, {'attributes.element': {'in': elements}})
    query.append(orm.UpfFamily, with_node='upfdata', tag='group', project=['label', 'description'])

    query.distinct()
    if query.count() > 0:
        for res in query.dict():
            group_label = res.get('group', {}).get('label')
            group_desc = res.get('group', {}).get('description')
            query = orm.QueryBuilder()
            query.append(orm.Group, tag='thisgroup', filters={'label': {'like': group_label}})
            query.append(UpfData, project=['id'], with_group='thisgroup')

            if with_description:
                description_string = f': {group_desc}'
            else:
                description_string = ''

            echo.echo_success(f'* {group_label} [{query.count()} pseudos]{description_string}')

    else:
        echo.echo_warning('No valid UPF pseudopotential family found.')


@upf.command(
    'exportfamily',
    deprecated='See https://aiida-pseudo.readthedocs.io/en/latest/howto.html#migrate-from-legacy-upfdata-from-aiida-core',
)
@click.argument('folder', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@arguments.GROUP()
@decorators.with_dbenv()
def upf_exportfamily(folder, group):
    """Export a pseudopotential family into a folder.
    Call without parameters to get some help.
    """
    if group.is_empty:
        echo.echo_critical(f'Group<{group.label}> contains no pseudos')

    for node in group.nodes:
        dest_path = os.path.join(folder, node.filename)
        if not os.path.isfile(dest_path):
            with open(dest_path, 'w', encoding='utf8') as handle:
                handle.write(node.get_content())
        else:
            echo.echo_warning(f'File {node.filename} is already present in the destination folder')


@upf.command(
    'import',
    deprecated='See https://aiida-pseudo.readthedocs.io/en/latest/howto.html#migrate-from-legacy-upfdata-from-aiida-core',
)
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@decorators.with_dbenv()
def upf_import(filename):
    """Import a UPF pseudopotential from a file."""
    from aiida.orm import UpfData

    node, _ = UpfData.get_or_create(filename)
    echo.echo_success(f'Imported: {node}')


@upf.command(
    'export',
    deprecated='See https://aiida-pseudo.readthedocs.io/en/latest/howto.html#migrate-from-legacy-upfdata-from-aiida-core',
)
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.upf',)))
@options.EXPORT_FORMAT(
    type=click.Choice(['json']),
    default='json',
)
@export_options
@decorators.with_dbenv()
def upf_export(**kwargs):
    """Export `UpfData` object to file."""
    node = kwargs.pop('datum')
    output = kwargs.pop('output')
    fmt = kwargs.pop('fmt')
    force = kwargs.pop('force')

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    data_export(node, output, fmt, other_args=kwargs, overwrite=force)
