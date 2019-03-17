# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import io

import click
import six
from six.moves import zip
from six.moves.html_parser import HTMLParser
from distutils.version import StrictVersion
from aiida.common import exceptions
from aiida.common.utils import export_shard_uuid, get_class_string, grouper, get_new_uuid
from aiida.orm import Computer, Group, GroupTypeString, Node, QueryBuilder, User, Log, Comment
from aiida.orm.utils.repository import Repository

IMPORTGROUP_TYPE = GroupTypeString.IMPORTGROUP_TYPE
DUPL_SUFFIX = ' (Imported #{})'

# Giving names to the various entities. Attributes and links are not AiiDA
# entities but we will refer to them as entities in the file (to simplify
# references to them).
NODE_ENTITY_NAME = "Node"
LINK_ENTITY_NAME = "Link"
GROUP_ENTITY_NAME = "Group"
ATTRIBUTE_ENTITY_NAME = "Attribute"
COMPUTER_ENTITY_NAME = "Computer"
USER_ENTITY_NAME = "User"
LOG_ENTITY_NAME = "Log"
COMMENT_ENTITY_NAME = "Comment"

# The signatures used to reference the entities in the import/export file
NODE_SIGNATURE = "aiida.backends.djsite.db.models.DbNode"
LINK_SIGNATURE = "aiida.backends.djsite.db.models.DbLink"
GROUP_SIGNATURE = "aiida.backends.djsite.db.models.DbGroup"
COMPUTER_SIGNATURE = "aiida.backends.djsite.db.models.DbComputer"
USER_SIGNATURE = "aiida.backends.djsite.db.models.DbUser"
ATTRIBUTE_SIGNATURE = "aiida.backends.djsite.db.models.DbAttribute"
LOG_SIGNATURE = "aiida.backends.djsite.db.models.DbLog"
COMMENT_SIGNATURE = "aiida.backends.djsite.db.models.DbComment"

# Mapping from entity names to signatures (used by the SQLA import/export)
entity_names_to_signatures = {
    NODE_ENTITY_NAME: NODE_SIGNATURE,
    LINK_ENTITY_NAME: LINK_SIGNATURE,
    GROUP_ENTITY_NAME: GROUP_SIGNATURE,
    COMPUTER_ENTITY_NAME: COMPUTER_SIGNATURE,
    USER_ENTITY_NAME: USER_SIGNATURE,
    ATTRIBUTE_ENTITY_NAME: ATTRIBUTE_SIGNATURE,
    LOG_ENTITY_NAME: LOG_SIGNATURE,
    COMMENT_ENTITY_NAME: COMMENT_SIGNATURE
}

# Mapping from signatures to entity names (used by the SQLA import/export)
signatures_to_entity_names = {
    NODE_SIGNATURE: NODE_ENTITY_NAME,
    LINK_SIGNATURE: LINK_ENTITY_NAME,
    GROUP_SIGNATURE: GROUP_ENTITY_NAME,
    COMPUTER_SIGNATURE: COMPUTER_ENTITY_NAME,
    USER_SIGNATURE: USER_ENTITY_NAME,
    ATTRIBUTE_SIGNATURE: ATTRIBUTE_ENTITY_NAME,
    LOG_SIGNATURE: LOG_ENTITY_NAME,
    COMMENT_SIGNATURE: COMMENT_ENTITY_NAME
}

# Mapping from entity names to AiiDA classes (used by the SQLA import/export)
entity_names_to_entities = {
    NODE_ENTITY_NAME: Node,
    GROUP_ENTITY_NAME: Group,
    COMPUTER_ENTITY_NAME: Computer,
    USER_ENTITY_NAME: User,
    LOG_ENTITY_NAME: Log,
    COMMENT_ENTITY_NAME: Comment
}


def schema_to_entity_names(class_string):
    """
    Mapping from classes path to entity names (used by the SQLA import/export)
    This could have been written much simpler if it is only for SQLA but there
    is an attempt the SQLA import/export code to be used for Django too.
    """
    if class_string is None or len(class_string) == 0:
        return

    if (class_string == "aiida.backends.djsite.db.models.DbNode" or
            class_string == "aiida.backends.sqlalchemy.models.node.DbNode"):
        return NODE_ENTITY_NAME

    if (class_string == "aiida.backends.djsite.db.models.DbLink" or
            class_string == "aiida.backends.sqlalchemy.models.node.DbLink"):
        return LINK_ENTITY_NAME

    if (class_string == "aiida.backends.djsite.db.models.DbGroup" or
            class_string ==
            "aiida.backends.sqlalchemy.models.group.DbGroup"):
        return GROUP_ENTITY_NAME

    if (class_string == "aiida.backends.djsite.db.models.DbComputer" or
            class_string ==
            "aiida.backends.sqlalchemy.models.computer.DbComputer"):
        return COMPUTER_ENTITY_NAME

    if (class_string == "aiida.backends.djsite.db.models.DbUser" or
            class_string == "aiida.backends.sqlalchemy.models.user.DbUser"):
        return USER_ENTITY_NAME

    if (class_string == "aiida.backends.djsite.db.models.DbLog" or
            class_string == "aiida.backends.sqlalchemy.models.log.DbLog"):
        return LOG_ENTITY_NAME

    if (class_string == "aiida.backends.djsite.db.models.DbComment" or
            class_string == "aiida.backends.sqlalchemy.models.comment.DbComment"):
        return COMMENT_ENTITY_NAME


# Mapping of entity names to SQLA class paths
entity_names_to_sqla_schema = {
    NODE_ENTITY_NAME: "aiida.backends.sqlalchemy.models.node.DbNode",
    LINK_ENTITY_NAME: "aiida.backends.sqlalchemy.models.node.DbLink",
    GROUP_ENTITY_NAME: "aiida.backends.sqlalchemy.models.group.DbGroup",
    COMPUTER_ENTITY_NAME: "aiida.backends.sqlalchemy.models.computer.DbComputer",
    USER_ENTITY_NAME: "aiida.backends.sqlalchemy.models.user.DbUser",
    LOG_ENTITY_NAME: "aiida.backends.sqlalchemy.models.log.DbLog",
    COMMENT_ENTITY_NAME: "aiida.backends.sqlalchemy.models.comment.DbComment"
}

# Mapping of the export file fields (that coincide with the Django fields) to
# model fields that can be used for the query of the database in both backends.
# These are the names of the fields of the models that belong to the
# corresponding entities.
file_fields_to_model_fields = {
    NODE_ENTITY_NAME: {
        "dbcomputer": "dbcomputer_id",
        "user": "user_id"
    },
    GROUP_ENTITY_NAME: {
        "user": "user_id"
    },
    COMPUTER_ENTITY_NAME: {
        "metadata": "_metadata"
    },
    LOG_ENTITY_NAME: {
        "dbnode": "dbnode_id",
        "metadata": "_metadata"
    },
    COMMENT_ENTITY_NAME: {
        "dbnode": "dbnode_id",
        "user": "user_id"
    }
}

# As above but the opposite procedure
model_fields_to_file_fields = {
    NODE_ENTITY_NAME: {
        "dbcomputer_id": "dbcomputer",
        "user_id": "user"
    },
    LINK_ENTITY_NAME: {},
    GROUP_ENTITY_NAME: {
        "user_id": "user"
    },
    COMPUTER_ENTITY_NAME: {
        "_metadata": "metadata"
    },
    USER_ENTITY_NAME: {},
    LOG_ENTITY_NAME: {
        "dbnode_id": "dbnode",
        "_metadata": "metadata"
    },
    COMMENT_ENTITY_NAME: {
        "dbnode_id": "dbnode",
        "user_id": "user"
    }
}


def get_all_fields_info():
    """
    This method returns a description of the field names that should be used
    to describe the entity properties.
    Apart from of the listing of the fields per properties, it also shown
    the dependencies among different entities (and on which fields). It is
    also shown/return the unique identifiers used per entity.

    """
    unique_identifiers = {
        USER_ENTITY_NAME: "email",
        COMPUTER_ENTITY_NAME: "uuid",
        LINK_ENTITY_NAME: None,
        NODE_ENTITY_NAME: "uuid",
        ATTRIBUTE_ENTITY_NAME: None,
        GROUP_ENTITY_NAME: "uuid",
        LOG_ENTITY_NAME: "uuid",
        COMMENT_ENTITY_NAME: "uuid"
    }

    all_fields_info = dict()
    all_fields_info[USER_ENTITY_NAME] = {
        "last_name": {},
        "first_name": {},
        "institution": {},
        "email": {}
    }
    all_fields_info[COMPUTER_ENTITY_NAME] = {
        "transport_type": {},
        "transport_params": {},
        "hostname": {},
        "description": {},
        "scheduler_type": {},
        "metadata": {},
        "enabled": {},
        "uuid": {},
        "name": {}
    }
    all_fields_info[LINK_ENTITY_NAME] = {
        "input": {
            "requires": NODE_ENTITY_NAME,
            "related_name": "output_links"
        },
        "type": {},
        "output": {
            "requires": NODE_ENTITY_NAME,
            "related_name": "input_links"
        },
        "label": {}
    }
    all_fields_info[NODE_ENTITY_NAME] = {
        "ctime": {
            "convert_type": "date"
        },
        "uuid": {},
        "public": {},
        "mtime": {
            "convert_type": "date"
        },
        "node_type": {},
        "label": {},
        "nodeversion": {},
        "user": {
            "requires": USER_ENTITY_NAME,
            "related_name": "dbnodes"
        },
        "dbcomputer": {
            "requires": COMPUTER_ENTITY_NAME,
            "related_name": "dbnodes"
        },
        "description": {},
        "process_type": {}
    }
    all_fields_info[ATTRIBUTE_ENTITY_NAME] = {
        "dbnode": {
            "requires": NODE_ENTITY_NAME,
            "related_name": "dbattributes"
        },
        "key": {},
        "tval": {},
        "fval": {},
        "bval": {},
        "datatype": {},
        "dval": {
            "convert_type": "date"
        },
        "ival": {}
    }
    all_fields_info[GROUP_ENTITY_NAME] = {
         "description": {},
         "user": {
            "related_name": "dbgroups",
            "requires": USER_ENTITY_NAME
         },
         "time": {
            "convert_type": "date"
         },
         "type_string": {},
         "uuid": {},
         "label": {}
    }
    all_fields_info[LOG_ENTITY_NAME] = {
         "uuid": {},
         "time": {
             "convert_type": "date"
         },
         "loggername": {},
         "levelname": {},
         "message": {},
         "metadata": {},
         "dbnode": {
             "related_name": "dblogs",
             "requires": NODE_ENTITY_NAME
         }
    }
    all_fields_info[COMMENT_ENTITY_NAME] = {
         "uuid": {},
         "ctime": {
             "convert_type": "date"
         },
         "mtime": {
             "convert_type": "date"
         },
         "content": {},
         "dbnode": {
             "related_name": "dbcomments",
             "requires": NODE_ENTITY_NAME
         },
         "user": {
             "related_name": "dbcomments",
             "requires": USER_ENTITY_NAME
         }
    }
    return all_fields_info, unique_identifiers


def deserialize_attributes(attributes_data, conversion_data):
    import datetime
    import pytz

    if isinstance(attributes_data, dict):
        ret_data = {}
        for k, v in attributes_data.items():
            # print("k: ", k, " v: ", v)
            if conversion_data is not None:
                ret_data[k] = deserialize_attributes(v, conversion_data[k])
            else:
                ret_data[k] = deserialize_attributes(v, None)
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
                ret_data = datetime.datetime.strptime(
                    attributes_data, '%Y-%m-%dT%H:%M:%S.%f').replace(
                    tzinfo=pytz.utc)
            else:
                raise ValueError("Unknown convert_type '{}'".format(
                    conversion_data))

    return ret_data


def deserialize_field(k, v, fields_info, import_unique_ids_mappings,
                      foreign_ids_reverse_mappings):
    try:
        field_info = fields_info[k]
    except KeyError:
        raise ValueError("Unknown field '{}'".format(k))

    if k == 'id' or k == 'pk':
        raise ValueError("ID or PK explicitly passed!")

    requires = field_info.get('requires', None)
    if requires is None:
        # Actual data, no foreign key
        converter = field_info.get('convert_type', None)
        return (k, deserialize_attributes(v, converter))
    else:
        # Foreign field
        # Correctly manage nullable fields
        if v is not None:
            unique_id = import_unique_ids_mappings[requires][v]
            # map to the PK/ID associated to the given entry, in the arrival DB,
            # rather than in the export DB

            # I store it in the FIELDNAME_id variable, that directly stores the
            # PK in the remote table, rather than requiring to create Model
            # instances for the foreign relations
            return ("{}_id".format(k),
                    foreign_ids_reverse_mappings[requires][unique_id])
        else:
            return ("{}_id".format(k), None)

