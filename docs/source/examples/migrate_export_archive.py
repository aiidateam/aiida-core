#!/usr/bin/env python

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
    old_version = metadata['export_version']
    conversion_info = metadata.get('conversion_info', [])

    conversion_message = 'Converted from version {} to {} with external script'.format(old_version, version)
    conversion_info.append(conversion_message)

    metadata['export_version'] = version
    metadata['conversion_info'] = conversion_info

def migrate_v2_to_v3(metadata, data):
    """
    Migration of export files from v2 to v3, which means adding the link
    types to the link entries

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
            raise RuntimeError('Unknown node UUID')

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


if __name__ == '__main__':
    import argparse, os, json, sys
    import tarfile, zipfile
    from aiida.common.folders import SandboxFolder
    from aiida.common.archive import extract_tree, extract_zip, extract_tar

    parser = argparse.ArgumentParser(description='Migrate an AiiDA export archive file')
    parser.add_argument('file_input', help='filepath to the input export file')
    parser.add_argument('file_output', help='filepath to where the migrated export file is written')
    parser.add_argument('-f', action='store_true', dest='force', default=False, help='overwrite output file if it already exists')
    parser.add_argument('-s', action='store_true', dest='silent', default=False, help='suppress output')
    args = parser.parse_args()

    if os.path.exists(args.file_output) and not args.force:
        print >> sys.stderr, 'Error: the output file already exists'
        sys.exit(2)

    with SandboxFolder() as folder:

        if tarfile.is_tarfile(args.file_input):
            extract_tar(args.file_input, folder, silent=args.silent)
        else:
            raise ValueError('invalid archive format, expected .tar.gz AiiDA export file')

        try:
            with open(folder.get_abs_path('data.json')) as f:
                data = json.load(f)
            with open(folder.get_abs_path('metadata.json')) as f:
                metadata = json.load(f)
        except IOError as e:
            raise ValueError('export archive does not contain the required file {}'.format(e.filename))

        old_version = verify_metadata_version(metadata)

        try:
            if old_version == '0.2':
                migrate_v2_to_v3(metadata, data)
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

        with tarfile.open(args.file_output, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as tar:
            tar.add(folder.abspath, arcname='')

        if not args.silent:
            print 'Successfully migrated the archive from version {} to {}'.format(old_version, new_version)