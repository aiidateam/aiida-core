# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Utility functions for import of AiiDA entities """
# pylint: disable=inconsistent-return-statements,too-many-branches
import click

from aiida.orm import QueryBuilder, Comment
from aiida.common.utils import get_new_uuid
from aiida.tools.importexport.common import exceptions


def merge_comment(incoming_comment, comment_mode):
    """ Merge comment according comment_mode
    :return: New UUID if new Comment should be created, else None.
    """

    # Get incoming Comment's UUID, 'mtime', and 'comment'
    incoming_uuid = str(incoming_comment['uuid'])
    incoming_mtime = incoming_comment['mtime']
    incoming_content = incoming_comment['content']

    # Compare modification time 'mtime'
    if comment_mode == 'newest':
        # Get existing Comment's 'mtime' and 'content'
        builder = QueryBuilder().append(Comment, filters={'uuid': incoming_uuid}, project=['mtime', 'content'])
        if builder.count() != 1:
            raise exceptions.ImportValidationError('Multiple Comments with the same UUID: {}'.format(incoming_uuid))
        builder = builder.all()

        existing_mtime = builder[0][0]
        existing_content = builder[0][1]

        # Existing Comment is "newer" than imported Comment: KEEP existing
        if existing_mtime > incoming_mtime:
            return None

        # Existing Comment is "older" than imported Comment: OVERWRITE existing
        if existing_mtime < incoming_mtime:
            cmt = Comment.objects.get(uuid=incoming_uuid)
            cmt.set_content(incoming_content)
            cmt.set_mtime(incoming_mtime)
            return None

        # Existing Comment has the same modification time as the imported Comment
        # Check content. If the same, ignore Comment. If different, add as new Comment.
        if existing_mtime == incoming_mtime:
            if existing_content == incoming_content:
                # Ignore
                return None

            # ELSE: Add it as a new comment
            return get_new_uuid()

    # Overwrite existing Comment
    elif comment_mode == 'overwrite':
        cmt = Comment.objects.get(uuid=incoming_uuid)
        cmt.set_content(incoming_content)
        cmt.set_mtime(incoming_mtime)
        return None

    # Invalid comment_mode
    else:
        raise exceptions.ImportValidationError(
            'Unknown comment_mode value: {}. Should be '
            "either 'newest' or 'overwrite'".format(comment_mode)
        )