def merge_extras(old_extras, new_extras, mode):
    """
    :param old_extras: a dictionary containing the old extras of an already existing node
    :param new_extras: a dictionary containing the new extras of an imported node
    :param extras_mode_existing: 3 letter code that will identify what to do with the extras import. The first letter acts on
                        extras that are present in the original node and not present in the imported node. Can be
                        either k (keep it) or n (do not keep it). The second letter acts on the imported extras that
                        are not present in the original node. Can be either c (create it) or n (do not create it). The
                        third letter says what to do in case of a name collision. Can be l (leave the old value), u
                        (update with a new value), d (delete the extra), a (ask what to do if the content is
                        different).
    """
    from six import string_types
    if not isinstance(mode, string_types):
        raise TypeError("Parameter 'mode' should be of string type, you provided '{}' type".format(type(mode)))
    elif not len(mode) == 3:
        raise ValueError("Parameter 'mode' should be a 3-letter string, you provided: '{}'".format(mode))

    old_keys = set(old_extras.keys())
    new_keys = set(new_extras.keys())

    collided_keys = old_keys.intersection(new_keys)
    old_keys_only = old_keys.difference(collided_keys)
    new_keys_only = new_keys.difference(collided_keys)

    final_extras = {}

    # Fast implementations for the common operations:
    if mode == 'ncu': # 'mirror' operation: remove old extras, put only the new ones
        return new_extras

    if mode == 'knl': # 'none': keep old extras, do not add imported ones
        return old_extras

    if mode == 'kcu': # 'update_existing' operation: if an extra already exists,
                      # overwrite its new value with a new one
        final_extras = new_extras
        for key in old_keys_only:
            final_extras[key] = old_extras[key]

    elif mode == 'kcl': # 'keep_existing': if an extra already exists, keep its original value
        final_extras = old_extras
        for key in new_keys_only:
            final_extras[key] = new_extras[key]

    elif mode == 'kca': # 'ask': if an extra already exists ask a user whether to update its value
        final_extras = old_extras
        for key in new_keys_only:
            final_extras[key] = new_extras[key]
        for key in collided_keys:
            if old_extras[key] != new_extras[key]:
                if click.confirm('The extra {} collided, would you'
                        ' like to overwrite its value?\nOld value: {}\nNew value: {}\n'.format(key,
                            old_extras[key], new_extras[key])):
                    final_extras[key] = new_extras[key]

    # Slow, but more general implementation
    else:
        if mode[0] == 'k':
            for key in old_keys_only:
                final_extras[key] = old_extras[key]
        elif mode[0] != 'n':
            raise ValueError("Unknown first letter of the update extras mode: '{}'. " \
                             "Should be either 'k' or 'n'".format(mode))

        if mode[1] == 'c':
            for key in new_keys_only:
                final_extras[key] = new_extras[key]
        elif mode[1] != 'n':
            raise ValueError("Unknown second letter of the update extras mode: '{}'. " \
                             "Should be either 'c' or 'n'".format(mode))

        if mode[2] == 'u':
            for key in collided_keys:
                final_extras[key] = new_extras[key]
        elif mode[2] == 'l':
            for key in collided_keys:
                final_extras[key] = old_extras[key]
        elif mode[2] == 'a':
            for key in collided_keys:
                if old_extras[key] != new_extras[key]:
                    if click.confirm('The extra {} collided, would you'
                            ' like to overwrite its value?\nOld value: {}\nNew value: {}\n'.format(key,
                                old_extras[key], new_extras[key])):
                        final_extras[key] = new_extras[key]
                    else:
                        final_extras[key] = old_extras[key]
        elif mode[2] != 'd':
            raise ValueError("Unknown third letter of the update extras mode: '{}'. " \
                             "Should be one of 'u'/'l'/'a'/'d'".format(mode))

    return final_extras


def _merge_comment(incoming_comment, comment_mode):
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
        builder = QueryBuilder().append(Comment,
            filters={'uuid': incoming_uuid},
            project=['mtime', 'content'])
        if builder.count() != 1:
            raise exceptions.ValidationError("Multiple Comments with the same "
                                             "UUID: {}".format(incoming_uuid))
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
        raise ValueError("Unknown comment_mode value: {}. Should be "
                         "either 'newest' or 'overwrite'".format(comment_mode))


def import_data(in_path, group=None, silent=False, **kwargs):
    """
    Import exported AiiDA environment to the AiiDA database.
    If the 'in_path' is a folder, calls extract_tree; otherwise, tries to
    detect the compression format (zip, tar.gz, tar.bz2, ...) and calls the
    correct function.
    :param in_path: the path to a file or folder that can be imported in AiiDA
    :param extras_mode_existing: 3 letter code that will identify what to do with the extras import.
    The first letter acts on extras that are present in the original node and not present in the imported node.
    Can be either:
    'k' (keep it) or
    'n' (do not keep it).
    The second letter acts on the imported extras that are not present in the original node.
    Can be either:
    'c' (create it) or
    'n' (do not create it).
    The third letter defines what to do in case of a name collision.
    Can be either:
    'l' (leave the old value),
    'u' (update with a new value),
    'd' (delete the extra),
    'a' (ask what to do if the content is different).
    :param extras_mode_new: 'import' to import extras of new nodes or 'none' to ignore them
    :param comment_node_existing: Similar to param extras_mode_existing, but for Comments.
    :param comment_mode_new: Similar to param extras_mode_new, but for Comments.
    """
    from aiida.backends.settings import BACKEND
    from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA

    if BACKEND == BACKEND_SQLA:
        return import_data_sqla(in_path, user_group=group, silent=silent, **kwargs)
    elif BACKEND == BACKEND_DJANGO:
        return import_data_dj(in_path, user_group=group, silent=silent, **kwargs)
    else:
        raise Exception("Unknown settings.BACKEND: {}".format(
            BACKEND))


