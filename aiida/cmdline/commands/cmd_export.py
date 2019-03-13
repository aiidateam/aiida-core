# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,import-error
"""`verdi export` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils import echo
from aiida.common.exceptions import DanglingLinkError


@verdi.group('export')
def verdi_export():
    """Create and manage export archives."""


@verdi_export.command('inspect')
@click.argument('archive', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('-v', '--version', is_flag=True, help='Print the archive format version and exit.')
@click.option('-d', '--data', is_flag=True, help='Print the data contents and exit.')
@click.option('-m', '--meta-data', is_flag=True, help='Print the meta data contents and exit.')
@decorators.with_dbenv()
def inspect(archive, version, data, meta_data):
    """
    Inspect the contents of an exported archive without importing the content.

    By default a summary of the archive contents will be printed. The various options can be used to
    change exactly what information is displayed.
    """
    from aiida.common.archive import Archive

    with Archive(archive) as archive_object:
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


@verdi_export.command('create')
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.NODES()
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@click.option(
    '--input-forward/--no-input-forward',
    default=False,
    show_default=True,
    help='Follow forward INPUT links (recursively) when calculating the node set to export.')
@click.option(
    '--create-reversed/--no-create-reversed',
    default=True,
    show_default=True,
    help='Follow reverse CREATE links (recursively) when calculating the node set to export.')
@click.option(
    '--return-reversed/--no-return-reversed',
    default=False,
    show_default=True,
    help='Follow reverse RETURN links (recursively) when calculating the node set to export.')
@click.option(
    '--call-reversed/--no-call-reversed',
    default=False,
    show_default=True,
    help='Follow reverse CALL links (recursively) when calculating the node set to export.')
@click.option(
    '--include-logs/--exclude-logs',
    default=True,
    show_default=True,
    help='Include or exclude logs for node(s) in export.')
@click.option(
    '--include-comments/--exclude-comments',
    default=True,
    show_default=True,
    help='Include or exclude comments for node(s) in export. (Will also export extra users who commented).')
@decorators.with_dbenv()
def create(output_file, codes, computers, groups, nodes, archive_format, force, input_forward, create_reversed,
           return_reversed, call_reversed, include_comments, include_logs):
    """
    Export various entities, such as Codes, Computers, Groups and Nodes, to an archive file for backup or
    sharing purposes.
    """
    from aiida.orm.importexport import export, export_zip

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
        'input_forward': input_forward,
        'create_reversed': create_reversed,
        'return_reversed': return_reversed,
        'call_reversed': call_reversed,
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
    Migrate an existing export archive file to the most recent version of the export format
    """
    import os
    import tarfile
    import zipfile

    from aiida.common import json
    from aiida.common.folders import SandboxFolder
    from aiida.common.archive import extract_zip, extract_tar

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
            with io.open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                data = json.load(fhandle)
            with io.open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
        except IOError:
            echo.echo_critical('export archive does not contain the required file {}'.format(fhandle.filename))

        old_version = verify_metadata_version(metadata)
        new_version = migrate_recursive(metadata, data)

        with io.open(folder.get_abs_path('data.json'), 'wb') as fhandle:
            json.dump(data, fhandle)

        with io.open(folder.get_abs_path('metadata.json'), 'wb') as fhandle:
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


def verify_metadata_version(metadata, version=None):
    """
    Utility function to verify that the metadata has the correct version number.
    If no version number is passed, it will just extract the version number
    and return it.

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the metadata is expected to have
    """
    try:
        metadata_version = metadata['export_version']
    except KeyError:
        raise ValueError('could not find the export_version field in the metadata')

    if version is None:
        return metadata_version

    if metadata_version != version:
        raise ValueError('expected export file with version {} but found version {}'.format(version, metadata_version))

    return None


def update_metadata(metadata, version):
    """
    Update the metadata with a new version number and a notification of the
    conversion that was executed

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the updated metadata should get
    """
    import aiida
    old_version = metadata['export_version']
    conversion_info = metadata.get('conversion_info', [])

    conversion_message = 'Converted from version {} to {} with external script'.format(old_version, version)
    conversion_info.append(conversion_message)

    metadata['aiida_version'] = aiida.get_version()
    metadata['export_version'] = version
    metadata['conversion_info'] = conversion_info


def migrate_v1_to_v2(metadata, data):
    """
    Migration of export files from v0.1 to v0.2, which means generalizing the
    field names with respect to the database backend

    :param data: the content of an export archive data.json file
    :param metadata: the content of an export archive metadata.json file
    """
    old_version = '0.1'
    new_version = '0.2'

    old_start = "aiida.djsite"
    new_start = "aiida.backends.djsite"

    try:
        verify_metadata_version(metadata, old_version)
        update_metadata(metadata, new_version)
    except ValueError:  # pylint: disable=try-except-raise
        raise

    def get_new_string(old_string):
        """Replace the old module prefix with the new."""
        if old_string.startswith(old_start):
            return '{}{}'.format(new_start, old_string[len(old_start):])

        return old_string

    def replace_requires(data):
        """Replace the requires keys with new module path."""
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if key == 'requires' and value.startswith(old_start):
                    new_data[key] = get_new_string(value)
                else:
                    new_data[key] = replace_requires(value)
            return new_data

        return data

    for field in ['export_data']:
        for key in list(data[field]):
            if key.startswith(old_start):
                new_key = get_new_string(key)
                data[field][new_key] = data[field][key]
                del data[field][key]

    for field in ['unique_identifiers', 'all_fields_info']:
        for key in list(metadata[field].keys()):
            if key.startswith(old_start):
                new_key = get_new_string(key)
                metadata[field][new_key] = metadata[field][key]
                del metadata[field][key]

    metadata['all_fields_info'] = replace_requires(metadata['all_fields_info'])