def merge_extras(old_extras, new_extras, mode):
    """
    :param old_extras: a dictionary containing the old extras of an already existing node
    :param new_extras: a dictionary containing the new extras of an imported node
    :param extras_mode_existing: 3 letter code that will identify what to do with the extras import.
        The first letter acts on extras that are present in the original node and not present
        in the imported node. Can be either k (keep it) or n (do not keep it).
        The second letter acts on the imported extras that are not present in the original node.
        Can be either c (create it) or n (do not create it). The third letter says what to do
        in case of a name collision. Can be l (leave the old value), u (update with a new value),
        d (delete the extra), a (ask what to do if the content is different).
    """
    if not isinstance(mode, str):
        raise exceptions.ImportValidationError(
            "Parameter 'mode' should be of string type, you provided '{}' type".format(type(mode))
        )
    elif not len(mode) == 3:
        raise exceptions.ImportValidationError(
            "Parameter 'mode' should be a 3-letter string, you provided: '{}'".format(mode)
        )

    old_keys = set(old_extras.keys())
    new_keys = set(new_extras.keys())

    collided_keys = old_keys.intersection(new_keys)
    old_keys_only = old_keys.difference(collided_keys)
    new_keys_only = new_keys.difference(collided_keys)

    final_extras = {}

    # Fast implementations for the common operations:
    if mode == 'ncu':  # 'mirror' operation: remove old extras, put only the new ones
        return new_extras

    if mode == 'knl':  # 'none': keep old extras, do not add imported ones
        return old_extras

    if mode == 'kcu':  # 'update_existing' operation: if an extra already exists,
        # overwrite its new value with a new one
        final_extras = new_extras
        for key in old_keys_only:
            final_extras[key] = old_extras[key]

    elif mode == 'kcl':  # 'keep_existing': if an extra already exists, keep its original value
        final_extras = old_extras
        for key in new_keys_only:
            final_extras[key] = new_extras[key]

    elif mode == 'kca':  # 'ask': if an extra already exists ask a user whether to update its value
        final_extras = old_extras
        for key in new_keys_only:
            final_extras[key] = new_extras[key]
        for key in collided_keys:
            if old_extras[key] != new_extras[key]:
                if click.confirm(
                    'The extra {} collided, would you'
                    ' like to overwrite its value?\nOld value: {}\nNew value: {}\n'.format(
                        key, old_extras[key], new_extras[key]
                    )
                ):
                    final_extras[key] = new_extras[key]

    # Slow, but more general implementation
    else:
        if mode[0] == 'k':
            for key in old_keys_only:
                final_extras[key] = old_extras[key]
        elif mode[0] != 'n':
            raise exceptions.ImportValidationError(
                "Unknown first letter of the update extras mode: '{}'. Should be either 'k' or 'n'".format(mode)
            )

        if mode[1] == 'c':
            for key in new_keys_only:
                final_extras[key] = new_extras[key]
        elif mode[1] != 'n':
            raise exceptions.ImportValidationError(
                "Unknown second letter of the update extras mode: '{}'. Should be either 'c' or 'n'".format(mode)
            )

        if mode[2] == 'u':
            for key in collided_keys:
                final_extras[key] = new_extras[key]
        elif mode[2] == 'l':
            for key in collided_keys:
                final_extras[key] = old_extras[key]
        elif mode[2] == 'a':
            for key in collided_keys:
                if old_extras[key] != new_extras[key]:
                    if click.confirm(
                        'The extra {} collided, would you'
                        ' like to overwrite its value?\nOld value: {}\nNew value: {}\n'.format(
                            key, old_extras[key], new_extras[key]
                        )
                    ):
                        final_extras[key] = new_extras[key]
                    else:
                        final_extras[key] = old_extras[key]
        elif mode[2] != 'd':
            raise exceptions.ImportValidationError(
                "Unknown third letter of the update extras mode: '{}'. Should be one of 'u'/'l'/'a'/'d'".format(mode)
            )

    return final_extras


def deserialize_attributes(attributes_data, conversion_data):
    """Deserialize attributes"""
    import datetime
    import pytz

    if isinstance(attributes_data, dict):
        ret_data = {}
        for key, value in attributes_data.items():
            if conversion_data is not None:
                ret_data[key] = deserialize_attributes(value, conversion_data[key])
            else:
                ret_data[key] = deserialize_attributes(value, None)
    elif isinstance(attributes_data, (list, tuple)):
        ret_data = []
        if conversion_data is not None:
            for value, conversion in zip(attributes_data, conversion_data):
                ret_data.append(deserialize_attributes(value, conversion))
        else:
            for value in attributes_data:
                ret_data.append(deserialize_attributes(value, None))
    else:
        if conversion_data is None:
            ret_data = attributes_data
        else:
            if conversion_data == 'date':
                ret_data = datetime.datetime.strptime(attributes_data, '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.utc)
            else:
                raise exceptions.ArchiveImportError("Unknown convert_type '{}'".format(conversion_data))

    return ret_data


def deserialize_field(key, value, fields_info, import_unique_ids_mappings, foreign_ids_reverse_mappings):
    """Deserialize field using deserialize attributes"""
    try:
        field_info = fields_info[key]
    except KeyError:
        raise exceptions.ArchiveImportError("Unknown field '{}'".format(key))

    if key in ('id', 'pk'):
        raise exceptions.ImportValidationError('ID or PK explicitly passed!')

    requires = field_info.get('requires', None)
    if requires is None:
        # Actual data, no foreign key
        converter = field_info.get('convert_type', None)
        return (key, deserialize_attributes(value, converter))

    # Foreign field
    # Correctly manage nullable fields
    if value is not None:
        unique_id = import_unique_ids_mappings[requires][value]
        # map to the PK/ID associated to the given entry, in the arrival DB,
        # rather than in the export DB

        # I store it in the FIELDNAME_id variable, that directly stores the
        # PK in the remote table, rather than requiring to create Model
        # instances for the foreign relations
        return ('{}_id'.format(key), foreign_ids_reverse_mappings[requires][unique_id])

    # else
    return ('{}_id'.format(key), None)