def import_data_dj(in_path, user_group=None, ignore_unknown_nodes=False,
                   extras_mode_existing='kcl', extras_mode_new='import',
                   comment_mode='newest', silent=False):
    """
    Import exported AiiDA environment to the AiiDA database.
    If the 'in_path' is a folder, calls extract_tree; otherwise, tries to
    detect the compression format (zip, tar.gz, tar.bz2, ...) and calls the
    correct function.
    :param in_path: the path to a file or folder that can be imported in AiiDA
    :param extras_mode_existing: 3 letter code that will identify what to do with the extras import.
    The first letter acts on extras that are present in the original node and not present in the imported node.
    Can be either:
    'k' (keep it) or
    'n' (do not keep it).
    The second letter acts on the imported extras that are not present in the original node.
    Can be either:
    'c' (create it) or
    'n' (do not create it).
    The third letter defines what to do in case of a name collision.
    Can be either:
    'l' (leave the old value),
    'u' (update with a new value),
    'd' (delete the extra),
    'a' (ask what to do if the content is different).
    :param extras_mode_new: 'import' to import extras of new nodes or 'none' to ignore them
    :param comment_mode: Comment import modes (when same UUIDs are found):
    'newest': Will keep the Comment with the most recent modification time (mtime)
    'overwrite': Will overwrite existing Comments with the ones from the import file
    """
    import os
    import tarfile
    import zipfile
    from itertools import chain

    from django.db import transaction
    from aiida.common import timezone

    from aiida.common.archive import extract_tree, extract_tar, extract_zip
    from aiida.common.links import LinkType
    from aiida.common.folders import SandboxFolder, RepositoryFolder
    from aiida.backends.djsite.db import models
    from aiida.common.utils import get_object_from_string
    from aiida.common import json
    from aiida.backends.djsite.db.models import suppress_auto_now

    # This is the export version expected by this function
    expected_export_version = StrictVersion('0.4')

    # The name of the subfolder in which the node files are stored
    nodes_export_subfolder = 'nodes'

    # The returned dictionary with new and existing nodes and links
    ret_dict = {}

    ################
    # EXTRACT DATA #
    ################
    # The sandbox has to remain open until the end
    with SandboxFolder() as folder:
        if os.path.isdir(in_path):
            extract_tree(in_path, folder)
        else:
            if tarfile.is_tarfile(in_path):
                extract_tar(in_path, folder, silent=silent,
                            nodes_export_subfolder=nodes_export_subfolder)
            elif zipfile.is_zipfile(in_path):
                try:
                    extract_zip(in_path, folder, silent=silent,
                                nodes_export_subfolder=nodes_export_subfolder)
                except ValueError as exc:
                    print("The following problem occured while processing the "
                          "provided file: {}".format(exc))
                    return
            else:
                raise ValueError("Unable to detect the input file format, it "
                                 "is neither a (possibly compressed) tar file, "
                                 "nor a zip file.")

        if not folder.get_content_list():
            from aiida.common.exceptions import ContentNotExistent
            raise ContentNotExistent("The provided file/folder ({}) is empty"
                                     .format(in_path))
        try:
            with io.open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)

            with io.open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                data = json.load(fhandle)
        except IOError as e:
            raise ValueError("Unable to find the file {} in the import "
                             "file or folder".format(e.filename))

        ######################
        # PRELIMINARY CHECKS #
        ######################
        export_version = StrictVersion(str(metadata['export_version']))
        if export_version != expected_export_version:
            msg = "Export file version is {}, can import only version {}"\
                    .format(metadata['export_version'], expected_export_version)
            if export_version < expected_export_version:
                msg += "\nUse 'verdi export migrate' to update this export file."
            else:
                msg += "\nUpdate your AiiDA version in order to import this file."

            raise exceptions.IncompatibleArchiveVersionError(msg)

        ##########################################################################
        # CREATE UUID REVERSE TABLES AND CHECK IF I HAVE ALL NODES FOR THE LINKS #
        ##########################################################################
        linked_nodes = set(chain.from_iterable((l['input'], l['output'])
                                               for l in data['links_uuid']))
        group_nodes = set(chain.from_iterable(six.itervalues(data['groups_uuid'])))

        # I preload the nodes, I need to check each of them later, and I also
        # store them in a reverse table
        # I break up the query due to SQLite limitations..
        relevant_db_nodes = {}
        for group in grouper(999, linked_nodes):
            relevant_db_nodes.update({n.uuid: n for n in
                                      models.DbNode.objects.filter(
                                          uuid__in=group)})

        db_nodes_uuid = set(relevant_db_nodes.keys())
        # ~ dbnode_model = get_class_string(models.DbNode)
        # ~ print(dbnode_model)
        if NODE_ENTITY_NAME in data['export_data']:
            import_nodes_uuid = set(v['uuid'] for v in data['export_data'][NODE_ENTITY_NAME].values())
        else:
            import_nodes_uuid = set()

        # the combined set of linked_nodes and group_nodes was obtained from looking at all the links
        # the combined set of db_nodes_uuid and import_nodes_uuid was received from the staff
        # actually referred to in export_data
        unknown_nodes = linked_nodes.union(group_nodes) - db_nodes_uuid.union(
            import_nodes_uuid)

        if unknown_nodes and not ignore_unknown_nodes:
            raise ValueError(
                "The import file refers to {} nodes with unknown UUID, therefore "
                "it cannot be imported. Either first import the unknown nodes, "
                "or export also the parents when exporting. The unknown UUIDs "
                "are:\n".format(len(unknown_nodes)) +
                "\n".join('* {}'.format(uuid) for uuid in unknown_nodes))

        ###################################
        # DOUBLE-CHECK MODEL DEPENDENCIES #
        ###################################
        # I hardcode here the model order, for simplicity; in any case, this is
        # fixed by the export version

        model_order = (USER_ENTITY_NAME, COMPUTER_ENTITY_NAME, NODE_ENTITY_NAME,
                      GROUP_ENTITY_NAME, LOG_ENTITY_NAME, COMMENT_ENTITY_NAME)
        # Models that do appear in the import file, but whose import is managed manually
        model_manual = (LINK_ENTITY_NAME, ATTRIBUTE_ENTITY_NAME)

        all_known_models = model_order + model_manual

        for import_field_name in metadata['all_fields_info']:
            if import_field_name not in all_known_models:
                raise NotImplementedError("Apparently, you are importing a "
                                          "file with a model '{}', but this does not appear in "
                                          "all_known_models!".format(import_field_name))

        for idx, model_name in enumerate(model_order):
            dependencies = []
            for field in metadata['all_fields_info'][model_name].values():
                try:
                    dependencies.append(field['requires'])
                except KeyError:
                    # (No ForeignKey)
                    pass
            for dependency in dependencies:
                if dependency not in model_order[:idx]:
                    raise ValueError("Model {} requires {} but would be loaded "
                                     "first; stopping...".format(model_name,
                                                                 dependency))

        ###################################################
        # CREATE IMPORT DATA DIRECT UNIQUE_FIELD MAPPINGS #
        ###################################################
        import_unique_ids_mappings = {}
        for model_name, import_data in data['export_data'].items():
            if model_name in metadata['unique_identifiers']:
                # I have to reconvert the pk to integer
                import_unique_ids_mappings[model_name] = {
                    int(k): v[metadata['unique_identifiers'][model_name]] for k, v in
                    import_data.items()}

        ###############
        # IMPORT DATA #
        ###############
        # DO ALL WITH A TRANSACTION
        with transaction.atomic():
            foreign_ids_reverse_mappings = {}
            new_entries = {}
            existing_entries = {}

            # I first generate the list of data
            for model_name in model_order:
                cls_signature = entity_names_to_signatures[model_name]
                Model = get_object_from_string(cls_signature)
                fields_info = metadata['all_fields_info'].get(model_name, {})
                unique_identifier = metadata['unique_identifiers'].get(
                    model_name, None)

                new_entries[model_name] = {}
                existing_entries[model_name] = {}

                foreign_ids_reverse_mappings[model_name] = {}

                # Not necessarily all models are exported
                if model_name in data['export_data']:

                    # skip nodes that are already present in the DB
                    if unique_identifier is not None:
                        import_unique_ids = set(v[unique_identifier] for v in
                                                data['export_data'][model_name].values())

                        relevant_db_entries_result = Model.objects.filter(
                            **{'{}__in'.format(unique_identifier): import_unique_ids})
                        # Note: uuids need to be converted to strings
                        relevant_db_entries = {str(getattr(n, unique_identifier)):
                                n for n in relevant_db_entries_result}

                        foreign_ids_reverse_mappings[model_name] = {
                            k: v.pk for k, v in relevant_db_entries.items()}
                        for k, v in data['export_data'][model_name].items():
                            if v[unique_identifier] in relevant_db_entries.keys():
                                # Already in DB
                                existing_entries[model_name][k] = v
                            else:
                                # To be added
                                new_entries[model_name][k] = v
                    else:
                        new_entries[model_name] = data['export_data'][model_name].copy()

            # Show Comment mode if not silent and Comments exist in existing_entries
            if not silent:
                if COMMENT_ENTITY_NAME in existing_entries:
                    print("Comment mode: {}".format(comment_mode))

            # I import data from the given model
            for model_name in model_order:
                cls_signature = entity_names_to_signatures[model_name]
                Model = get_object_from_string(cls_signature)
                # Model = get_object_from_string(model_name)
                fields_info = metadata['all_fields_info'].get(model_name, {})
                unique_identifier = metadata['unique_identifiers'].get(
                    model_name, None)

                for import_entry_id, entry_data in existing_entries[model_name].items():
                    unique_id = entry_data[unique_identifier]
                    existing_entry_id = foreign_ids_reverse_mappings[model_name][unique_id]
                    import_data = dict(deserialize_field(
                        k, v, fields_info=fields_info,
                        import_unique_ids_mappings=import_unique_ids_mappings,
                        foreign_ids_reverse_mappings=foreign_ids_reverse_mappings)
                                       for k, v in entry_data.items())
                    # TODO COMPARE, AND COMPARE ATTRIBUTES

                    if Model is models.DbComment:
                        new_entry_uuid = _merge_comment(import_data, comment_mode)
                        if new_entry_uuid is not None:
                            entry_data[unique_identifier] = new_entry_uuid
                            new_entries[model_name][import_entry_id] = entry_data

                    if model_name not in ret_dict:
                        ret_dict[model_name] = {'new': [], 'existing': []}
                    ret_dict[model_name]['existing'].append((import_entry_id,
                                                             existing_entry_id))
                    if not silent:
                        print("existing %s: %s (%s->%s)" % (model_name, unique_id,
                                                            import_entry_id,
                                                            existing_entry_id))
                        # print("  `-> WARNING: NO DUPLICITY CHECK DONE!")
                        # CHECK ALSO FILES!

                # Store all objects for this model in a list, and store them
                # all in once at the end.
                objects_to_create = []
                # This is needed later to associate the import entry with the new pk
                import_entry_ids = {}
                imported_comp_names = set()
                for import_entry_id, entry_data in new_entries[model_name].items():
                    unique_id = entry_data[unique_identifier]
                    import_data = dict(deserialize_field(
                        k, v, fields_info=fields_info,
                        import_unique_ids_mappings=import_unique_ids_mappings,
                        foreign_ids_reverse_mappings=foreign_ids_reverse_mappings)
                                       for k, v in entry_data.items())

                    if Model is models.DbGroup:
                        # Check if there is already a group with the same name
                        dupl_counter = 0
                        orig_label = import_data['label']
                        while Model.objects.filter(label=import_data['label']):
                            import_data['label'] = orig_label + DUPL_SUFFIX.format(dupl_counter)
                            dupl_counter += 1
                            if dupl_counter == 100:
                                raise exceptions.UniquenessError("A group of that label ( {} ) already exists"
                                    " and I could not create a new one".format(orig_label))

                    elif Model is models.DbComputer:
                        # Check if there is already a computer with the same name in the database
                        dupl = (Model.objects.filter(name=import_data['name'])
                                or import_data['name'] in imported_comp_names)
                        orig_name = import_data['name']
                        dupl_counter = 0
                        while dupl:
                            # Rename the new computer
                            import_data['name'] = (
                                    orig_name +
                                    DUPL_SUFFIX.format(dupl_counter))
                            dupl = (Model.objects.filter(name=import_data['name'])
                                    or import_data['name'] in imported_comp_names)
                            dupl_counter += 1
                            if dupl_counter == 100:
                                raise exceptions.UniquenessError("A computer of that name ( {} ) already exists"
                                    " and I could not create a new one".format(orig_name))

                        # The following is done for compatibility reasons
                        # In case the export file was generate with the SQLA
                        # export method
                        if isinstance(import_data['metadata'], dict):
                            import_data['metadata'] = json.dumps(import_data['metadata'])
                        if isinstance(import_data['transport_params'], dict):
                            import_data['transport_params'] = json.dumps(import_data['transport_params'])

                        imported_comp_names.add(import_data['name'])

                    elif Model is models.DbLog:
                        # Django requires metadata as a string.
                        # A JSON-serializable string.
                        if isinstance(import_data['metadata'], dict):
                            import_data['metadata'] = json.dumps(import_data['metadata'])

                    objects_to_create.append(Model(**import_data))
                    import_entry_ids[unique_id] = import_entry_id

                # Before storing entries in the DB, I store the files (if these
                # are nodes). Note: only for new entries!
                if model_name == NODE_ENTITY_NAME:
                    if not silent:
                        print("STORING NEW NODE FILES...")
                    for o in objects_to_create:

                        subfolder = folder.get_subfolder(os.path.join(
                            nodes_export_subfolder, export_shard_uuid(o.uuid)))
                        if not subfolder.exists():
                            raise ValueError("Unable to find the repository "
                                             "folder for node with UUID={} " \
                                             "in the exported "
                                             "file".format(o.uuid))
                        destdir = RepositoryFolder(
                            section=Repository._section_name,
                            uuid=o.uuid)
                        # Replace the folder, possibly destroying existing
                        # previous folders, and move the files (faster if we
                        # are on the same filesystem, and
                        # in any case the source is a SandboxFolder)
                        destdir.replace_with_folder(subfolder.abspath,
                                                    move=True, overwrite=True)

                # If there is an mtime in the field, disable the automatic update
                # to keep the mtime that we have set here
                if 'mtime' in [field.name for field in Model._meta.local_fields]:
                    with suppress_auto_now([(Model, ['mtime'])]):
                        # Store them all in once; however, the PK are not set in this way...
                        Model.objects.bulk_create(objects_to_create)
                else:
                    Model.objects.bulk_create(objects_to_create)

                # Get back the just-saved entries
                just_saved_queryset = Model.objects.filter(
                    **{"{}__in".format(unique_identifier):
                           import_entry_ids.keys()}).values_list(unique_identifier, 'pk')
                # note: convert uuids from type UUID to strings
                just_saved = { str(k) : v for k,v in just_saved_queryset }

                # Now I have the PKs, print the info
                # Moreover, set the foreign_ids_reverse_mappings
                for unique_id, new_pk in just_saved.items():
                    import_entry_id = import_entry_ids[unique_id]
                    foreign_ids_reverse_mappings[model_name][unique_id] = new_pk
                    if model_name not in ret_dict:
                        ret_dict[model_name] = {'new': [], 'existing': []}
                    ret_dict[model_name]['new'].append((import_entry_id,
                                                        new_pk))

                    if not silent:
                        print("NEW %s: %s (%s->%s)" % (model_name, unique_id,
                                                       import_entry_id,
                                                       new_pk))

                # For DbNodes, we also have to store its attributes
                if model_name == NODE_ENTITY_NAME:
                    if not silent:
                        print("STORING NEW NODE ATTRIBUTES...")
                    for unique_id, new_pk in just_saved.items():
                        import_entry_id = import_entry_ids[unique_id]
                        # Get attributes from import file
                        try:
                            attributes = data['node_attributes'][
                                str(import_entry_id)]
                            attributes_conversion = data[
                                'node_attributes_conversion'][
                                str(import_entry_id)]
                        except KeyError:
                            raise ValueError("Unable to find attribute info "
                                             "for DbNode with UUID = {}".format(unique_id))

                        # Here I have to deserialize the attributes
                        deserialized_attributes = deserialize_attributes(
                            attributes, attributes_conversion)
                        models.DbAttribute.reset_values_for_node(
                            dbnode=new_pk,
                            attributes=deserialized_attributes,
                            with_transaction=False)

                # For DbNodes, we also have to store its extras
                if model_name == NODE_ENTITY_NAME:
                    if extras_mode_new == 'import':
                        if not silent:
                            print("STORING NEW NODE EXTRAS...")
                        for unique_id, new_pk in just_saved.items():
                            import_entry_id = import_entry_ids[unique_id]
                            # Get extras from import file
                            try:
                                extras = data['node_extras'][
                                    str(import_entry_id)]
                                extras_conversion = data[
                                    'node_extras_conversion'][
                                    str(import_entry_id)]
                            except KeyError:
                                raise ValueError("Unable to find extras info "
                                                 "for DbNode with UUID = {}".format(unique_id))
                            deserialized_extras = deserialize_attributes(extras, extras_conversion)
                            # TODO: remove when aiida extras will be moved somewhere else
                            # from here
                            deserialized_extras = {key:value for key,value in deserialized_extras.items() if not
                                    key.startswith('_aiida_')}
                            if models.DbNode.objects.filter(uuid=unique_id)[0].node_type.endswith('code.Code.'):
                                deserialized_extras = {key:value for key,value in deserialized_extras.items() if not
                                        key == 'hidden'}
                            # till here
                            models.DbExtra.reset_values_for_node(
                                dbnode=new_pk,
                                attributes=deserialized_extras,
                                with_transaction=False)
                    elif extras_mode_new == 'none':
                        if not silent:
                            print("SKIPPING NEW NODE EXTRAS...")
                    else:
                        raise ValueError("Unknown extras_mode_new value: {}, should be either 'import' or "
                                "'none'".format(extras_mode_new))

                    # For the existing DbNodes we may want to choose the import mode
                    if not silent:
                        print("UPDATING EXISTING NODE EXTRAS (mode: {})".format(extras_mode_existing))

                    for import_entry_id, entry_data in existing_entries[model_name].items():
                        unique_id = entry_data[unique_identifier]
                        existing_entry_id = foreign_ids_reverse_mappings[model_name][unique_id]
                        # Get extras from import file
                        try:
                            extras = data['node_extras'][
                                str(import_entry_id)]
                            extras_conversion = data[
                                'node_extras_conversion'][
                                str(import_entry_id)]
                        except KeyError:
                            raise ValueError("Unable to find extras info "
                                             "for DbNode with UUID = {}".format(unique_id))

                        # Here I have to deserialize the extras
                        old_extras = models.DbExtra.get_all_values_for_nodepk(existing_entry_id)
                        deserialized_extras = deserialize_attributes(extras, extras_conversion)
                        # TODO: remove when aiida extras will be moved somewhere else
                        # from here
                        deserialized_extras = {key:value for key,value in deserialized_extras.items() if not
                                key.startswith('_aiida_')}
                        if models.DbNode.objects.filter(uuid=unique_id)[0].node_type.endswith('code.Code.'):
                            deserialized_extras = {key:value for key,value in deserialized_extras.items() if not
                                    key == 'hidden'}
                        # till here
                        merged_extras = merge_extras(old_extras, deserialized_extras, extras_mode_existing)

                        models.DbExtra.reset_values_for_node(
                            dbnode=existing_entry_id,
                            attributes=merged_extras,
                            with_transaction=False)

            if not silent:
                print("STORING NODE LINKS...")
            ## TODO: check that we are not creating input links of an already
            ##       existing node...
            import_links = data['links_uuid']
            links_to_store = []

            # Needed for fast checks of existing links
            existing_links_raw = models.DbLink.objects.all().values_list(
                'input', 'output', 'label', 'type')
            existing_links_labels = {(l[0], l[1]): l[2] for l in existing_links_raw}
            existing_input_links = {(l[1], l[2]): l[0] for l in existing_links_raw}

            # ~ print(foreign_ids_reverse_mappings)
            dbnode_reverse_mappings = foreign_ids_reverse_mappings[NODE_ENTITY_NAME]
            for link in import_links:
                try:
                    in_id = dbnode_reverse_mappings[link['input']]
                    out_id = dbnode_reverse_mappings[link['output']]
                except KeyError:
                    if ignore_unknown_nodes:
                        continue
                    else:
                        raise ValueError("Trying to create a link with one "
                                         "or both unknown nodes, stopping "
                                         "(in_uuid={}, out_uuid={}, "
                                         "label={})".format(link['input'],
                                                            link['output'],
                                                            link['label']))

                try:
                    existing_label = existing_links_labels[in_id, out_id]
                    if existing_label != link['label']:
                        raise ValueError("Trying to rename an existing link "
                                         "name, stopping (in={}, out={}, "
                                         "old_label={}, new_label={})"
                                         .format(in_id, out_id, existing_label,
                                                 link['label']))
                        # Do nothing, the link is already in place and has
                        # the correct name
                except KeyError:
                    try:
                        # We try to get the existing input of the link that
                        # points to "out" and has label link['label'].
                        # If there is no existing_input, it means that the
                        # link doesn't exist and it has to be created. If
                        # it exists, then the only case that we can have more
                        # than one links with the same name entering a node
                        # is the case of the RETURN links of workflows/
                        # workchains. If it is not this case, then it is
                        # an error.
                        existing_input = existing_input_links[out_id,
                                                              link['label']]

                        if link['type'] != LinkType.RETURN:
                            raise ValueError(
                                "There exists already an input link to node "
                                "with UUID {} with label {} but it does not "
                                "come from the expected input with UUID {} "
                                "but from a node with UUID {}."
                                    .format(link['output'], link['label'],
                                            link['input'], existing_input))
                    except KeyError:
                        # New link
                        links_to_store.append(models.DbLink(
                            input_id=in_id, output_id=out_id, label=link['label'], type=LinkType(link['type']).value))
                        if LINK_ENTITY_NAME not in ret_dict:
                            ret_dict[LINK_ENTITY_NAME] = {'new': []}
                        ret_dict[LINK_ENTITY_NAME]['new'].append((in_id, out_id))

            # Store new links
            if links_to_store:
                if not silent:
                    print("   ({} new links...)".format(len(links_to_store)))

                models.DbLink.objects.bulk_create(links_to_store)
            else:
                if not silent:
                    print("   (0 new links...)")

            if not silent:
                print("STORING GROUP ELEMENTS...")
            import_groups = data['groups_uuid']
            for groupuuid, groupnodes in import_groups.items():
                # TODO: cache these to avoid too many queries
                group = models.DbGroup.objects.get(uuid=groupuuid)
                nodes_to_store = [dbnode_reverse_mappings[node_uuid]
                                  for node_uuid in groupnodes]
                if nodes_to_store:
                    group.dbnodes.add(*nodes_to_store)

            ######################################################
            # Put everything in a specific group
            dbnode_model_name = NODE_ENTITY_NAME

            existing = existing_entries.get(dbnode_model_name, {})
            existing_pk = [foreign_ids_reverse_mappings[
                               dbnode_model_name][v['uuid']]
                           for v in six.itervalues(existing)]
            new = new_entries.get(dbnode_model_name, {})
            new_pk = [foreign_ids_reverse_mappings[
                          dbnode_model_name][v['uuid']]
                      for v in six.itervalues(new)]

            pks_for_group = existing_pk + new_pk

            # So that we do not create empty groups
            if pks_for_group:
                # If user specified a group, import all things in it
                if user_group:
                    group = user_group[0]
                else:
                    # Get an unique name for the import group, based on the
                    # current (local) time
                    basename = timezone.localtime(timezone.now()).strftime(
                        "%Y%m%d-%H%M%S")
                    counter = 0
                    created = False
                    while not created:
                        if counter == 0:
                            group_label = basename
                        else:
                            group_label = "{}_{}".format(basename, counter)
                        try:
                            group = Group(label=group_label, type_string=IMPORTGROUP_TYPE).store()
                            created = True
                        except (exceptions.UniquenessError, exceptions.IntegrityError):
                            counter += 1

                # Add all the nodes to the new group
                # TODO: decide if we want to return the group label
                nodes = [entry[0] for entry in QueryBuilder().append(Node, filters={'id': {'in': pks_for_group}}).all()]
                group.add_nodes(nodes)

                if not silent:
                    print("IMPORTED NODES GROUPED IN IMPORT GROUP NAMED '{}'".format(group.label))
            else:
                if not silent:
                    print("NO DBNODES TO IMPORT, SO NO GROUP CREATED")

    if not silent:
        print("*** WARNING: MISSING EXISTING UUID CHECKS!!")
        print("*** WARNING: TODO: UPDATE IMPORT_DATA WITH DEFAULT VALUES! (e.g. calc status, user pwd, ...)")
        print("DONE.")

    return ret_dict


