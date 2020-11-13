# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
""" Configuration file for AiiDA Import/Export module """
from enum import Enum
from aiida.orm import Computer, Group, Node, User, Log, Comment

__all__ = ('EXPORT_VERSION',)

# Current export version
EXPORT_VERSION = '0.10'


class ExportFileFormat(str, Enum):
    """Archive file formats"""
    ZIP = 'zip'
    TAR_GZIPPED = 'tar.gz'


DUPL_SUFFIX = ' (Imported #{})'

# The name of the subfolder in which the node files are stored
NODES_EXPORT_SUBFOLDER = 'nodes'

# Giving names to the various entities. Attributes and links are not AiiDA
# entities but we will refer to them as entities in the file (to simplify
# references to them).
NODE_ENTITY_NAME = 'Node'
GROUP_ENTITY_NAME = 'Group'
COMPUTER_ENTITY_NAME = 'Computer'
USER_ENTITY_NAME = 'User'
LOG_ENTITY_NAME = 'Log'
COMMENT_ENTITY_NAME = 'Comment'

# The signatures used to reference the entities in the archive file
NODE_SIGNATURE = 'aiida.backends.djsite.db.models.DbNode'
GROUP_SIGNATURE = 'aiida.backends.djsite.db.models.DbGroup'
COMPUTER_SIGNATURE = 'aiida.backends.djsite.db.models.DbComputer'
USER_SIGNATURE = 'aiida.backends.djsite.db.models.DbUser'
LOG_SIGNATURE = 'aiida.backends.djsite.db.models.DbLog'
COMMENT_SIGNATURE = 'aiida.backends.djsite.db.models.DbComment'

# Mapping from entity names to signatures (used by the SQLA import/export)
entity_names_to_signatures = {
    NODE_ENTITY_NAME: NODE_SIGNATURE,
    GROUP_ENTITY_NAME: GROUP_SIGNATURE,
    COMPUTER_ENTITY_NAME: COMPUTER_SIGNATURE,
    USER_ENTITY_NAME: USER_SIGNATURE,
    LOG_ENTITY_NAME: LOG_SIGNATURE,
    COMMENT_ENTITY_NAME: COMMENT_SIGNATURE
}

# Mapping from signatures to entity names (used by the SQLA import/export)
signatures_to_entity_names = {
    NODE_SIGNATURE: NODE_ENTITY_NAME,
    GROUP_SIGNATURE: GROUP_ENTITY_NAME,
    COMPUTER_SIGNATURE: COMPUTER_ENTITY_NAME,
    USER_SIGNATURE: USER_ENTITY_NAME,
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

# Mapping of entity names to SQLA class paths
entity_names_to_sqla_schema = {
    NODE_ENTITY_NAME: 'aiida.backends.sqlalchemy.models.node.DbNode',
    GROUP_ENTITY_NAME: 'aiida.backends.sqlalchemy.models.group.DbGroup',
    COMPUTER_ENTITY_NAME: 'aiida.backends.sqlalchemy.models.computer.DbComputer',
    USER_ENTITY_NAME: 'aiida.backends.sqlalchemy.models.user.DbUser',
    LOG_ENTITY_NAME: 'aiida.backends.sqlalchemy.models.log.DbLog',
    COMMENT_ENTITY_NAME: 'aiida.backends.sqlalchemy.models.comment.DbComment'
}

# Mapping of the archive file fields (that coincide with the Django fields) to
# model fields that can be used for the query of the database in both backends.
# These are the names of the fields of the models that belong to the
# corresponding entities.

file_fields_to_model_fields = {
    NODE_ENTITY_NAME: {
        'dbcomputer': 'dbcomputer_id',
        'user': 'user_id'
    },
    GROUP_ENTITY_NAME: {
        'user': 'user_id'
    },
    COMPUTER_ENTITY_NAME: {},
    LOG_ENTITY_NAME: {
        'dbnode': 'dbnode_id'
    },
    COMMENT_ENTITY_NAME: {
        'dbnode': 'dbnode_id',
        'user': 'user_id'
    }
}
# As above but the opposite procedure
model_fields_to_file_fields = {
    NODE_ENTITY_NAME: {
        'dbcomputer_id': 'dbcomputer',
        'user_id': 'user'
    },
    GROUP_ENTITY_NAME: {
        'user_id': 'user'
    },
    COMPUTER_ENTITY_NAME: {},
    USER_ENTITY_NAME: {},
    LOG_ENTITY_NAME: {
        'dbnode_id': 'dbnode'
    },
    COMMENT_ENTITY_NAME: {
        'dbnode_id': 'dbnode',
        'user_id': 'user'
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
        USER_ENTITY_NAME: 'email',
        COMPUTER_ENTITY_NAME: 'uuid',
        NODE_ENTITY_NAME: 'uuid',
        GROUP_ENTITY_NAME: 'uuid',
        LOG_ENTITY_NAME: 'uuid',
        COMMENT_ENTITY_NAME: 'uuid'
    }

    all_fields_info = dict()
    all_fields_info[USER_ENTITY_NAME] = {'last_name': {}, 'first_name': {}, 'institution': {}, 'email': {}}
    all_fields_info[COMPUTER_ENTITY_NAME] = {
        'transport_type': {},
        'hostname': {},
        'description': {},
        'scheduler_type': {},
        'metadata': {},
        'uuid': {},
        'name': {}
    }
    all_fields_info[NODE_ENTITY_NAME] = {
        'ctime': {
            'convert_type': 'date'
        },
        'uuid': {},
        'mtime': {
            'convert_type': 'date'
        },
        'node_type': {},
        'label': {},
        'user': {
            'requires': USER_ENTITY_NAME,
            'related_name': 'dbnodes'
        },
        'dbcomputer': {
            'requires': COMPUTER_ENTITY_NAME,
            'related_name': 'dbnodes'
        },
        'description': {},
        'process_type': {},
        'extras': {
            'convert_type': 'jsonb'
        },
        'attributes': {
            'convert_type': 'jsonb'
        }
    }
    all_fields_info[GROUP_ENTITY_NAME] = {
        'description': {},
        'user': {
            'related_name': 'dbgroups',
            'requires': USER_ENTITY_NAME
        },
        'time': {
            'convert_type': 'date'
        },
        'type_string': {},
        'uuid': {},
        'label': {},
        'extras': {
            'convert_type': 'jsonb'
        }
    }
    all_fields_info[LOG_ENTITY_NAME] = {
        'uuid': {},
        'time': {
            'convert_type': 'date'
        },
        'loggername': {},
        'levelname': {},
        'message': {},
        'metadata': {},
        'dbnode': {
            'related_name': 'dblogs',
            'requires': NODE_ENTITY_NAME
        }
    }
    all_fields_info[COMMENT_ENTITY_NAME] = {
        'uuid': {},
        'ctime': {
            'convert_type': 'date'
        },
        'mtime': {
            'convert_type': 'date'
        },
        'content': {},
        'dbnode': {
            'related_name': 'dbcomments',
            'requires': NODE_ENTITY_NAME
        },
        'user': {
            'related_name': 'dbcomments',
            'requires': USER_ENTITY_NAME
        }
    }
    return all_fields_info, unique_identifiers
