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

    .. deprecated:: 1.5.0
        Support for the --data flag

    """
    import dataclasses
    from aiida.tools.importexport import CorruptArchive, detect_archive_type, get_reader

    reader_cls = get_reader(detect_archive_type(archive))

    with reader_cls(archive) as reader:
        try:
            if version:
                echo.echo(reader.export_version)
            elif data:
                # data is an internal implementation detail
                echo.echo_deprecated('--data is deprecated and will be removed in v2.0.0')
                echo.echo_dictionary(reader._get_data())  # pylint: disable=protected-access
            elif meta_data:
                echo.echo_dictionary(dataclasses.asdict(reader.metadata))
            else:
                statistics = {
                    'Version aiida': reader.metadata.aiida_version,
                    'Version format': reader.metadata.export_version,
                    'Computers': reader.entity_count('Computer'),
                    'Groups': reader.entity_count('Group'),
                    'Links': reader.link_count,
                    'Nodes': reader.entity_count('Node'),
                    'Users': reader.entity_count('User'),
                }
                if reader.metadata.conversion_info:
                    statistics['Conversion info'] = '\n'.join(reader.metadata.conversion_info)

                echo.echo(tabulate.tabulate(statistics.items()))
        except CorruptArchive as exception:
            echo.echo_critical(f'corrupt archive: {exception}')


@verdi_export.command('create')
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.NODES()
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@click.option(
    '-v',
    '--verbosity',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'CRITICAL']),
    help='Control the verbosity of console logging'
)
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
    create_backward, return_backward, call_calc_backward, call_work_backward, include_comments, include_logs, verbosity
):
    """
    Export subsets of the provenance graph to file for sharing.

    Besides Nodes of the provenance graph, you can export Groups, Codes, Computers, Comments and Logs.

    By default, the archive file will include not only the entities explicitly provided via the command line but also
    their provenance, according to the rules outlined in the documentation.
    You can modify some of those rules using options of this command.
    """
    from aiida.common.log import override_log_formatter_context
    from aiida.common.progress_reporter import set_progress_bar_tqdm
    from aiida.tools.importexport import export, ExportFileFormat, EXPORT_LOGGER
    from aiida.tools.importexport.common.exceptions import ArchiveExportError

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
        export_format = ExportFileFormat.ZIP
        kwargs.update({'use_compression': True})
    elif archive_format == 'zip-uncompressed':
        export_format = ExportFileFormat.ZIP
        kwargs.update({'use_compression': False})
    elif archive_format == 'tar.gz':
        export_format = ExportFileFormat.TAR_GZIPPED

    if verbosity in ['DEBUG', 'INFO']:
        set_progress_bar_tqdm(leave=(verbosity == 'DEBUG'))
    EXPORT_LOGGER.setLevel(verbosity)

    try:
        with override_log_formatter_context('%(message)s'):
            export(entities, filename=output_file, file_format=export_format, **kwargs)
    except ArchiveExportError as exception:
        echo.echo_critical(f'failed to write the archive file. Exception: {exception}')
    else:
        echo.echo_success(f'wrote the export archive file to {output_file}')


@verdi_export.command('migrate')
@arguments.INPUT_FILE()
@arguments.OUTPUT_FILE(required=False)
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@click.option('-i', '--in-place', is_flag=True, help='Migrate the archive in place, overwriting the original file.')
@options.SILENT()
@click.option(
    '-v',
    '--version',
    type=click.STRING,
    required=False,
    metavar='VERSION',
    # Note: Adding aiida.tools.EXPORT_VERSION as a default value explicitly would result in a slow import of
    # aiida.tools and, as a consequence, aiida.orm. As long as this is the case, better determine the latest export
    # version inside the function when needed.
    help='Archive format version to migrate to (defaults to latest version).',
)
def migrate(input_file, output_file, force, silent, in_place, archive_format, version):
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    """Migrate an export archive to a more recent format version."""
    from distutils.version import StrictVersion
    import os
    import shutil
    import tarfile
    import tempfile
    import zipfile

    from aiida.common import json
    from aiida.common.folders import SandboxFolder
    from aiida.tools.importexport import migration, extract_zip, extract_tar, ArchiveMigrationError, EXPORT_VERSION

    if version is None:
        version = EXPORT_VERSION

    if in_place:
        if output_file:
            echo.echo_critical('output file specified together with --in-place flag')
        tempdir = tempfile.TemporaryDirectory()
        output_file = os.path.join(tempdir.name, 'archive.aiida')
    elif not output_file:
        echo.echo_critical(
            'no output file specified. Please add --in-place flag if you would like to migrate in place.'
        )

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
            echo.echo_critical(f'export archive does not contain the required file {fhandle.filename}')

        old_version = migration.verify_metadata_version(metadata)
        if StrictVersion(version) <= StrictVersion(old_version):
            echo.echo_success(f'nothing to be done - archive already at version {old_version} >= {version}')
            return

        try:
            new_version = migration.migrate_recursively(metadata, data, folder, version)
        except ArchiveMigrationError as exception:
            echo.echo_critical(str(exception))

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

        if in_place:
            shutil.move(output_file, input_file)
            tempdir.cleanup()

        if not silent:
            echo.echo_success(f'migrated the archive from version {old_version} to {new_version}')