def validate_uuid(given_uuid):
    """
    A simple check for the UUID validity.
    """
    from uuid import UUID
    try:
        parsed_uuid = UUID(given_uuid, version=4)
    except ValueError:
        # If not a valid UUID
        return False

    # Check if there was any kind of conversion of the hex during
    # the validation
    return str(parsed_uuid) == given_uuid


def import_data_sqla(in_path, user_group=None, ignore_unknown_nodes=False,
        extras_mode_existing='kcl', extras_mode_new='import',
        comment_mode='newest', silent=False):
    """
    Import exported AiiDA environment to the AiiDA database.
    If the 'in_path' is a folder, calls extract_tree; otherwise, tries to
    detect the compression format (zip, tar.gz, tar.bz2, ...) and calls the
    correct function.
    :param in_path: the path to a file or folder that can be imported in AiiDA
    :param extras_mode_existing: 3 letter code that will identify what to do with the extras import.
    The first letter acts on extras that are present in the original node and not present in the imported node.
    Can be either:
    'k' (keep it) or
    'n' (do not keep it).
    The second letter acts on the imported extras that are not present in the original node.
    Can be either:
    'c' (create it) or
    'n' (do not create it).
    The third letter defines what to do in case of a name collision.
    Can be either:
    'l' (leave the old value),
    'u' (update with a new value),
    'd' (delete the extra), or
    'a' (ask what to do if the content is different).
    :param extras_mode_new: 'import' to import extras of new nodes or 'none' to ignore them
    :param comment_mode: Comment import modes (when same UUIDs are found):
    'newest': Will keep the Comment with the most recent modification time (mtime)
    'overwrite': Will overwrite existing Comments with the ones from the import file
    """
    import os
    import tarfile
    import zipfile
    from itertools import chain

    from aiida.common import timezone

    from aiida.backends.sqlalchemy.models.node import DbNode
    from aiida.backends.sqlalchemy.utils import flag_modified
    from aiida.common.archive import extract_tree, extract_tar, extract_zip
    from aiida.common.folders import SandboxFolder, RepositoryFolder
    from aiida.common.utils import get_object_from_string
    from aiida.common.links import LinkType
    from aiida.common import json

    # This is the export version expected by this function
    expected_export_version = StrictVersion('0.4')

    # The name of the subfolder in which the node files are stored
    nodes_export_subfolder = 'nodes'

    # The returned dictionary with new and existing nodes and links
    ret_dict = {}

    ################
    # EXTRACT DATA #
    ################
    # The sandbox has to remain open until the end
    with SandboxFolder() as folder:
        if os.path.isdir(in_path):
            extract_tree(in_path, folder)
        else:
            if tarfile.is_tarfile(in_path):
                extract_tar(in_path, folder, silent=silent,
                            nodes_export_subfolder=nodes_export_subfolder)
            elif zipfile.is_zipfile(in_path):
                extract_zip(in_path, folder, silent=silent,
                            nodes_export_subfolder=nodes_export_subfolder)
            else:
                raise ValueError("Unable to detect the input file format, it "
                                 "is neither a (possibly compressed) tar "
                                 "file, nor a zip file.")

        if not folder.get_content_list():
            from aiida.common.exceptions import ContentNotExistent
            raise ContentNotExistent("The provided file/folder ({}) is empty"
                                     .format(in_path))
        try:
            with io.open(folder.get_abs_path('metadata.json'), encoding='utf8') as fhandle:
                metadata = json.load(fhandle)

            with io.open(folder.get_abs_path('data.json'), encoding='utf8') as fhandle:
                data = json.load(fhandle)
        except IOError as e:
            raise ValueError("Unable to find the file {} in the import "
                             "file or folder".format(e.filename))

        ######################
        # PRELIMINARY CHECKS #
        ######################
        export_version = StrictVersion(str(metadata['export_version']))
        if export_version != expected_export_version:
            msg = "Export file version is {}, can import only version {}"\
                    .format(metadata['export_version'], expected_export_version)
            if export_version < expected_export_version:
                msg += "\nUse 'verdi export migrate' to update this export file."
            else:
                msg += "\nUpdate your AiiDA version in order to import this file."

            raise exceptions.IncompatibleArchiveVersionError(msg)

        ###################################################################
        #           CREATE UUID REVERSE TABLES AND CHECK IF               #
        #              I HAVE ALL NODES FOR THE LINKS                     #
        ###################################################################
        linked_nodes = set(chain.from_iterable((l['input'], l['output'])
                                               for l in data['links_uuid']))
        group_nodes = set(chain.from_iterable(
            six.itervalues(data['groups_uuid'])))

        # Check that UUIDs are valid
        linked_nodes = set(x for x in linked_nodes if validate_uuid(x))
        group_nodes = set(x for x in group_nodes if validate_uuid(x))

        # I preload the nodes, I need to check each of them later, and I also
        # store them in a reverse table
        # I break up the query due to SQLite limitations..
        # relevant_db_nodes = {}
        db_nodes_uuid = set()
        import_nodes_uuid = set()
        if linked_nodes:
            qb = QueryBuilder()
            qb.append(Node, filters={"uuid": {"in": linked_nodes}},
                      project=["uuid"])
            for res in qb.iterall():
                db_nodes_uuid.add(res[0])

        if NODE_ENTITY_NAME in data['export_data']:
            for v in data['export_data'][NODE_ENTITY_NAME].values():
                import_nodes_uuid.add(v['uuid'])

        unknown_nodes = linked_nodes.union(group_nodes) - db_nodes_uuid.union(
            import_nodes_uuid)

        if unknown_nodes and not ignore_unknown_nodes:
            raise ValueError(
                "The import file refers to {} nodes with unknown UUID, "
                "therefore it cannot be imported. Either first import the "
                "unknown nodes, or export also the parents when exporting. "
                "The unknown UUIDs are:\n".format(len(unknown_nodes)) +
                "\n".join('* {}'.format(uuid) for uuid in unknown_nodes))

        ###################################
        # DOUBLE-CHECK MODEL DEPENDENCIES #
        ###################################
        # The entity import order. It is defined by the database model
        # relationships.
        # It is a list of strings, e.g.:
        # ['aiida.backends.djsite.db.models.DbUser', 'aiida.backends.djsite.db.models.DbComputer', 'aiida.backends.djsite.db.models.DbNode', 'aiida.backends.djsite.db.models.DbGroup']
        entity_sig_order = [entity_names_to_signatures[m]
                            for m in (USER_ENTITY_NAME, COMPUTER_ENTITY_NAME,
                                      NODE_ENTITY_NAME, GROUP_ENTITY_NAME,
                                      LOG_ENTITY_NAME, COMMENT_ENTITY_NAME)]
        # "Entities" that do appear in the import file, but whose import is
        # managed manually
        entity_sig_manual = [entity_names_to_signatures[m]
                         for m in (LINK_ENTITY_NAME, ATTRIBUTE_ENTITY_NAME)]

        all_known_entity_sigs = entity_sig_order + entity_sig_manual

        #  I make a new list that contains the entity names:
        # eg: ['User', 'Computer', 'Node', 'Group', 'Link', 'Attribute']
        all_entity_names = [signatures_to_entity_names[entity_sig] for entity_sig in all_known_entity_sigs]
        for import_field_name in metadata['all_fields_info']:
            if import_field_name not in all_entity_names:
                raise NotImplementedError("Apparently, you are importing a "
                                          "file with a model '{}', but this "
                                          "does not appear in "
                                          "all_known_models!"
                                          .format(import_field_name))

        for idx, entity_sig in enumerate(entity_sig_order):
            dependencies = []
            entity_name = signatures_to_entity_names[entity_sig]
            # for every field, I checked the dependencies given as value for key requires
            for field in metadata['all_fields_info'][entity_name].values():
                try:
                    dependencies.append(field['requires'])
                except KeyError:
                    # (No ForeignKey)
                    pass
            for dependency in dependencies:
                if dependency not in all_entity_names[:idx]:
                    raise ValueError("Entity {} requires {} but would be "
                                     "loaded first; stopping..."
                                     .format(entity_sig, dependency))

        ###################################################
        # CREATE IMPORT DATA DIRECT UNIQUE_FIELD MAPPINGS #
        ###################################################
        # This is nested dictionary of entity_name:{id:uuid}
        # to map one id (the pk) to a different one.
        # One of the things to remove for v0.4
        # {
        # u'Node': {2362: u'82a897b5-fb3a-47d7-8b22-c5fe1b4f2c14', 2363: u'ef04aa5d-99e7-4bfd-95ef-fe412a6a3524', 2364: u'1dc59576-af21-4d71-81c2-bac1fc82a84a'},
        # u'User': {1: u'aiida@localhost'}
        # }
        import_unique_ids_mappings = {}
        # Export data since v0.3 contains the keys entity_name
        for entity_name, import_data in data['export_data'].items():
            # Again I need the entity_name since that's what's being stored since 0.3
            if entity_name in metadata['unique_identifiers']:
                # I have to reconvert the pk to integer
                import_unique_ids_mappings[entity_name] = {
                    int(k): v[metadata['unique_identifiers'][entity_name]]
                    for k, v in import_data.items()}
        ###############
        # IMPORT DATA #
        ###############
        # DO ALL WITH A TRANSACTION
        import aiida.backends.sqlalchemy

        session = aiida.backends.sqlalchemy.get_scoped_session()

        try:
            foreign_ids_reverse_mappings = {}
            new_entries = {}
            existing_entries = {}

            # I first generate the list of data
            for entity_sig in entity_sig_order:
                entity_name = signatures_to_entity_names[entity_sig]
                entity = entity_names_to_entities[entity_name]
                # I get the unique identifier, since v0.3 stored under entity_name
                unique_identifier = metadata['unique_identifiers'].get(entity_name, None)

                # so, new_entries. Also, since v0.3 it makes more sense to use the entity_name
                #~ new_entries[entity_sig] = {}
                new_entries[entity_name] = {}
                # existing_entries[entity_sig] = {}
                existing_entries[entity_name] = {}
                # ~ foreign_ids_reverse_mappings[entity_sig] = {}
                foreign_ids_reverse_mappings[entity_name] = {}

                # Not necessarily all models are exported
                if entity_name in data['export_data']:

                    if unique_identifier is not None:
                        import_unique_ids = set(v[unique_identifier] for v in data['export_data'][entity_name].values())

                        relevant_db_entries = dict()
                        if len(import_unique_ids) > 0:
                            qb = QueryBuilder()
                            qb.append(entity, filters={
                                unique_identifier: {"in": import_unique_ids}},
                                      project=["*"], tag="res")
                            relevant_db_entries = {
                                str(getattr(v[0], unique_identifier)):  # str() to convert UUID() to string
                                    v[0] for v in qb.all()}

                            foreign_ids_reverse_mappings[entity_name] = {
                                k: v.pk for k, v in
                                relevant_db_entries.items()}

                        imported_comp_names = set()
                        for k, v in data['export_data'][entity_name].items():
                            if entity_name == GROUP_ENTITY_NAME:
                                # Check if there is already a group with the same name,
                                # and if so, recreate the name
                                orig_label = v["label"]
                                dupl_counter = 0
                                while QueryBuilder().append(entity,
                                            filters={'label': {"==": v["label"]}}).count():
                                    # Rename the new group
                                    v["label"] = orig_label + DUPL_SUFFIX.format(dupl_counter)
                                    dupl_counter += 1
                                    if dupl_counter == 100:
                                        raise exceptions.UniquenessError("A group of that label ( {} )"
                                                "  already exists and I could not create a new one"
                                                "".format(orig_label))


                            elif entity_name == COMPUTER_ENTITY_NAME:
                                # The following is done for compatibility
                                # reasons in case the export file was generated
                                # with the Django export method. In Django the
                                # metadata and the transport parameters are
                                # stored as (unicode) strings of the serialized
                                # JSON objects and not as simple serialized
                                # JSON objects.
                                if (isinstance(v['metadata'], six.string_types) or
                                        isinstance(v['metadata'], six.binary_type)):
                                    v['metadata'] = json.loads(v['metadata'])  # loads() can handle str and unicode/bytes

                                if (isinstance(v['transport_params'], six.string_types) or
                                        isinstance(v['transport_params'], six.binary_type)):
                                    v['transport_params'] = json.loads(v['transport_params'])

                                # Check if there is already a computer with the
                                # same name in the database
                                qb = QueryBuilder()
                                qb.append(entity,
                                          filters={'name': {"==": v["name"]}},
                                          project=["*"], tag="res")
                                dupl = (qb.count()
                                        or v["name"] in imported_comp_names)
                                dupl_counter = 0
                                orig_name = v["name"]
                                while dupl:
                                    # Rename the new computer
                                    v["name"] = (
                                            orig_name +
                                            DUPL_SUFFIX.format(
                                                dupl_counter))
                                    dupl_counter += 1
                                    qb = QueryBuilder()
                                    qb.append(entity,
                                              filters={
                                                  'name': {"==": v["name"]}},
                                              project=["*"], tag="res")
                                    dupl = (qb.count() or
                                            v["name"] in imported_comp_names)

                                imported_comp_names.add(v["name"])

                            if v[unique_identifier] in relevant_db_entries:
                                # Already in DB
                                # again, switched to entity_name in v0.3
                                existing_entries[entity_name][k] = v
                            else:
                                # To be added
                                new_entries[entity_name][k] = v
                    else:
                        # Why the copy:
                        new_entries[entity_name] = data['export_data'][entity_name].copy()

            # Show Comment mode if not silent and Comments exist in existing_entries
            if not silent:
                if COMMENT_ENTITY_NAME in existing_entries:
                    print("Comment mode: {}".format(comment_mode))

            # I import data from the given model
            for entity_sig in entity_sig_order:
                entity_name = signatures_to_entity_names[entity_sig]
                entity = entity_names_to_entities[entity_name]
                fields_info = metadata['all_fields_info'].get(entity_name, {})
                unique_identifier = metadata['unique_identifiers'].get(entity_name, None)

                for import_entry_id, entry_data in existing_entries[entity_name].items():
                    unique_id = entry_data[unique_identifier]
                    existing_entry_id = foreign_ids_reverse_mappings[entity_name][unique_id]
                    import_data = dict(deserialize_field(
                        k, v, fields_info=fields_info,
                        import_unique_ids_mappings=import_unique_ids_mappings,
                        foreign_ids_reverse_mappings=foreign_ids_reverse_mappings)
                                       for k, v in entry_data.items())
                    # TODO COMPARE, AND COMPARE ATTRIBUTES

                    if entity_sig is entity_names_to_signatures[COMMENT_ENTITY_NAME]:
                        new_entry_uuid = _merge_comment(import_data, comment_mode)
                        if new_entry_uuid is not None:
                            entry_data[unique_identifier] = new_entry_uuid
                            new_entries[entity_name][import_entry_id] = entry_data

                    if entity_name not in ret_dict:
                        ret_dict[entity_name] = {'new': [], 'existing': []}
                    ret_dict[entity_name]['existing'].append((import_entry_id, existing_entry_id))
                    if not silent:
                        print("existing %s: %s (%s->%s)" % (entity_sig,
                                                            unique_id,
                                                            import_entry_id,
                                                            existing_entry_id))

                # Store all objects for this model in a list, and store them
                # all in once at the end.
                objects_to_create = list()
                # This is needed later to associate the import entry with the new pk
                import_entry_ids = dict()

                for import_entry_id, entry_data in new_entries[entity_name].items():
                    unique_id = entry_data[unique_identifier]
                    import_data = dict(deserialize_field(
                        k, v, fields_info=fields_info,
                        import_unique_ids_mappings=import_unique_ids_mappings,
                        foreign_ids_reverse_mappings=foreign_ids_reverse_mappings)
                                       for k, v in entry_data.items())

                    # We convert the Django fields to SQLA. Note that some of
                    # the Django fields were converted to SQLA compatible
                    # fields by the deserialize_field method. This was done
                    # for optimization reasons in Django but makes them
                    # compatible with the SQLA schema and they don't need any
                    # further conversion.
                    if entity_name in file_fields_to_model_fields:
                        for file_fkey in file_fields_to_model_fields[entity_name]:

                            # This is an exception because the DbLog model defines the `_metadata` column instead of the
                            # `metadata` column used in the Django model. This is because the SqlAlchemy model base
                            # class already has a metadata attribute that cannot be overridden. For consistency, the
                            # `DbLog` class however expects the `metadata` keyword in its constructor, so we should
                            # ignore the mapping here
                            if entity_name == LOG_ENTITY_NAME and file_fkey == 'metadata':
                                continue

                            model_fkey = file_fields_to_model_fields[entity_name][file_fkey]
                            if model_fkey in import_data:
                                continue
                            import_data[model_fkey] = import_data[file_fkey]
                            import_data.pop(file_fkey, None)

                    db_entity = get_object_from_string(
                        entity_names_to_sqla_schema[entity_name])

                    objects_to_create.append(db_entity(**import_data))
                    import_entry_ids[unique_id] = import_entry_id

                # Before storing entries in the DB, I store the files (if these
                # are nodes). Note: only for new entries!
                if entity_sig == entity_names_to_signatures[NODE_ENTITY_NAME]:

                    if not silent:
                        print("STORING NEW NODE FILES & ATTRIBUTES...")
                    for o in objects_to_create:

                        # Creating the needed files
                        subfolder = folder.get_subfolder(os.path.join(
                            nodes_export_subfolder, export_shard_uuid(o.uuid)))
                        if not subfolder.exists():
                            raise ValueError("Unable to find the repository "
                                             "folder for node with UUID={} "
                                             "in the exported file"
                                             .format(o.uuid))
                        destdir = RepositoryFolder(
                            section=Repository._section_name,
                            uuid=o.uuid)
                        # Replace the folder, possibly destroying existing
                        # previous folders, and move the files (faster if we
                        # are on the same filesystem, and
                        # in any case the source is a SandboxFolder)
                        destdir.replace_with_folder(subfolder.abspath,
                                                    move=True, overwrite=True)

                        # For DbNodes, we also have to store Attributes!
                        import_entry_id = import_entry_ids[str(o.uuid)]
                        # Get attributes from import file
                        try:
                            attributes = data['node_attributes'][
                                str(import_entry_id)]

                            attributes_conversion = data[
                                'node_attributes_conversion'][
                                str(import_entry_id)]
                        except KeyError:
                            raise ValueError(
                                "Unable to find attribute info "
                                "for DbNode with UUID = {}".format(
                                    o.uuid))

                        # Here I have to deserialize the attributes
                        deserialized_attributes = deserialize_attributes(
                            attributes, attributes_conversion)

                        if deserialized_attributes:
                            o.attributes = dict()
                            for k, v in deserialized_attributes.items():
                                o.attributes[k] = v

                        # For DbNodes, we also have to store extras
                        # Get extras from import file
                        if extras_mode_new == 'import':
                            if not silent:
                                print("STORING NEW NODE EXTRAS...")
                            try:
                                extras = data['node_extras'][
                                    str(import_entry_id)]

                                extras_conversion = data[
                                    'node_extras_conversion'][
                                    str(import_entry_id)]
                            except KeyError:
                                raise ValueError(
                                    "Unable to find extras info "
                                    "for DbNode with UUID = {}".format(
                                        o.uuid))
                            # Here I have to deserialize the extras
                            deserialized_extras = deserialize_attributes(extras, extras_conversion)
                            # TODO: remove when aiida extras will be moved somewhere else
                            # from here
                            deserialized_extras = {key:value for key, value in deserialized_extras.items() if not
                                    key.startswith('_aiida_')}
                            if o.node_type.endswith('code.Code.'):
                                deserialized_extras = {key:value for key,value in deserialized_extras.items() if not
                                        key == 'hidden'}
                            # till here
                            o.extras = dict()
                            for k, v in deserialized_extras.items():
                                o.extras[k] = v
                        elif extras_mode_new == 'none':
                            if not silent:
                                print("SKIPPING NEW NODE EXTRAS...")
                        else:
                            raise ValueError("Unknown extras_mode_new value: {}, should be either 'import' or "
                                    "'none'".format(extras_mode_new))

                    if not silent:
                        print("UPDATING EXISTING NODE EXTRAS (mode: {})".format(extras_mode_existing))

                    uuid_import_pk_match = {entry_data[unique_identifier]:import_entry_id for
                            import_entry_id, entry_data in existing_entries[entity_name].items()}
                    for db_node in session.query(DbNode).filter(DbNode.uuid.in_(uuid_import_pk_match)).distinct().all():
                        import_entry_id = uuid_import_pk_match[str(db_node.uuid)]
                        # Get extras from import file
                        try:
                            extras = data['node_extras'][
                                str(import_entry_id)]
                            extras_conversion = data[
                                'node_extras_conversion'][
                                str(import_entry_id)]
                        except KeyError:
                            raise ValueError("Unable to find extras info "
                                             "for DbNode with UUID = {}".format(db_node.uuid))

                        # Here I have to deserialize the extras
                        old_extras = db_node.extras
                        deserialized_extras = deserialize_attributes(extras, extras_conversion)
                        # TODO: remove when aiida extras will be moved somewhere else
                        # from here
                        deserialized_extras = {key:value for key, value in deserialized_extras.items() if not
                                key.startswith('_aiida_')}
                        if db_node.node_type.endswith('code.Code.'):
                            deserialized_extras = {key:value for key,value in deserialized_extras.items() if not
                                    key == 'hidden'}
                        # till here
                        db_node.extras = merge_extras(old_extras, deserialized_extras, extras_mode_existing)
                        flag_modified(db_node, "extras")

                # Store them all in once; However, the PK
                # are not set in this way...
                if objects_to_create:
                    session.add_all(objects_to_create)

                session.flush()

                if import_entry_ids.keys():
                    qb = QueryBuilder()
                    qb.append(entity, filters={
                        unique_identifier: {"in": list(import_entry_ids.keys())}},
                              project=[unique_identifier, "id"], tag="res")
                    just_saved = {v[0]: v[1] for v in qb.all()}
                else:
                    just_saved = dict()

                # Now I have the PKs, print the info
                # Moreover, set the foreign_ids_reverse_mappings
                for unique_id, new_pk in just_saved.items():
                    from uuid import UUID
                    if isinstance(unique_id, UUID):
                        unique_id = str(unique_id)
                    import_entry_id = import_entry_ids[unique_id]
                    foreign_ids_reverse_mappings[entity_name][unique_id] = new_pk
                    if entity_name not in ret_dict:
                        ret_dict[entity_name] = {'new': [], 'existing': []}
                    ret_dict[entity_name]['new'].append((import_entry_id,
                                                         new_pk))

                    if not silent:
                        print("NEW %s: %s (%s->%s)" % (entity_sig, unique_id,
                                                       import_entry_id,
                                                       new_pk))

            if not silent:
                print("STORING NODE LINKS...")
            ## TODO: check that we are not creating input links of an already
            ##       existing node...
            import_links = data['links_uuid']
            links_to_store = []

            # Needed for fast checks of existing links
            from aiida.backends.sqlalchemy.models.node import DbLink
            existing_links_raw = session.query(
                DbLink.input_id, DbLink.output_id,DbLink.label).all()
            existing_links_labels = {(l[0], l[1]): l[2]
                                     for l in existing_links_raw}
            existing_input_links = {(l[1], l[2]): l[0]
                                    for l in existing_links_raw}

            dbnode_reverse_mappings = foreign_ids_reverse_mappings[NODE_ENTITY_NAME]
            for link in import_links:
                try:
                    in_id = dbnode_reverse_mappings[link['input']]
                    out_id = dbnode_reverse_mappings[link['output']]
                except KeyError:
                    if ignore_unknown_nodes:
                        continue
                    else:
                        raise ValueError("Trying to create a link with one "
                                         "or both unknown nodes, stopping "
                                         "(in_uuid={}, out_uuid={}, "
                                         "label={})".format(link['input'],
                                                            link['output'],
                                                            link['label']))

                try:
                    existing_label = existing_links_labels[in_id, out_id]
                    if existing_label != link['label']:
                        raise ValueError("Trying to rename an existing link "
                                         "name, stopping (in={}, out={}, "
                                         "old_label={}, new_label={})"
                                         .format(in_id, out_id, existing_label,
                                                 link['label']))
                        # Do nothing, the link is already in place and has
                        # the correct name
                except KeyError:
                    try:
                        # We try to get the existing input of the link that
                        # points to "out" and has label link['label'].
                        # If there is no existing_input, it means that the
                        # link doesn't exist and it has to be created. If
                        # it exists, then the only case that we can have more
                        # than one links with the same name entering a node
                        # is the case of the RETURN links of workflows/
                        # workchains. If it is not this case, then it is
                        # an error.
                        existing_input = existing_input_links[out_id,
                                                              link['label']]

                        if link['type'] != LinkType.RETURN:
                            raise ValueError(
                                "There exists already an input link to node "
                                "with UUID {} with label {} but it does not "
                                "come from the expected input with UUID {} "
                                "but from a node with UUID {}."
                                    .format(link['output'], link['label'],
                                            link['input'], existing_input))
                    except KeyError:
                        # New link
                        links_to_store.append(DbLink(
                            input_id=in_id, output_id=out_id,
                            label=link['label'], type=LinkType(link['type']).value))
                        if LINK_ENTITY_NAME not in ret_dict:
                            ret_dict[LINK_ENTITY_NAME] = {'new': []}
                        ret_dict[LINK_ENTITY_NAME]['new'].append((in_id, out_id))

            # Store new links
            if links_to_store:
                if not silent:
                    print("   ({} new links...)".format(len(links_to_store)))
                session.add_all(links_to_store)
            else:
                if not silent:
                    print("   (0 new links...)")

            if not silent:
                print("STORING GROUP ELEMENTS...")
            import_groups = data['groups_uuid']
            for groupuuid, groupnodes in import_groups.items():
                # # TODO: cache these to avoid too many queries
                qb_group = QueryBuilder().append(
                    Group, filters={'uuid': {'==': groupuuid}})
                group = qb_group.first()[0]
                nodes_ids_to_add = [dbnode_reverse_mappings[node_uuid]
                                    for node_uuid in groupnodes]
                qb_nodes = QueryBuilder().append(
                    Node, filters={'id': {'in': nodes_ids_to_add}})
                # Adding nodes to group avoiding the SQLA ORM to increase speed
                nodes_to_add = [n[0].backend_entity for n in qb_nodes.all()]
                group.backend_entity.add_nodes(nodes_to_add, skip_orm=True)

            ######################################################
            # Put everything in a specific group
            existing = existing_entries.get(NODE_ENTITY_NAME, {})
            existing_pk = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][v['uuid']]
                           for v in six.itervalues(existing)]
            new = new_entries.get(NODE_ENTITY_NAME, {})
            new_pk = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][v['uuid']]
                      for v in six.itervalues(new)]

            pks_for_group = existing_pk + new_pk

            # So that we do not create empty groups
            if pks_for_group:
                # If user specified a group, import all things in it
                if user_group:
                    group = user_group[0]
                else:
                    # Get an unique name for the import group, based on the
                    # current (local) time
                    basename = timezone.localtime(timezone.now()).strftime(
                        "%Y%m%d-%H%M%S")
                    counter = 0
                    created = False
                    while not created:
                        if counter == 0:
                            group_label = basename
                        else:
                            group_label = "{}_{}".format(basename, counter)

                        group = Group(label=group_label,
                                      type_string=IMPORTGROUP_TYPE)
                        from aiida.backends.sqlalchemy.models.group import DbGroup
                        if session.query(DbGroup).filter(
                                DbGroup.label == group.backend_entity._dbmodel.label).count() == 0:
                            session.add(group.backend_entity._dbmodel)
                            created = True
                        else:
                            counter += 1

                # Adding nodes to group avoiding the SQLA ORM to increase speed
                nodes = [entry[0].backend_entity for entry in QueryBuilder().append(Node, filters={'id': {'in': pks_for_group}}).all()]
                group.backend_entity.add_nodes(nodes, skip_orm=True)
                if not silent:
                    print("IMPORTED NODES GROUPED IN IMPORT GROUP NAMED '{}'".format(group.label))
            else:
                if not silent:
                    print("NO DBNODES TO IMPORT, SO NO GROUP CREATED")

            if not silent:
                print("COMMITTING EVERYTHING...")
            session.commit()
        except:
            print("Rolling back")
            session.rollback()
            raise

    if not silent:
        print("*** WARNING: MISSING EXISTING UUID CHECKS!!")
        print("*** WARNING: TODO: UPDATE IMPORT_DATA WITH DEFAULT VALUES! (e.g. calc status, user pwd, ...)")
        print("DONE.")

    return ret_dict


