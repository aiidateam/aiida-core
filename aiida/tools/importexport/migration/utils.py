# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for migration of export-files."""

from aiida.tools.importexport.common import exceptions


def verify_metadata_version(metadata, version=None):
    """Utility function to verify that the metadata has the correct version number.

    If no version number is passed, it will just extract the version number and return it.

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the metadata is expected to have
    """
    try:
        metadata_version = metadata['export_version']
    except KeyError:
        raise exceptions.ArchiveMigrationError("metadata is missing the 'export_version' key")

    if version is None:
        return metadata_version

    if metadata_version != version:
        raise exceptions.MigrationValidationError(
            f'expected archive file with version {version} but found version {metadata_version}'
        )

    return None


def update_metadata(metadata, version):
    """Update the metadata with a new version number and a notification of the conversion that was executed.

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the updated metadata should get
    """
    from aiida import get_version

    old_version = metadata['export_version']
    conversion_info = metadata.get('conversion_info', [])

    conversion_message = f'Converted from version {old_version} to {version} with AiiDA v{get_version()}'
    conversion_info.append(conversion_message)

    metadata['aiida_version'] = get_version()
    metadata['export_version'] = version
    metadata['conversion_info'] = conversion_info


def remove_fields(metadata, data, entities, fields):
    """Remove fields under entities from data.json and metadata.json.

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    :param entities: list of ORM entities
    :param fields: list of fields to be removed from the export archive files
    """
    # data.json
    for entity in entities:
        for content in data['export_data'].get(entity, {}).values():
            for field in fields:
                content.pop(field, None)

    # metadata.json
    for entity in entities:
        for field in fields:
            metadata['all_fields_info'][entity].pop(field, None)