def migrate_v2_to_v3(metadata, data):  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    """
    Migration of export files from v0.2 to v0.3, which means adding the link
    types to the link entries and making the entity key names backend agnostic
    by effectively removing the prefix 'aiida.backends.djsite.db.models'

    :param data: the content of an export archive data.json file
    :param metadata: the content of an export archive metadata.json file
    """
    import enum

    old_version = '0.2'
    new_version = '0.3'

    class LinkType(enum.Enum):  # pylint: disable=too-few-public-methods
        """This was the state of the `aiida.common.links.LinkType` enum before aiida-core v1.0.0a5"""

        UNSPECIFIED = 'unspecified'
        CREATE = 'createlink'
        RETURN = 'returnlink'
        INPUT = 'inputlink'
        CALL = 'calllink'

    class NodeType(enum.Enum):  # pylint: disable=too-few-public-methods
        """A simple enum of relevant node types"""

        NONE = 'none'
        CALC = 'calculation'
        CODE = 'code'
        DATA = 'data'
        WORK = 'work'

    entity_map = {
        'aiida.backends.djsite.db.models.DbNode': 'Node',
        'aiida.backends.djsite.db.models.DbLink': 'Link',
        'aiida.backends.djsite.db.models.DbGroup': 'Group',
        'aiida.backends.djsite.db.models.DbComputer': 'Computer',
        'aiida.backends.djsite.db.models.DbUser': 'User',
        'aiida.backends.djsite.db.models.DbAttribute': 'Attribute'
    }

    try:
        verify_metadata_version(metadata, old_version)
        update_metadata(metadata, new_version)
    except ValueError:  # pylint: disable=try-except-raise
        raise

    # Create a mapping from node uuid to node type
    mapping = {}
    for nodes in data['export_data'].values():
        for node in nodes.values():

            try:
                node_uuid = node['uuid']
                node_type_string = node['type']
            except KeyError:
                continue

            if node_type_string.startswith('calculation.job.'):
                node_type = NodeType.CALC
            elif node_type_string.startswith('calculation.inline.'):
                node_type = NodeType.CALC
            elif node_type_string.startswith('code.Code'):
                node_type = NodeType.CODE
            elif node_type_string.startswith('data.'):
                node_type = NodeType.DATA
            elif node_type_string.startswith('calculation.work.'):
                node_type = NodeType.WORK
            else:
                node_type = NodeType.NONE

            mapping[node_uuid] = node_type

    # For each link, deduce the link type and insert it in place
    for link in data['links_uuid']:

        try:
            input_type = NodeType(mapping[link['input']])
            output_type = NodeType(mapping[link['output']])
        except KeyError:
            raise DanglingLinkError('Unknown node UUID {} or {}'.format(link['input'], link['output']))

        # The following table demonstrates the logic for infering the link type
        # (CODE, DATA) -> (WORK, CALC) : INPUT
        # (CALC)       -> (DATA)       : CREATE
        # (WORK)       -> (DATA)       : RETURN
        # (WORK)       -> (CALC, WORK) : CALL
        if input_type in [NodeType.CODE, NodeType.DATA] and output_type in [NodeType.CALC, NodeType.WORK]:
            link['type'] = LinkType.INPUT.value
        elif input_type == NodeType.CALC and output_type == NodeType.DATA:
            link['type'] = LinkType.CREATE.value
        elif input_type == NodeType.WORK and output_type == NodeType.DATA:
            link['type'] = LinkType.RETURN.value
        elif input_type == NodeType.WORK and output_type in [NodeType.CALC, NodeType.WORK]:
            link['type'] = LinkType.CALL.value
        else:
            link['type'] = LinkType.UNSPECIFIED.value

    # Now we migrate the entity key names i.e. removing the 'aiida.backends.djsite.db.models' prefix
    for field in ['unique_identifiers', 'all_fields_info']:
        for old_key, new_key in entity_map.items():
            if old_key in metadata[field]:
                metadata[field][new_key] = metadata[field][old_key]
                del metadata[field][old_key]

    # Replace the 'requires' keys in the nested dictionaries in 'all_fields_info'
    for entity in metadata['all_fields_info'].values():
        for prop in entity.values():
            for key, value in prop.items():
                if key == 'requires' and value in entity_map:
                    prop[key] = entity_map[value]

    # Replace any present keys in the data.json
    for field in ['export_data']:
        for old_key, new_key in entity_map.items():
            if old_key in data[field]:
                data[field][new_key] = data[field][old_key]
                del data[field][old_key]


def migrate_recursive(metadata, data):
    """
    Recursive migration of export files from v0.1 to newest version,
    See specific migration functions for detailed descriptions.
    NOTE: Remember to update newest_version to the newest export version,
    when/if a migration is available.

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    """
    newest_version = '0.3'
    old_version = verify_metadata_version(metadata)

    try:
        if old_version == '0.1':
            migrate_v1_to_v2(metadata, data)
        elif old_version == '0.2':
            migrate_v2_to_v3(metadata, data)
        else:
            echo.echo_critical('cannot migrate from version {}'.format(old_version))
    except ValueError as exception:
        echo.echo_critical(exception)
    except DanglingLinkError:
        echo.echo_critical('export file is invalid because it contains dangling links')

    new_version = verify_metadata_version(metadata)

    if new_version < newest_version:
        migrate_recursive(metadata, data)

    return new_version
