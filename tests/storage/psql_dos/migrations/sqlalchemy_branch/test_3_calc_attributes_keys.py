###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests migration of the keys of certain attribute for ProcessNodes and CalcJobNodes: e72ad251bcdb -> 7ca08c391c49"""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator

KEY_RESOURCES_OLD = 'jobresource_params'
KEY_RESOURCES_NEW = 'resources'
KEY_PARSER_NAME_OLD = 'parser'
KEY_PARSER_NAME_NEW = 'parser_name'
KEY_PROCESS_LABEL_OLD = '_process_label'
KEY_PROCESS_LABEL_NEW = 'process_label'
KEY_ENVIRONMENT_VARIABLES_OLD = 'custom_environment_variables'
KEY_ENVIRONMENT_VARIABLES_NEW = 'environment_variables'
PARSER_NAME = 'aiida.parsers:parser'
PROCESS_LABEL = 'TestLabel'


def test_calc_attributes_keys(perform_migrations: PsqlDosMigrator):
    """Test the migration of the keys of certain attribute for ProcessNodes and CalcJobNodes."""
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@e72ad251bcdb')  # e72ad251bcdb_dbgroup_class_change_type_string_values

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')

    resources = {'number_machines': 1}
    environment_variables: dict = {}

    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(user)
        session.commit()

        resources = {'number_machines': 1}
        environment_variables = {}

        attributes = {
            KEY_RESOURCES_OLD: resources,
            KEY_PARSER_NAME_OLD: PARSER_NAME,
            KEY_PROCESS_LABEL_OLD: PROCESS_LABEL,
            KEY_ENVIRONMENT_VARIABLES_OLD: environment_variables,
        }
        node_work = DbNode(type='node.process.workflow.WorkflowNode.', attributes=attributes, user_id=user.id)
        node_calc = DbNode(type='node.process.calculation.calcjob.CalcJobNode.', attributes=attributes, user_id=user.id)
        # Create a node of a different type to ensure that its attributes are not updated
        node_other = DbNode(type='node.othernode.', attributes=attributes, user_id=user.id)

        session.add(node_work)
        session.add(node_calc)
        session.add(node_other)
        session.commit()

        node_work_id = node_work.id
        node_calc_id = node_calc.id
        node_other_id = node_other.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@7ca08c391c49')  # 7ca08c391c49_calc_job_option_attribute_keys

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')
    not_found = tuple([0])
    with perform_migrations.session() as session:
        node_work = session.query(DbNode).filter(DbNode.id == node_work_id).one()
        assert node_work.attributes.get(KEY_PROCESS_LABEL_NEW) == PROCESS_LABEL
        assert node_work.attributes.get(KEY_PROCESS_LABEL_OLD, not_found) == not_found

        node_calc = session.query(DbNode).filter(DbNode.id == node_calc_id).one()
        assert node_calc.attributes.get(KEY_PROCESS_LABEL_NEW) == PROCESS_LABEL
        assert node_calc.attributes.get(KEY_PARSER_NAME_NEW) == PARSER_NAME
        assert node_calc.attributes.get(KEY_RESOURCES_NEW) == resources
        assert node_calc.attributes.get(KEY_ENVIRONMENT_VARIABLES_NEW) == environment_variables
        assert node_calc.attributes.get(KEY_PROCESS_LABEL_OLD, not_found) == not_found
        assert node_calc.attributes.get(KEY_PARSER_NAME_OLD, not_found) == not_found
        assert node_calc.attributes.get(KEY_RESOURCES_OLD, not_found) == not_found
        assert node_calc.attributes.get(KEY_ENVIRONMENT_VARIABLES_OLD, not_found) == not_found

        # The following node should not be migrated even if its attributes have the matching keys because
        # the node is not a ProcessNode
        node_other = session.query(DbNode).filter(DbNode.id == node_other_id).one()
        assert node_other.attributes.get(KEY_PROCESS_LABEL_OLD) == PROCESS_LABEL
        assert node_other.attributes.get(KEY_PARSER_NAME_OLD) == PARSER_NAME
        assert node_other.attributes.get(KEY_RESOURCES_OLD) == resources
        assert node_other.attributes.get(KEY_ENVIRONMENT_VARIABLES_OLD) == environment_variables
        assert node_other.attributes.get(KEY_PROCESS_LABEL_NEW, not_found) == not_found
        assert node_other.attributes.get(KEY_PARSER_NAME_NEW, not_found) == not_found
        assert node_other.attributes.get(KEY_RESOURCES_NEW, not_found) == not_found
        assert node_other.attributes.get(KEY_ENVIRONMENT_VARIABLES_NEW, not_found) == not_found
