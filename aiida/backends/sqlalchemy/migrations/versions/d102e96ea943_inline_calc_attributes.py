# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migrate attributes from old InlineCalculation that have been transformed into CalcFunctions:

* OLD `sealed` and `function_name` remain the same
* OLD `namespace` becomes `function_namespace`
* OLD `first_line_source_code` becomes `function_starting_line_number`
* OLD `source_file` is moved to repository and dropped from DB
* OLD `source_code` is used to calculate `function_number_of_lines` and dropped from DB
* NEW `exit_status` is initialized at 0
* NEW `process_state` is initialized at "finished"
* NEW `process_label` is set as `Legacy InlineCalculation`

Note 1: old InlineCalculation can be identified by the old keywords, and after migration they will be
identified by having `function_number_of_lines` but no `version`.

Note 2: `exit_status` and `process_state` are initialized to 0 and "finished" respectively because the
CalcFunctions affected are old InlineCalculation, which were only stored if they succeeded. You can check
the relevant code here (line 60 has the execution call, it is stored after that):

https://github.com/aiidateam/aiida-core/blob/v0.12.5/aiida/orm/implementation/django/calculation/inline.py#L60

Revision ID: d102e96ea943
Revises: 0edcdd5a30f0
Create Date: 2021-02-09 16:25:16.106176

"""
# pylint: disable=invalid-name,no-member
# yapf: disable
from alembic import op
from sqlalchemy.sql import text
from aiida.backends.general.migrations import utils

# revision identifiers, used by Alembic.
revision = 'd102e96ea943'
down_revision = '0edcdd5a30f0'
branch_labels = None
depends_on = None


def upgrade():
    """Creates the new attributes"""
    conn = op.get_bind()


    # Creates 'function_namespace' from 'namespace'
    # Creates 'function_starting_line_number' from 'first_line_source_code'
    # Creates 'exit_status', 'process_state' and 'process_label'
    conn.execute(text(
        """
        UPDATE db_dbnode
        SET attributes = attributes || '{
            "exit_status": 0,
            "process_state": "finished",
            "process_label": "Legacy InlineCalculation"
            }'::jsonb ||
            jsonb_build_object(
                'function_starting_line_number', attributes->'first_line_source_code',
                'function_namespace', attributes->'namespace'
                )
        WHERE
            attributes ? 'namespace' AND
            attributes ? 'first_line_source_code' AND
            node_type = 'process.calculation.calcfunction.CalcFunctionNode.';
        """))


    # Sets new 'function_number_of_lines' with the information on 'source_code'
    sqlquery_results = conn.execute(text("SELECT id, attributes -> 'source_code' FROM db_dbnode;"))

    for data_pair in sqlquery_results:
        node_pkid = data_pair[0]
        source_code = data_pair[1]
        num_lines = len(source_code.splitlines())
        conn.execute(text(
            """
            UPDATE db_dbnode
            SET attributes = jsonb_set(attributes, '{function_number_of_lines}', to_jsonb(:value))
            WHERE id = :idnum;
            """), {'value': num_lines, 'idnum': node_pkid})


    # Saves the source file in the repository
    sqlquery_results = conn.execute(text("SELECT uuid, attributes -> 'source_file' FROM db_dbnode;"))

    for data_pair in sqlquery_results:
        node_uuid = data_pair[0]
        node_file = data_pair[1]
        utils.put_object_from_string(node_uuid, 'source_file', node_file)


    # Removes all the old attributes
    conn.execute(text(
        """
        UPDATE db_dbnode
        SET attributes = attributes
            - 'namespace'
            - 'source_code'
            - 'source_file'
            - 'first_line_source_code'
        WHERE
            attributes ? 'namespace' AND
            attributes ? 'first_line_source_code' AND
            node_type = 'process.calculation.calcfunction.CalcFunctionNode.';
        """))

    # ### end Alembic commands ###


def downgrade():
    """Deletes the old attributes"""
    # ### end Alembic commands ###
