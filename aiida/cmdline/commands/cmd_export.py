# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,import-error,too-many-locals
"""`verdi export` command."""

import os

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils import echo
from aiida.common.links import GraphTraversalRules


@verdi.group('export')
def verdi_export():
    """Create and manage export archives."""


@verdi_export.command('inspect')
@click.argument('archive', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('-v', '--version', is_flag=True, help='Print the archive format version and exit.')
@click.option('-d', '--data', is_flag=True, help='Print the data contents and exit.')
@click.option('-m', '--meta-data', is_flag=True, help='Print the meta data contents and exit.')
def inspect(archive, version, data, meta_data):
    """Inspect contents of an exported archive without importing it.

    By default a summary of the archive contents will be printed. The various options can be used to change exactly what
    information is displayed.
    """
    from aiida.tools.importexport import Archive, CorruptArchive

    with Archive(archive) as archive_object:
        try:
            if version:
                echo.echo(archive_object.version_format)
            elif data:
                echo.echo_dictionary(archive_object.data)
            elif meta_data:
                echo.echo_dictionary(archive_object.meta_data)
            else:
                info = archive_object.get_info()
                data = sorted([(k.capitalize(), v) for k, v in info.items()])
                data.extend(sorted([(k.capitalize(), v) for k, v in archive_object.get_data_statistics().items()]))
                echo.echo(tabulate.tabulate(data))
        except CorruptArchive as exception:
            echo.echo_critical('corrupt archive: {}'.format(exception))


@verdi_export.command('create')
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.NODES()
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@options.graph_traversal_rules(GraphTraversalRules.EXPORT.value)
@click.option(
    '--include-logs/--exclude-logs',
    default=True,
    show_default=True,
    help='Include or exclude logs for node(s) in export.'
)
@click.option(
    '--include-comments/--exclude-comments',
    default=True,
    show_default=True,
    help='Include or exclude comments for node(s) in export. (Will also export extra users who commented).'
)
@decorators.with_dbenv()
def create(
    output_file, codes, computers, groups, nodes, archive_format, force, input_calc_forward, input_work_forward,
    create_backward, return_backward, call_calc_backward, call_work_backward, include_comments, include_logs
):
    """
    Export subsets of the provenance graph to file for sharing.

    Besides Nodes of the provenance graph, you can export Groups, Codes, Computers, Comments and Logs.

    By default, the export file will include not only the entities explicitly provided via the command line but also
    their provenance, according to the rules outlined in the documentation.
    You can modify some of those rules using options of this command.
    """
    from aiida.tools.importexport import export, export_zip

    entities = []

    if codes:
        entities.extend(codes)

    if computers:
        entities.extend(computers)

    if groups:
        entities.extend(groups)

    if nodes:
        entities.extend(nodes)

    kwargs = {
        'input_calc_forward': input_calc_forward,
        'input_work_forward': input_work_forward,
        'create_backward': create_backward,
        'return_backward': return_backward,
        'call_calc_backward': call_calc_backward,
        'call_work_backward': call_work_backward,
        'include_comments': include_comments,
        'include_logs': include_logs,
        'overwrite': force
    }

    if archive_format == 'zip':
        export_function = export_zip
        kwargs.update({'use_compression': True})
    elif archive_format == 'zip-uncompressed':
        export_function = export_zip
        kwargs.update({'use_compression': False})
    elif archive_format == 'tar.gz':
        export_function = export

    try:
        export_function(entities, outfile=output_file, **kwargs)

    except IOError as exception:
        echo.echo_critical('failed to write the export archive file: {}'.format(exception))
    else:
        echo.echo_success('wrote the export archive file to {}'.format(output_file))


@verdi_export.command('migrate')
@arguments.INPUT_FILE()
@arguments.OUTPUT_FILE()
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@options.SILENT()
def migrate(input_file, output_file, force, silent, archive_format):
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    """
    Migrate an old export archive file to the most recent format.
    """
    import tarfile
    import zipfile

    from aiida.common import json
    from aiida.common.folders import SandboxFolder
    from aiida.tools.importexport import migration, extract_zip, extract_tar

    if os.path.exists(output_file) and not force:
        echo.echo_critical('the output file already exists')

    with SandboxFolder(sandbox_in_repo=False) as folder:

        if zipfile.is_zipfile(input_file):
            extract_zip(input_file, folder, silent=silent)
        elif tarfile.is_tarfile(input_file):
            extract_tar(input_file, folder, silent=silent)
        else:
            echo.echo_critical('invalid file format, expected either a zip archive or gzipped tarball')

        try:
            with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                data = json.load(fhandle)
            with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
        except IOError:
            echo.echo_critical('export archive does not contain the required file {}'.format(fhandle.filename))

        old_version = migration.verify_metadata_version(metadata)
        new_version = migration.migrate_recursively(metadata, data, folder)

        with open(folder.get_abs_path('data.json'), 'wb') as fhandle:
            json.dump(data, fhandle, indent=4)

        with open(folder.get_abs_path('metadata.json'), 'wb') as fhandle:
            json.dump(metadata, fhandle)

        if archive_format in ['zip', 'zip-uncompressed']:
            compression = zipfile.ZIP_DEFLATED if archive_format == 'zip' else zipfile.ZIP_STORED
            with zipfile.ZipFile(output_file, mode='w', compression=compression, allowZip64=True) as archive:
                src = folder.abspath
                for dirpath, dirnames, filenames in os.walk(src):
                    relpath = os.path.relpath(dirpath, src)
                    for filename in dirnames + filenames:
                        real_src = os.path.join(dirpath, filename)
                        real_dest = os.path.join(relpath, filename)
                        archive.write(real_src, real_dest)
        elif archive_format == 'tar.gz':
            with tarfile.open(output_file, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as archive:
                archive.add(folder.abspath, arcname='')

        if not silent:
            echo.echo_success('migrated the archive from version {} to {}'.format(old_version, new_version))
