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
from aiida.cmdline.commands import verdi, export
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class DanglingLinkError(Exception):
    pass

class Export(VerdiCommandWithSubcommands):
    """
    Create and manage AiiDA export archives
    """
    def __init__(self):
        self.valid_subcommands = {
            'create': (self.cli, self.complete_none),
            'migrate': (self.cli, self.complete_none)
        }

    def cli(self, *args):
        verdi()


@export.command('create', context_settings=CONTEXT_SETTINGS)
@click.argument('outfile', type=click.Path())
@click.option('-n', '--nodes', multiple=True, type=int,
    help='Export the given nodes by pk')
@click.option('-c', '--computers', multiple=True, type=int,
    help='Export the given computers by pk')
@click.option('-G', '--groups', multiple=True, type=int,
    help='Export the given groups by pk')
@click.option('-g', '--group-names', multiple=True, type=str,
    help='Export the given groups by group name')
@click.option('-I', '--input-forward', is_flag=True, default=False,
    show_default=True, help='Follow forward INPUT links (recursively) when '
                            'calculating the node set to export.')
@click.option('-C', '--create-reversed', is_flag=True, default=True,
    show_default=True, help='Follow reverse CREATE links (recursively) when '
                            'calculating the node set to export.')
@click.option('-R', '--return-reversed', is_flag=True, default=False,
    show_default=True, help='Follow reverse RETURN links (recursively) when '
                            'calculating the node set to export.')
@click.option('-X', '--call-reversed', is_flag=True, default=False,
    show_default=True, help='Follow reverse CALL links (recursively) when '
                            'calculating the node set to export.')
@click.option('-f', '--overwrite', is_flag=True, default=False,
    help='Overwrite the output file, if it exists')
@click.option('-a', '--archive-format',
              type=click.Choice(['zip', 'zip-uncompressed', 'tar.gz']),
              default='zip')
def create(outfile, computers, groups, nodes, group_names, input_forward,
           create_reversed, return_reversed, call_reversed, overwrite,
           archive_format):
    """
    Export nodes and groups of nodes to an archive file for backup or sharing purposes
    """
    import sys
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    # TODO: Replace with aiida.cmdline.utils.decorators.with_dbenv decocator
    # TODO: when we merge to develop
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.orm import Group, Node, Computer
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.importexport import export, export_zip

    node_id_set = set(nodes)
    group_dict = dict()

    if group_names:
        qb = QueryBuilder()
        qb.append(Group, tag='group', project=['*'], filters={'name': {'in': group_names}})
        qb.append(Node, tag='node', member_of='group', project=['id'])
        res = qb.dict()

        group_dict.update(
            {group['group']['*'].id: group['group']['*'] for group in res})
        node_id_set.update([node['node']['id'] for node in res])

    if groups:
        qb = QueryBuilder()
        qb.append(Group, tag='group', project=['*'], filters={'id': {'in': groups}})
        qb.append(Node, tag='node', member_of='group', project=['id'])
        res = qb.dict()

        group_dict.update(
            {group['group']['*'].id: group['group']['*'] for group in res})
        node_id_set.update([node['node']['id'] for node in res])

    groups_list = group_dict.values()

    # Getting the nodes that correspond to the ids that were found above
    if len(node_id_set) > 0:
        qb = QueryBuilder()
        qb.append(Node, tag='node', project=['*'], filters={'id': {'in': node_id_set}})
        node_list = [node[0] for node in qb.all()]
    else:
        node_list = list()

    # Check if any of the nodes wasn't found in the database.
    missing_nodes = node_id_set.difference(node.id for node in node_list)
    for node_id in missing_nodes:
        print >> sys.stderr, ('WARNING! Node with pk={} not found, skipping'.format(node_id))

    if computers:
        qb = QueryBuilder()
        qb.append(Computer, tag='comp', project=['*'], filters={'id': {'in': set(computers)}})
        computer_list = [computer[0] for computer in qb.all()]
        missing_computers = set(computers).difference(computer.id for computer in computer_list)

        for computer_id in missing_computers:
            print >> sys.stderr, ('WARNING! Computer with pk={} not found, skipping'.format(computer_id))
    else:
        computer_list = []

    what_list = node_list + computer_list + groups_list
    additional_kwargs = dict()

    if archive_format == 'zip':
        export_function = export_zip
        additional_kwargs.update({'use_compression': True})
    elif archive_format == 'zip-uncompressed':
        export_function = export_zip
        additional_kwargs.update({'use_compression': False})
    elif archive_format == 'tar.gz':
        export_function = export
    else:
        print >> sys.stderr, 'invalid --archive-format value {}'.format(
            archive_format)
        sys.exit(1)

    try:
        export_function(
            what=what_list, input_forward=input_forward,
            create_reversed=create_reversed,
            return_reversed=return_reversed,
            call_reversed=call_reversed, outfile=outfile,
            overwrite=overwrite, **additional_kwargs
        )

    except IOError as e:
        print >> sys.stderr, 'IOError: {}'.format(e.message)
        sys.exit(1)


