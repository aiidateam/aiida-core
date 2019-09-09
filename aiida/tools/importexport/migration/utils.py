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


def verify_archive_version(archive_version, version):
    """Utility function to verify that the archive has the correct version number.

    :param archive_version: the version from an export archive metadata.json file
    :type archive_version: str
    :param version: version number that the archive is expected to have
    :type version: str
    """
    from aiida.tools.importexport.common.exceptions import MigrationValidationError

    if not isinstance(archive_version, str) or not isinstance(version, str):
        raise MigrationValidationError('Only strings are accepted for "verify_archive_version"')
    if archive_version != version:
        raise MigrationValidationError(
            'expected export file with version {} but found version {}'.format(version, archive_version)
        )


def update_metadata(metadata, version):
    """Update the metadata with a new version number and a notification of the conversion that was executed.

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the updated metadata should get
    """
    from aiida import get_version

    old_version = metadata['export_version']
    conversion_info = metadata.get('conversion_info', [])

    conversion_message = 'Converted from version {} to {} with AiiDA v{}'.format(old_version, version, get_version())
    conversion_info.append(conversion_message)

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