class HTMLGetLinksParser(HTMLParser):
    def __init__(self, filter_extension=None):
        """
        If a filter_extension is passed, only links with extension matching
        the given one will be returned.
        """
        self.filter_extension = filter_extension
        self.links = []
        super(HTMLGetLinksParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        """
        Store the urls encountered, if they match the request.
        """
        if tag == 'a':
            for k, v in attrs:
                if k == 'href':
                    if (self.filter_extension is None or
                            v.endswith('.{}'.format(self.filter_extension))):
                        self.links.append(v)

    def get_links(self):
        """
        Return the links that were found during the parsing phase.
        """
        return self.links


def get_valid_import_links(url):
    """
    Open the given URL, parse the HTML and return a list of valid links where
    the link file has a .aiida extension.
    """
    from six.moves import urllib

    request = urllib.request.urlopen(url)
    parser = HTMLGetLinksParser(filter_extension='aiida')
    parser.feed(request.read())

    return_urls = []

    for link in parser.get_links():
        return_urls.append(urllib.parse.urljoin(request.geturl(), link))

    return return_urls


def serialize_field(data, track_conversion=False):
    """
    Serialize a single field.

    :todo: Generalize such that it the proper function is selected also during
        import
    """
    import datetime
    import pytz
    from uuid import UUID

    if isinstance(data, dict):
        if track_conversion:
            ret_data = {}
            ret_conversion = {}
            for k, v in data.items():
                ret_data[k], ret_conversion[k] = serialize_field(
                    data=v, track_conversion=track_conversion)
        else:
            ret_data = {k: serialize_field(data=v,
                                           track_conversion=track_conversion)
                        for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        if track_conversion:
            ret_data = []
            ret_conversion = []
            for value in data:
                this_data, this_conversion = serialize_field(
                    data=value, track_conversion=track_conversion)
                ret_data.append(this_data)
                ret_conversion.append(this_conversion)
        else:
            ret_data = [serialize_field(
                data=value, track_conversion=track_conversion)
                for value in data]
    elif isinstance(data, datetime.datetime):
        # Note: requires timezone-aware objects!
        ret_data = data.astimezone(pytz.utc).strftime(
            '%Y-%m-%dT%H:%M:%S.%f')
        ret_conversion = 'date'
    elif isinstance(data, UUID):
        ret_data = str(data)
        ret_conversion = None
    else:
        ret_data = data
        ret_conversion = None

    if track_conversion:
        return (ret_data, ret_conversion)
    else:
        return ret_data


def serialize_dict(datadict, remove_fields=[], rename_fields={},
                   track_conversion=False):
    """
    Serialize the dict using the serialize_field function to serialize
    each field.

    :param remove_fields: a list of strings.
      If a field with key inside the remove_fields list is found,
      it is removed from the dict.

      This is only used at level-0, no removal
      is possible at deeper levels.

    :param rename_fields: a dictionary in the format
      ``{"oldname": "newname"}``.

      If the "oldname" key is found, it is replaced with the
      "newname" string in the output dictionary.

      This is only used at level-0, no renaming
      is possible at deeper levels.
    :param track_conversion: if True, a tuple is returned, where the first
      element is the serialized dictionary, and the second element is a
      dictionary with the information on the serialized fields.
    """
    ret_dict = {}

    conversions = {}

    for k, v in datadict.items():
        if k not in remove_fields:
            # rename_fields.get(k,k): use the replacement if found in rename_fields,
            # otherwise use 'k' as the default value.
            if track_conversion:
                (ret_dict[rename_fields.get(k, k)],
                 conversions[rename_fields.get(k, k)]) = serialize_field(
                    data=v, track_conversion=track_conversion)
            else:
                ret_dict[rename_fields.get(k, k)] = serialize_field(
                    data=v, track_conversion=track_conversion)

    if track_conversion:
        return (ret_dict, conversions)
    else:
        return ret_dict


def fill_in_query(partial_query, originating_entity_str, current_entity_str,
                  tag_suffixes=[], entity_separator="_"):
    """
    This function recursively constructs QueryBuilder queries that are needed
    for the SQLA export function. To manage to construct such queries, the
    relationship dictionary is consulted (which shows how to reference
    different AiiDA entities in QueryBuilder.
    To find the dependencies of the relationships of the exported data, the
    get_all_fields_info_sqla (which described the exported schema and its
    dependencies) is consulted.
    """

    relationship_dic = {
        "Node": {
            "Computer": "with_computer",
            "Group": "with_group",
            "User": "with_user",
            "Log": "with_log",
            "Comment": "with_comment"
        },
        "Group": {
            "Node": "with_node"
        },
        "Computer": {
            "Node": "with_node"
        },
        "User": {
            "Node": "with_node",
            "Group": "with_group",
            "Comment": "with_comment",
        },
        "Log": {
            "Node": "with_node"
        },
        "Comment": {
            "Node": "with_node",
            "User": "with_user"
        }
    }

    all_fields_info, unique_identifiers = get_all_fields_info()

    entity_prop = all_fields_info[current_entity_str].keys()

    project_cols = ["id"]
    for prop in entity_prop:
        nprop = prop
        if current_entity_str in file_fields_to_model_fields:
            if prop in file_fields_to_model_fields[current_entity_str]:
                nprop = file_fields_to_model_fields[current_entity_str][prop]

        project_cols.append(nprop)

    # Here we should reference the entity of the main query
    current_entity_mod = entity_names_to_entities[current_entity_str]

    rel_string = relationship_dic[current_entity_str][originating_entity_str]
    mydict = {rel_string: entity_separator.join(tag_suffixes)}

    partial_query.append(current_entity_mod,
                         tag=entity_separator.join(tag_suffixes) +
                             entity_separator + current_entity_str,
                         project=project_cols, outerjoin=True, **mydict)

    # prepare the recursion for the referenced entities
    foreign_fields = {k: v for k, v in
                      all_fields_info[
                          current_entity_str].items()
                      # all_fields_info[model_name].items()
                      if 'requires' in v}

    new_tag_suffixes = tag_suffixes + [current_entity_str]
    for k, v in foreign_fields.items():
        ref_model_name = v['requires']
        fill_in_query(partial_query, current_entity_str, ref_model_name,
                      new_tag_suffixes)


def export_tree(what, folder, allowed_licenses=None, forbidden_licenses=None,
                silent=False, input_forward=False, create_reversed=True,
                return_reversed=False, call_reversed=False, include_comments=True,
                include_logs=True, **kwargs):
    """
    Export the entries passed in the 'what' list to a file tree.
    :todo: limit the export to finished or failed calculations.
    :param what: a list of entity instances; they can belong to
    different models/entities.
    :param folder: a :py:class:`Folder <aiida.common.folders.Folder>` object
    :param input_forward: Follow forward INPUT links (recursively) when
    calculating the node set to export.
    :param create_reversed: Follow reversed CREATE links (recursively) when
    calculating the node set to export.
    :param return_reversed: Follow reversed RETURN links (recursively) when
    calculating the node set to export.
    :param call_reversed: Follow reversed CALL links (recursively) when
    calculating the node set to export.
    :param allowed_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param forbidden_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param include_comments: Bool: In-/exclude export of comments for given node(s).
    Default: True, *include* comments in export (as well as relevant users).
    :param include_logs: Bool: In-/exclude export of logs for given node(s).
    Default: True, *include* logs in export.
    :param silent: suppress debug prints
    :raises LicensingException: if any node is licensed under forbidden
    license
    """
    import os
    import aiida
    from aiida.orm import Node, Data, Group, Log, Comment
    from aiida.orm import ProcessNode
    from aiida.common.exceptions import ContentNotExistent
    from aiida.common.links import LinkType
    from aiida.common.folders import RepositoryFolder
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.common import json
    from django.core.exceptions import ImproperlyConfigured

    if not silent:
        print("STARTING EXPORT...")

    EXPORT_VERSION = '0.4'

    all_fields_info, unique_identifiers = get_all_fields_info()

    # The set that contains the nodes ids of the nodes that should be exported
    to_be_exported = set()

    given_data_entry_ids = set()
    given_calculation_entry_ids = set()
    given_group_entry_ids = set()
    given_computer_entry_ids = set()
    given_groups = set()
    given_log_entry_ids = set()
    given_comment_entry_ids = set()

    # I store a list of the actual dbnodes
    for entry in what:
        # This returns the class name (as in imports). E.g. for a model node:
        # aiida.backends.djsite.db.models.DbNode
        entry_class_string = get_class_string(entry)
        # Now a load the backend-independent name into entry_entity_name, e.g. Node!
        entry_entity_name = schema_to_entity_names(entry_class_string)
        if issubclass(entry.__class__, Group):
            given_group_entry_ids.add(entry.id)
            given_groups.add(entry)
        elif issubclass(entry.__class__, Node):
            if issubclass(entry.__class__, Data):
                given_data_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, ProcessNode):
                given_calculation_entry_ids.add(entry.pk)
        elif issubclass(entry.__class__, Computer):
            given_computer_entry_ids.add(entry.pk)
        else:
            raise ValueError("I was given {} ({}), which is not a Node, Computer, or Group instance"
                            .format(entry, type(entry)))

    # Add all the nodes contained within the specified groups
    for group in given_groups:
        for entry in group.nodes:
            if issubclass(entry.__class__, Data):
                given_data_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, ProcessNode):
                given_calculation_entry_ids.add(entry.pk)

    # We will iteratively explore the AiiDA graph to find further nodes that
    # should also be exported.

    # We repeat until there are no further nodes to be visited
    while given_calculation_entry_ids or given_data_entry_ids:

        # If is is a calculation node
        if given_calculation_entry_ids:
            curr_node_id = given_calculation_entry_ids.pop()
            # If it is already visited continue to the next node
            if curr_node_id in to_be_exported:
                continue
            # Otherwise say that it is a node to be exported
            else:
                to_be_exported.add(curr_node_id)

            # INPUT(Data, ProcessNode) - Reversed
            qb = QueryBuilder()
            qb.append(Data, tag='predecessor', project=['id'])
            qb.append(ProcessNode, with_incoming='predecessor',
                      filters={'id': {'==': curr_node_id}},
                      edge_filters={'type': {'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]}})
            res = {_[0] for _ in qb.all()}
            given_data_entry_ids.update(res - to_be_exported)

            # INPUT(Data, ProcessNode) - Forward
            if input_forward:
                qb = QueryBuilder()
                qb.append(Data, tag='predecessor', project=['id'],
                          filters={'id': {'==': curr_node_id}})
                qb.append(ProcessNode, with_incoming='predecessor',
                      edge_filters={'type': {'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]}})
                res = {_[0] for _ in qb.all()}
                given_data_entry_ids.update(res - to_be_exported)

            # CREATE/RETURN(ProcessNode, Data) - Forward
            qb = QueryBuilder()
            qb.append(ProcessNode, tag='predecessor',
                      filters={'id': {'==': curr_node_id}})
            qb.append(Data, with_incoming='predecessor', project=['id'],
                      edge_filters={
                          'type': {
                              'in': [LinkType.CREATE.value,
                                     LinkType.RETURN.value]}})
            res = {_[0] for _ in qb.all()}
            given_data_entry_ids.update(res - to_be_exported)

            # CREATE(ProcessNode, Data) - Reversed
            if create_reversed:
                qb = QueryBuilder()
                qb.append(ProcessNode, tag='predecessor')
                qb.append(Data, with_incoming='predecessor', project=['id'],
                          filters={'id': {'==': curr_node_id}},
                          edge_filters={
                              'type': {
                                  'in': [LinkType.CREATE.value]}})
                res = {_[0] for _ in qb.all()}
                given_data_entry_ids.update(res - to_be_exported)

            # RETURN(ProcessNode, Data) - Reversed
            if return_reversed:
                qb = QueryBuilder()
                qb.append(ProcessNode, tag='predecessor')
                qb.append(Data, with_incoming='predecessor', project=['id'],
                          filters={'id': {'==': curr_node_id}},
                          edge_filters={
                              'type': {
                                  'in': [LinkType.RETURN.value]}})
                res = {_[0] for _ in qb.all()}
                given_data_entry_ids.update(res - to_be_exported)

            # CALL(ProcessNode, ProcessNode) - Forward
            qb = QueryBuilder()
            qb.append(ProcessNode, tag='predecessor',
                      filters={'id': {'==': curr_node_id}})
            qb.append(ProcessNode, with_incoming='predecessor', project=['id'],
                edge_filters={'type': {'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]}})
            res = {_[0] for _ in qb.all()}
            given_calculation_entry_ids.update(res - to_be_exported)

            # CALL(ProcessNode, ProcessNode) - Reversed
            if call_reversed:
                qb = QueryBuilder()
                qb.append(ProcessNode, tag='predecessor')
                qb.append(ProcessNode, with_incoming='predecessor', project=['id'],
                    filters={'id': {'==': curr_node_id}},
                    edge_filters={'type': {'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]}})
                res = {_[0] for _ in qb.all()}
                given_calculation_entry_ids.update(res - to_be_exported)


        # If it is a Data node
        else:
            curr_node_id = given_data_entry_ids.pop()
            # If it is already visited continue to the next node
            if curr_node_id in to_be_exported:
                continue
            # Otherwise say that it is a node to be exported
            else:
                to_be_exported.add(curr_node_id)

            # Case 2:
            # CREATE(ProcessNode, Data) - Reversed
            if create_reversed:
                qb = QueryBuilder()
                qb.append(ProcessNode, tag='predecessor', project=['id'])
                qb.append(Data, with_incoming='predecessor',
                          filters={'id': {'==': curr_node_id}},
                          edge_filters={
                              'type': {
                                  'in': [LinkType.CREATE.value]}})
                res = {_[0] for _ in qb.all()}
                given_calculation_entry_ids.update(res - to_be_exported)

            # Case 3:
            # RETURN(ProcessNode, Data) - Reversed
            if return_reversed:
                qb = QueryBuilder()
                qb.append(ProcessNode, tag='predecessor', project=['id'])
                qb.append(Data, with_incoming='predecessor',
                          filters={'id': {'==': curr_node_id}},
                          edge_filters={
                              'type': {
                                  'in': [LinkType.RETURN.value]}})
                res = {_[0] for _ in qb.all()}
                given_calculation_entry_ids.update(res - to_be_exported)

    ## Universal "entities" attributed to all types of nodes
    # Logs
    if include_logs and to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = QueryBuilder()
        builder.append(Log, filters={'dbnode_id': {'in': to_be_exported}}, project=['id'])
        res = {_[0] for _ in builder.all()}
        given_log_entry_ids.update(res)

    # Comments
    if include_comments and to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = QueryBuilder()
        builder.append(Comment, filters={'dbnode_id': {'in': to_be_exported}}, project=['id'])
        res = {_[0] for _ in builder.all()}
        given_comment_entry_ids.update(res)

    # Here we get all the columns that we plan to project per entity that we
    # would like to extract
    given_entities = list()
    if len(given_group_entry_ids) > 0:
        given_entities.append(GROUP_ENTITY_NAME)
    if len(to_be_exported) > 0:
        given_entities.append(NODE_ENTITY_NAME)
    if len(given_computer_entry_ids) > 0:
        given_entities.append(COMPUTER_ENTITY_NAME)
    if len(given_log_entry_ids) > 0:
        given_entities.append(LOG_ENTITY_NAME)
    if len(given_comment_entry_ids) > 0:
        given_entities.append(COMMENT_ENTITY_NAME)

    entries_to_add = dict()
    for given_entity in given_entities:
        project_cols = ["id"]
        # The following gets a list of fields that we need,
        # e.g. user, mtime, uuid, computer
        entity_prop = all_fields_info[given_entity].keys()

        # Here we do the necessary renaming of properties
        for prop in entity_prop:
            # nprop contains the list of projections
            nprop = (file_fields_to_model_fields[given_entity][prop]
                     if prop in file_fields_to_model_fields[given_entity]
                     else prop)
            project_cols.append(nprop)

        # Getting the ids that correspond to the right entity
        if given_entity == GROUP_ENTITY_NAME:
            entry_ids_to_add = given_group_entry_ids
        elif given_entity == NODE_ENTITY_NAME:
            entry_ids_to_add = to_be_exported
        elif given_entity == COMPUTER_ENTITY_NAME:
            entry_ids_to_add = given_computer_entry_ids
        elif given_entity == LOG_ENTITY_NAME:
            entry_ids_to_add = given_log_entry_ids
        elif given_entity == COMMENT_ENTITY_NAME:
            entry_ids_to_add = given_comment_entry_ids

        qb = QueryBuilder()
        qb.append(entity_names_to_entities[given_entity],
                  filters={"id": {"in": entry_ids_to_add}},
                  project=project_cols,
                  tag=given_entity, outerjoin=True)
        entries_to_add[given_entity] = qb

    # TODO (Spyros) To see better! Especially for functional licenses
    # Check the licenses of exported data.
    if allowed_licenses is not None or forbidden_licenses is not None:
        qb = QueryBuilder()
        qb.append(Node, project=["id", "attributes.source.license"],
                  filters={"id": {"in": to_be_exported}})
        # Skip those nodes where the license is not set (this is the standard behavior with Django)
        node_licenses = list((a, b) for [a, b] in qb.all() if b is not None)
        check_licences(node_licenses, allowed_licenses, forbidden_licenses)

    ############################################################
    ##### Start automatic recursive export data generation #####
    ############################################################
    if not silent:
        print("STORING DATABASE ENTRIES...")

    export_data = dict()
    entity_separator = '_'
    for entity_name, partial_query in entries_to_add.items():

        foreign_fields = {k: v for k, v in
                          all_fields_info[entity_name].items()
                          # all_fields_info[model_name].items()
                          if 'requires' in v}

        for k, v in foreign_fields.items():
            ref_model_name = v['requires']
            fill_in_query(partial_query, entity_name, ref_model_name,
                          [entity_name], entity_separator)

        for temp_d in partial_query.iterdict():
            for k in temp_d.keys():
                # Get current entity
                current_entity = k.split(entity_separator)[-1]

                # This is a empty result of an outer join.
                # It should not be taken into account.
                if temp_d[k]["id"] is None:
                    continue

                temp_d2 = {
                    temp_d[k]["id"]:
                        serialize_dict(temp_d[k],
                                       remove_fields=['id'],
                                       rename_fields=
                                       model_fields_to_file_fields[current_entity])}
                try:
                    export_data[current_entity].update(temp_d2)
                except KeyError:
                    export_data[current_entity] = temp_d2

    ######################################
    # Manually manage links and attributes
    ######################################
    # I use .get because there may be no nodes to export
    all_nodes_pk = list()
    if NODE_ENTITY_NAME in export_data:
        all_nodes_pk.extend(export_data.get(NODE_ENTITY_NAME).keys())

    if sum(len(model_data) for model_data in export_data.values()) == 0:
        if not silent:
            print("No nodes to store, exiting...")
        return

    if not silent:
        print("Exporting a total of {} db entries, of which {} nodes."
              .format(sum(len(model_data) for model_data in export_data.values()),
                      len(all_nodes_pk)))

    ## ATTRIBUTES
    if not silent:
        print("STORING NODE ATTRIBUTES...")
    node_attributes = {}
    node_attributes_conversion = {}

    # A second QueryBuilder query to get the attributes. See if this can be
    # optimized
    if len(all_nodes_pk) > 0:
        all_nodes_query = QueryBuilder()
        all_nodes_query.append(Node, filters={"id": {"in": all_nodes_pk}},
                               project=["*"])
        for res in all_nodes_query.iterall():
            n = res[0]
            (node_attributes[str(n.pk)],
             node_attributes_conversion[str(n.pk)]) = serialize_dict(
                n.attributes, track_conversion=True)

    ## EXTRAS
    if not silent:
        print("STORING NODE EXTRAS...")
    node_extras = {}
    node_extras_conversion = {}

    # A second QueryBuilder query to get the extras. See if this can be
    # optimized
    if len(all_nodes_pk) > 0:
        all_nodes_query = QueryBuilder()
        all_nodes_query.append(Node, filters={"id": {"in": all_nodes_pk}},
                               project=["*"])
        for res in all_nodes_query.iterall():
            n = res[0]
            (node_extras[str(n.pk)],
             node_extras_conversion[str(n.pk)]) = serialize_dict(n.extras, track_conversion=True)

    if not silent:
        print("STORING NODE LINKS...")

    links_uuid_dict = dict()
    if len(all_nodes_pk) > 0:
        # INPUT (Data, ProcessNode) - Forward, by the ProcessNode node
        if input_forward:
            # INPUT (Data, ProcessNode)
            links_qb = QueryBuilder()
            links_qb.append(Data,
                            project=['uuid'], tag='input',
                            filters = {'id': {'in': all_nodes_pk}})
            links_qb.append(ProcessNode,
                            project=['uuid'], tag='output',
                            edge_filters={'type': {'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]}},
                            edge_project=['label', 'type'], with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type':str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

        # INPUT (Data, ProcessNode) - Backward, by the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(Data,
                        project=['uuid'], tag='input')
        links_qb.append(ProcessNode,
                        project=['uuid'], tag='output',
                        filters={'id': {'in': all_nodes_pk}},
                        edge_filters={'type': {'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]}},
                        edge_project=['label', 'type'], with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type':str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # CREATE (ProcessNode, Data) - Forward, by the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(ProcessNode,
                        project=['uuid'], tag='input',
                        filters={'id': {'in': all_nodes_pk}})
        links_qb.append(Data,
                        project=['uuid'], tag='output',
                        edge_filters={'type': {'==': LinkType.CREATE.value}},
                        edge_project=['label', 'type'], with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type':str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # CREATE (ProcessNode, Data) - Backward, by the Data node
        if create_reversed:
            links_qb = QueryBuilder()
            links_qb.append(ProcessNode,
                            project=['uuid'], tag='input',
                            filters={'id': {'in': all_nodes_pk}})
            links_qb.append(Data,
                            project=['uuid'], tag='output',
                            edge_filters={'type': {'==': LinkType.CREATE.value}},
                            edge_project=['label', 'type'], with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type':str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

        # RETURN (ProcessNode, Data) - Forward, by the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(ProcessNode,
                        project=['uuid'], tag='input',
                        filters={'id': {'in': all_nodes_pk}})
        links_qb.append(Data,
                        project=['uuid'], tag='output',
                        edge_filters={'type': {'==': LinkType.RETURN.value}},
                        edge_project=['label', 'type'], with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type':str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # RETURN (ProcessNode, Data) - Backward, by the Data node
        if return_reversed:
            links_qb = QueryBuilder()
            links_qb.append(ProcessNode,
                            project=['uuid'], tag='input')
            links_qb.append(Data,
                            project=['uuid'], tag='output',
                            filters={'id': {'in': all_nodes_pk}},
                            edge_filters={'type': {'==': LinkType.RETURN.value}},
                            edge_project=['label', 'type'], with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type':str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

        # CALL (ProcessNode [caller], ProcessNode [called]) - Forward, by
        # the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(ProcessNode,
                        project=['uuid'], tag='input',
                        filters={'id': {'in': all_nodes_pk}})
        links_qb.append(ProcessNode,
                        project=['uuid'], tag='output',
                        edge_filters={'type': {'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]}},
                        edge_project=['label', 'type'], with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type':str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # CALL (ProcessNode [caller], ProcessNode [called]) - Backward,
        # by the ProcessNode [called] node
        if call_reversed:
            links_qb = QueryBuilder()
            links_qb.append(ProcessNode,
                            project=['uuid'], tag='input')
            links_qb.append(ProcessNode,
                            project=['uuid'], tag='output',
                            filters={'id': {'in': all_nodes_pk}},
                            edge_filters={'type': {'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]}},
                            edge_project=['label', 'type'], with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type':str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

    links_uuid = list(links_uuid_dict.values())

    if not silent:
        print("STORING GROUP ELEMENTS...")
    groups_uuid = dict()
    # If a group is in the exported date, we export the group/node correlation
    if GROUP_ENTITY_NAME in export_data:
        for curr_group in export_data[GROUP_ENTITY_NAME]:
            group_uuid_qb = QueryBuilder()
            group_uuid_qb.append(entity_names_to_entities[GROUP_ENTITY_NAME],
                                 filters={'id': {'==': curr_group}},
                                 project=['uuid'], tag='group')
            group_uuid_qb.append(entity_names_to_entities[NODE_ENTITY_NAME],
                                 project=['uuid'], with_group='group')
            for res in group_uuid_qb.iterall():
                if str(res[0]) in groups_uuid:
                    groups_uuid[str(res[0])].append(str(res[1]))
                else:
                    groups_uuid[str(res[0])] = [str(res[1])]

    ######################################
    # Now I store
    ######################################
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder('nodes', create=True,
                                         reset_limit=True)

    # Add the proper signatures to the exported data
    for entity_name in export_data.keys():
        export_data[entity_name] = (
            export_data.pop(entity_name))

    if not silent:
        print("STORING DATA...")

    data = {
        'node_attributes': node_attributes,
        'node_attributes_conversion': node_attributes_conversion,
        'node_extras': node_extras,
        'node_extras_conversion': node_extras_conversion,
        'export_data': export_data,
        'links_uuid': links_uuid,
        'groups_uuid': groups_uuid,
    }

    # N.B. We're really calling zipfolder.open
    with folder.open('data.json', mode='w') as fhandle:
        # fhandle.write(json.dumps(data, cls=UUIDEncoder))
        fhandle.write(json.dumps(data))

    # Add proper signature to unique identifiers & all_fields_info
    # Ignore if a key doesn't exist in any of the two dictionaries

    metadata = {
        'aiida_version': aiida.get_version(),
        'export_version': EXPORT_VERSION,
        'all_fields_info': all_fields_info,
        'unique_identifiers': unique_identifiers,
    }

    with folder.open('metadata.json', "w") as fhandle:
        fhandle.write(json.dumps(metadata))

    if silent is not True:
        print("STORING FILES...")

    # If there are no nodes, there are no files to store
    if len(all_nodes_pk) > 0:
        # Large speed increase by not getting the node itself and looping in memory
        # in python, but just getting the uuid
        uuid_query = QueryBuilder()
        uuid_query.append(Node, filters={"id": {"in": all_nodes_pk}},
                          project=["uuid"])
        for res in uuid_query.all():
            uuid = str(res[0])
            sharded_uuid = export_shard_uuid(uuid)

            # Important to set create=False, otherwise creates
            # twice a subfolder. Maybe this is a bug of insert_path??
            thisnodefolder = nodesubfolder.get_subfolder(
                sharded_uuid, create=False,
                reset_limit=True)
            # In this way, I copy the content of the folder, and not the folder itself
            src = RepositoryFolder(section=Repository._section_name, uuid=uuid).abspath
            thisnodefolder.insert_path(src=src, dest_name='.')


def check_licences(node_licenses, allowed_licenses, forbidden_licenses):
    from aiida.common.exceptions import LicensingException
    from inspect import isfunction

    for pk, license in node_licenses:
        if allowed_licenses is not None:
            try:
                if isfunction(allowed_licenses):
                    try:
                        if not allowed_licenses(license):
                            raise LicensingException
                    except Exception as e:
                        raise LicensingException
                else:
                    if license not in allowed_licenses:
                        raise LicensingException
            except LicensingException:
                raise LicensingException("Node {} is licensed "
                                         "under {} license, which "
                                         "is not in the list of "
                                         "allowed licenses".format(
                    pk, license))
        if forbidden_licenses is not None:
            try:
                if isfunction(forbidden_licenses):
                    try:
                        if forbidden_licenses(license):
                            raise LicensingException
                    except Exception as e:
                        raise LicensingException
                else:
                    if license in forbidden_licenses:
                        raise LicensingException
            except LicensingException:
                raise LicensingException("Node {} is licensed "
                                         "under {} license, which "
                                         "is in the list of "
                                         "forbidden licenses".format(
                    pk, license))


def get_all_parents_dj(node_pks):
    """
    Get all the parents of given nodes
    :param node_pks: one node pk or an iterable of node pks
    :return: a list of aiida objects with all the parents of the nodes
    """
    from aiida.backends.djsite.db import models

    try:
        the_node_pks = list(node_pks)
    except TypeError:
        the_node_pks = [node_pks]

    parents = models.DbNode.objects.none()
    q_inputs = models.DbNode.aiidaobjects.filter(outputs__pk__in=the_node_pks).distinct()
    while q_inputs.count() > 0:
        inputs = list(q_inputs)
        parents = q_inputs | parents.all()
        q_inputs = models.DbNode.aiidaobjects.filter(outputs__in=inputs).distinct()
    return parents


class MyWritingZipFile(object):
    def __init__(self, zipfile, fname):
        self._zipfile = zipfile
        self._fname = fname
        self._buffer = None

    def open(self):
        from six.moves import StringIO as StringIO

        if self._buffer is not None:
            raise IOError("Cannot open again!")
        self._buffer = StringIO()

    def write(self, data):
        self._buffer.write(data)

    def close(self):
        self._buffer.seek(0)
        self._zipfile.writestr(self._fname, self._buffer.read())
        self._buffer = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class ZipFolder(object):
    """
    To improve: if zipfile is closed, do something
    (e.g. add explicit open method, rename open to openfile,
    set _zipfile to None, ...)
    """

    def __init__(self, zipfolder_or_fname, mode=None, subfolder='.',
                use_compression=True, allowZip64=True):
        """
        :param zipfolder_or_fname: either another ZipFolder instance,
          of which you want to get a subfolder, or a filename to create.
        :param mode: the file mode; see the zipfile.ZipFile docs for valid
          strings. Note: can be specified only if zipfolder_or_fname is a
          string (the filename to generate)
        :param subfolder: the subfolder that specified the "current working
          directory" in the zip file. If zipfolder_or_fname is a ZipFolder,
          subfolder is a relative path from zipfolder_or_fname.subfolder
        :param use_compression: either True, to compress files in the Zip, or
          False if you just want to pack them together without compressing.
          It is ignored if zipfolder_or_fname is a ZipFolder isntance.
        """
        import zipfile
        import os

        if isinstance(zipfolder_or_fname, six.string_types):
            the_mode = mode
            if the_mode is None:
                the_mode = "r"
            if use_compression:
                compression = zipfile.ZIP_DEFLATED
            else:
                compression = zipfile.ZIP_STORED
            self._zipfile = zipfile.ZipFile(zipfolder_or_fname, mode=the_mode,
                                            compression=compression,
                                            allowZip64=allowZip64)
            self._pwd = subfolder
        else:
            if mode is not None:
                raise ValueError("Cannot specify 'mode' when passing a ZipFolder")
            self._zipfile = zipfolder_or_fname._zipfile
            self._pwd = os.path.join(zipfolder_or_fname.pwd, subfolder)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self._zipfile.close()

    @property
    def pwd(self):
        return self._pwd

    def open(self, fname, mode='r'):
        if mode == 'w':
            return MyWritingZipFile(
                zipfile=self._zipfile, fname=self._get_internal_path(fname))
        else:
            return self._zipfile.open(self._get_internal_path(fname), mode)

    def _get_internal_path(self, filename):
        import os
        return os.path.normpath(os.path.join(self.pwd, filename))

    def get_subfolder(self, subfolder, create=False, reset_limit=False):
        # reset_limit: ignored
        # create: ignored, for the time being
        subfolder = ZipFolder(self, subfolder=subfolder)
        return subfolder

    def insert_path(self, src, dest_name=None, overwrite=True):
        import os

        if dest_name is None:
            base_filename = six.text_type(os.path.basename(src))
        else:
            base_filename = six.text_type(dest_name)

        base_filename = self._get_internal_path(base_filename)

        src = six.text_type(src)

        if not os.path.isabs(src):
            raise ValueError("src must be an absolute path in insert_file")

        if not overwrite:
            try:
                self._zipfile.getinfo(base_filename)
                exists = True
            except KeyError:
                exists = False
            if exists:
                raise IOError("destination already exists: {}".format(
                    base_filename))

        # print src, filename
        if os.path.isdir(src):
            for dirpath, dirnames, filenames in os.walk(src):
                relpath = os.path.relpath(dirpath, src)
                for fn in dirnames + filenames:
                    real_src = os.path.join(dirpath, fn)
                    real_dest = os.path.join(base_filename, relpath, fn)
                    self._zipfile.write(real_src,
                                        real_dest)
        else:
            self._zipfile.write(src, base_filename)


def export_zip(what, outfile='testzip', overwrite=False,
               silent=False, use_compression=True, **kwargs):
    import os

    if not overwrite and os.path.exists(outfile):
        raise IOError("the output file '{}' already exists".format(outfile))

    import time
    t = time.time()
    with ZipFolder(outfile, mode='w', use_compression=use_compression) as folder:
        export_tree(what, folder=folder, silent=silent, **kwargs)
    if not silent:
        print("File written in {:10.3g} s.".format(time.time() - t))


def export(what, outfile='export_data.aiida.tar.gz', overwrite=False,
           silent=False, **kwargs):
    """
    Export the entries passed in the 'what' list to a file tree.
    :todo: limit the export to finished or failed calculations.
    :param what: a list of entity instances; they can belong to
    different models/entities.
    :param input_forward: Follow forward INPUT links (recursively) when
    calculating the node set to export.
    :param create_reversed: Follow reversed CREATE links (recursively) when
    calculating the node set to export.
    :param return_reversed: Follow reversed RETURN links (recursively) when
    calculating the node set to export.
    :param call_reversed: Follow reversed CALL links (recursively) when
    calculating the node set to export.
    :param allowed_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param forbidden_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param outfile: the filename of the file on which to export
    :param overwrite: if True, overwrite the output file without asking.
    if False, raise an IOError in this case.
    :param silent: suppress debug print

    :raise IOError: if overwrite==False and the filename already exists.
    """
    import os
    import tarfile
    import time

    from aiida.common.folders import SandboxFolder

    if not overwrite and os.path.exists(outfile):
        raise IOError("The output file '{}' already "
                      "exists".format(outfile))

    folder = SandboxFolder()
    t1 = time.time()
    export_tree(what, folder=folder, silent=silent, **kwargs)

    t2 = time.time()

    if not silent:
        print("COMPRESSING...")

    t3 = time.time()
    with tarfile.open(outfile, "w:gz", format=tarfile.PAX_FORMAT,
                      dereference=True) as tar:
        tar.add(folder.abspath, arcname="")
    t4 = time.time()

    if not silent:
        filecr_time = t2 - t1
        filecomp_time = t4 - t3
        print("Exported in {:6.2g}s, compressed in {:6.2g}s, total: {:6.2g}s."
              .format(filecr_time, filecomp_time, filecr_time + filecomp_time))

    if not silent:
        print("DONE.")

# Following code: to serialize the date directly when dumping into JSON.
# In our case, it is better to have a finer control on how to parse fields.

# def default_jsondump(data):
#    import datetime
#
#    if isinstance(data, datetime.datetime):
#        return data.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
#
#    raise TypeError(repr(data) + " is not JSON serializable")
# with open('testout.json', 'w') as f:
#    json.dump({
#            'entries': serialized_entries,
#        },
#        f,
#        default=default_jsondump)