@export.command('migrate', context_settings=CONTEXT_SETTINGS)
@click.argument('file_input', type=click.Path(exists=True))
@click.argument('file_output', type=click.Path())
@click.option('-f', '--force', is_flag=True, default=False, help='overwrite output file if it already exists')
@click.option('-s', '--silent', is_flag=True, default=False, help='suppress output')
@click.option('-a', '--archive-format', type=click.Choice(['zip', 'zip-uncompressed', 'tar.gz']), default='zip')
def migrate(file_input, file_output, force, silent, archive_format):
    """
    An entry point to migrate existing AiiDA export archives between version numbers
    """
    import os, json, sys
    import tarfile, zipfile
    from aiida.common.folders import SandboxFolder
    from aiida.common.archive import extract_zip, extract_tar

    if os.path.exists(file_output) and not force:
        print >> sys.stderr, 'Error: the output file already exists'
        sys.exit(2)

    with SandboxFolder(sandbox_in_repo=False) as folder:

        if zipfile.is_zipfile(file_input):
            extract_zip(file_input, folder, silent=silent)
        elif tarfile.is_tarfile(file_input):
            extract_tar(file_input, folder, silent=silent)
        else:
            print >> sys.stderr, 'Error: invalid file format, expected either a zip archive or gzipped tarball'
            sys.exit(2)

        try:
            with open(folder.get_abs_path('data.json')) as f:
                data = json.load(f)
            with open(folder.get_abs_path('metadata.json')) as f:
                metadata = json.load(f)
        except IOError as e:
            raise ValueError('export archive does not contain the required file {}'.format(e.filename))

        old_version = verify_metadata_version(metadata)

        try:
            if old_version == '0.1':
                migrate_v1_to_v2(metadata, data)
            elif old_version == '0.2':
                try:
                    migrate_v2_to_v3(metadata, data)
                except DanglingLinkError as e:
                    print "An exception occured!"
                    print e
                    raise RuntimeError("You're export file is broken because it contains dangling links")
            else:
                raise ValueError('cannot migrate from version {}'.format(old_version))
        except ValueError as exception:
            print >> sys.stderr, 'Error:', exception
            sys.exit(2)

        new_version = verify_metadata_version(metadata)

        with open(folder.get_abs_path('data.json'), 'w') as f:
            json.dump(data, f)

        with open(folder.get_abs_path('metadata.json'), 'w') as f:
            json.dump(metadata, f)

        if archive_format == 'zip' or archive_format == 'zip-uncompressed':
            compression = zipfile.ZIP_DEFLATED if archive_format == 'zip' else zipfile.ZIP_STORED
            with zipfile.ZipFile(file_output, mode='w', compression=compression, allowZip64=True) as archive:
                src = folder.abspath
                for dirpath, dirnames, filenames in os.walk(src):
                    relpath = os.path.relpath(dirpath, src)
                    for fn in dirnames + filenames:
                        real_src = os.path.join(dirpath,fn)
                        real_dest = os.path.join(relpath,fn)
                        archive.write(real_src, real_dest)
        elif archive_format == 'tar.gz':
            with tarfile.open(file_output, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as archive:
                archive.add(folder.abspath, arcname='')

        if not silent:
            print 'Successfully migrated the archive from version {} to {}'.format(old_version, new_version)


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
        raise ValueError('expected export file with version {} but found version {}'
            .format(version, metadata_version))

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
    except ValueError:
        raise

    def get_new_string(old_string):
        if old_string.startswith(old_start):
            return "{}{}".format(new_start, old_string[len(old_start):])
        else:
            return old_string

    def replace_requires(data):
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.iteritems():
                if k == 'requires' and v.startswith(old_start):
                    new_data[k] = get_new_string(v)
                else:
                    new_data[k] = replace_requires(v)
            return new_data
        else:
            return data

    for field in ['export_data']: 
        for k in list(data[field]):
            if k.startswith(old_start):
                new_k = get_new_string(k)
                data[field][new_k] = data[field][k]
                del data[field][k]

    for field in ['unique_identifiers', 'all_fields_info']: 
        for k in list(metadata[field].keys()):
            if k.startswith(old_start):
                new_k = get_new_string(k)
                metadata[field][new_k] = metadata[field][k]
                del metadata[field][k]

    metadata['all_fields_info'] = replace_requires(metadata['all_fields_info'])


def migrate_v2_to_v3(metadata, data):
    """
    Migration of export files from v0.2 to v0.3, which means adding the link
    types to the link entries and making the entity key names backend agnostic
    by effectively removing the prefix 'aiida.backends.djsite.db.models'

    :param data: the content of an export archive data.json file
    :param metadata: the content of an export archive metadata.json file
    """
    import json
    import enum
    from aiida.common.links import LinkType

    old_version = '0.2'
    new_version = '0.3'

    class NodeType(enum.Enum):
        """
        A simple enum of relevant node types
        """
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
    except ValueError:
        raise

    # Create a mapping from node uuid to node type
    mapping = {}
    for category, nodes in data['export_data'].iteritems():
        for pk, node in nodes.iteritems():

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
            raise DanglingLinkError('Unknown node UUID {} or {}'.format(link['input'],link['output']))

        # The following table demonstrates the logic for infering the link type
        # (CODE, DATA) -> (WORK, CALC) : INPUT
        # (CALC)       -> (DATA)       : CREATE
        # (WORK)       -> (DATA)       : RETURN
        # (WORK)       -> (CALC, WORK) : CALL
        if (input_type == NodeType.CODE or input_type == NodeType.DATA) \
            and (output_type == NodeType.CALC or output_type == NodeType.WORK):
            link['type'] = LinkType.INPUT.value
        elif input_type == NodeType.CALC and output_type == NodeType.DATA:
            link['type'] = LinkType.CREATE.value
        elif input_type == NodeType.WORK and output_type == NodeType.DATA:
            link['type'] = LinkType.RETURN.value
        elif input_type == NodeType.WORK \
            and (output_type == NodeType.CALC or output_type == NodeType.WORK):
            link['type'] = LinkType.CALL.value
        else:
            link['type'] = LinkType.UNSPECIFIED.value


    # Now we migrate the entity key names i.e. removing the 'aiida.backends.djsite.db.models' prefix
    for field in ['unique_identifiers', 'all_fields_info']:
        for old_key, new_key in entity_map.iteritems():
            if old_key in metadata[field]:
                metadata[field][new_key] = metadata[field][old_key]
                del metadata[field][old_key]

    # Replace the 'requires' keys in the nested dictionaries in 'all_fields_info'
    for entity in metadata['all_fields_info'].values():
        for prop in entity.values():
            for key, value in prop.iteritems():
                if key == 'requires' and value in entity_map:
                    prop[key] = entity_map[value]

    # Replace any present keys in the data.json
    for field in ['export_data']:
        for old_key, new_key in entity_map.iteritems():
            if old_key in data[field]:
                data[field][new_key] = data[field][old_key]
                del data[field][old_key]
