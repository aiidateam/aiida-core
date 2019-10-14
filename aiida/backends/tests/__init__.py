# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=line-too-long
"""
Module for defining tests that required access to (a temporary) database
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import range
from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO

DB_TEST_LIST = {
    BACKEND_DJANGO: {
        'generic': ['aiida.backends.djsite.db.subtests.test_generic'],
        'migrations': [
            'aiida.backends.djsite.db.subtests.migrations.test_migrations_many',
            'aiida.backends.djsite.db.subtests.migrations.test_migrations_0037_attributes_extras_settings_json',
            'aiida.backends.djsite.db.subtests.migrations.test_migrations_0038_data_migration_legacy_job_calculations',
            'aiida.backends.djsite.db.subtests.migrations.test_migrations_0040_data_migration_legacy_process_attributes',
        ],
    },
    BACKEND_SQLA: {
        'generic': ['aiida.backends.sqlalchemy.tests.test_generic'],
        'nodes': ['aiida.backends.sqlalchemy.tests.test_nodes'],
        'query': ['aiida.backends.sqlalchemy.tests.test_query'],
        'session': ['aiida.backends.sqlalchemy.tests.test_session'],
        'schema': ['aiida.backends.sqlalchemy.tests.test_schema'],
        'migrations': ['aiida.backends.sqlalchemy.tests.test_migrations'],
    },
    # Must be always defined (in the worst case, an empty dict)
    'common': {
        'base_dataclasses': ['aiida.backends.tests.test_base_dataclasses'],
        'calculation_node': ['aiida.backends.tests.test_calculation_node'],
        'cmdline.commands.calcjob': ['aiida.backends.tests.cmdline.commands.test_calcjob'],
        'cmdline.commands.code': ['aiida.backends.tests.cmdline.commands.test_code'],
        'cmdline.commands.comment': ['aiida.backends.tests.cmdline.commands.test_comment'],
        'cmdline.commands.computer': ['aiida.backends.tests.cmdline.commands.test_computer'],
        'cmdline.commands.config': ['aiida.backends.tests.cmdline.commands.test_config'],
        'cmdline.commands.daemon': ['aiida.backends.tests.cmdline.commands.test_daemon'],
        'cmdline.commands.data': ['aiida.backends.tests.cmdline.commands.test_data'],
        'cmdline.commands.database': ['aiida.backends.tests.cmdline.commands.test_database'],
        'cmdline.commands.export': ['aiida.backends.tests.cmdline.commands.test_export'],
        'cmdline.commands.graph': ['aiida.backends.tests.cmdline.commands.test_graph'],
        'cmdline.commands.group': ['aiida.backends.tests.cmdline.commands.test_group'],
        'cmdline.commands.import': ['aiida.backends.tests.cmdline.commands.test_import'],
        'cmdline.commands.node': ['aiida.backends.tests.cmdline.commands.test_node'],
        'cmdline.commands.process': ['aiida.backends.tests.cmdline.commands.test_process'],
        'cmdline.commands.profile': ['aiida.backends.tests.cmdline.commands.test_profile'],
        'cmdline.commands.rehash': ['aiida.backends.tests.cmdline.commands.test_rehash'],
        'cmdline.commands.run': ['aiida.backends.tests.cmdline.commands.test_run'],
        'cmdline.commands.setup': ['aiida.backends.tests.cmdline.commands.test_setup'],
        'cmdline.commands.status': ['aiida.backends.tests.cmdline.commands.test_status'],
        'cmdline.commands.user': ['aiida.backends.tests.cmdline.commands.test_user'],
        'cmdline.commands.verdi': ['aiida.backends.tests.cmdline.commands.test_verdi'],
        'cmdline.commands.restapi': ['aiida.backends.tests.cmdline.commands.test_restapi'],
        'cmdline.params.types.calculation': ['aiida.backends.tests.cmdline.params.types.test_calculation'],
        'cmdline.params.types.code': ['aiida.backends.tests.cmdline.params.types.test_code'],
        'cmdline.params.types.computer': ['aiida.backends.tests.cmdline.params.types.test_computer'],
        'cmdline.params.types.data': ['aiida.backends.tests.cmdline.params.types.test_data'],
        'cmdline.params.types.group': ['aiida.backends.tests.cmdline.params.types.test_group'],
        'cmdline.params.types.identifier': ['aiida.backends.tests.cmdline.params.types.test_identifier'],
        'cmdline.params.types.node': ['aiida.backends.tests.cmdline.params.types.test_node'],
        'cmdline.params.types.path': ['aiida.backends.tests.cmdline.params.types.test_path'],
        'cmdline.params.types.plugin': ['aiida.backends.tests.cmdline.params.types.test_plugin'],
        'cmdline.utils.common': ['aiida.backends.tests.cmdline.utils.test_common'],
        'common.extendeddicts': ['aiida.backends.tests.common.test_extendeddicts'],
        'common.folders': ['aiida.backends.tests.common.test_folders'],
        'common.hashing': ['aiida.backends.tests.common.test_hashing'],
        'common.lang': ['aiida.backends.tests.common.test_lang'],
        'common.links': ['aiida.backends.tests.common.test_links'],
        'common.logging': ['aiida.backends.tests.common.test_logging'],
        'common.serialize': ['aiida.backends.tests.common.test_serialize'],
        'common.timezone': ['aiida.backends.tests.common.test_timezone'],
        'common.utils': ['aiida.backends.tests.common.test_utils'],
        'dataclasses': ['aiida.backends.tests.test_dataclasses'],
        'dbimporters': ['aiida.backends.tests.test_dbimporters'],
        'engine.daemon.client': ['aiida.backends.tests.engine.daemon.test_client'],
        'engine.calc_job': ['aiida.backends.tests.engine.test_calc_job'],
        'engine.calcfunctions': ['aiida.backends.tests.engine.test_calcfunctions'],
        'engine.class_loader': ['aiida.backends.tests.engine.test_class_loader'],
        'engine.daemon': ['aiida.backends.tests.engine.test_daemon'],
        'engine.futures': ['aiida.backends.tests.engine.test_futures'],
        'engine.launch': ['aiida.backends.tests.engine.test_launch'],
        'engine.manager': ['aiida.backends.tests.engine.test_manager'],
        'engine.persistence': ['aiida.backends.tests.engine.test_persistence'],
        'engine.ports': ['aiida.backends.tests.engine.test_ports'],
        'engine.process': ['aiida.backends.tests.engine.test_process'],
        'engine.process_builder': ['aiida.backends.tests.engine.test_process_builder'],
        'engine.process_function': ['aiida.backends.tests.engine.test_process_function'],
        'engine.process_spec': ['aiida.backends.tests.engine.test_process_spec'],
        'engine.rmq': ['aiida.backends.tests.engine.test_rmq'],
        'engine.run': ['aiida.backends.tests.engine.test_run'],
        'engine.runners': ['aiida.backends.tests.engine.test_runners'],
        'engine.transport': ['aiida.backends.tests.engine.test_transport'],
        'engine.utils': ['aiida.backends.tests.engine.test_utils'],
        'engine.work_chain': ['aiida.backends.tests.engine.test_work_chain'],
        'engine.workfunctions': ['aiida.backends.tests.engine.test_workfunctions'],
        'generic': ['aiida.backends.tests.test_generic'],
        'manage.backup.backup_script': ['aiida.backends.tests.manage.backup.test_backup_script'],
        'manage.backup.backup_setup_script': ['aiida.backends.tests.manage.backup.test_backup_setup_script'],
        'manage.caching.': ['aiida.backends.tests.manage.test_caching'],
        'manage.configuration.config.': ['aiida.backends.tests.manage.configuration.test_config'],
        'manage.configuration.migrations.': ['aiida.backends.tests.manage.configuration.migrations.test_migrations'],
        'manage.configuration.options.': ['aiida.backends.tests.manage.configuration.test_options'],
        'manage.configuration.profile.': ['aiida.backends.tests.manage.configuration.test_profile'],
        'manage.external.postgres': ['aiida.backends.tests.manage.external.test_postgres'],
        'nodes': ['aiida.backends.tests.test_nodes'],
        'orm.authinfos': ['aiida.backends.tests.orm.test_authinfos'],
        'orm.comments': ['aiida.backends.tests.orm.test_comments'],
        'orm.computers': ['aiida.backends.tests.orm.test_computers'],
        'orm.data.data': ['aiida.backends.tests.orm.data.test_data'],
        'orm.data.dict': ['aiida.backends.tests.orm.data.test_dict'],
        'orm.data.folder': ['aiida.backends.tests.orm.data.test_folder'],
        'orm.data.kpoints': ['aiida.backends.tests.orm.data.test_kpoints'],
        'orm.data.orbital': ['aiida.backends.tests.orm.data.test_orbital'],
        'orm.data.remote': ['aiida.backends.tests.orm.data.test_remote'],
        'orm.data.singlefile': ['aiida.backends.tests.orm.data.test_singlefile'],
        'orm.data.upf': ['aiida.backends.tests.orm.data.test_upf'],
        'orm.data.to_aiida_type': ['aiida.backends.tests.orm.data.test_to_aiida_type'],
        'orm.entities': ['aiida.backends.tests.orm.test_entities'],
        'orm.groups': ['aiida.backends.tests.orm.test_groups'],
        'orm.implementation.backend': ['aiida.backends.tests.orm.implementation.test_backend'],
        'orm.implementation.comments': ['aiida.backends.tests.orm.implementation.test_comments'],
        'orm.implementation.logs': ['aiida.backends.tests.orm.implementation.test_logs'],
        'orm.implementation.nodes': ['aiida.backends.tests.orm.implementation.test_nodes'],
        'orm.logs': ['aiida.backends.tests.orm.test_logs'],
        'orm.mixins': ['aiida.backends.tests.orm.test_mixins'],
        'orm.node.calcjob': ['aiida.backends.tests.orm.node.test_calcjob'],
        'orm.node.node': ['aiida.backends.tests.orm.node.test_node'],
        'orm.querybuilder': ['aiida.backends.tests.orm.test_querybuilder'],
        'orm.utils.calcjob': ['aiida.backends.tests.orm.utils.test_calcjob'],
        'orm.utils.node': ['aiida.backends.tests.orm.utils.test_node'],
        'orm.utils.loaders': ['aiida.backends.tests.orm.utils.test_loaders'],
        'orm.utils.repository': ['aiida.backends.tests.orm.utils.test_repository'],
        'parsers.parser': ['aiida.backends.tests.parsers.test_parser'],
        'plugin_loader': ['aiida.backends.tests.test_plugin_loader'],
        'plugins.utils': ['aiida.backends.tests.plugins.test_utils'],
        'query': ['aiida.backends.tests.test_query'],
        'restapi': ['aiida.backends.tests.test_restapi'],
        'tools.data.orbital': ['aiida.backends.tests.tools.data.orbital.test_orbitals'],
        'tools.importexport.common.archive': ['aiida.backends.tests.tools.importexport.common.test_archive'],
        'tools.importexport.complex': ['aiida.backends.tests.tools.importexport.test_complex'],
        'tools.importexport.prov_redesign': ['aiida.backends.tests.tools.importexport.test_prov_redesign'],
        'tools.importexport.simple': ['aiida.backends.tests.tools.importexport.test_simple'],
        'tools.importexport.specific_import': ['aiida.backends.tests.tools.importexport.test_specific_import'],
        'tools.importexport.migration.migration': ['aiida.backends.tests.tools.importexport.migration.test_migration'],
        'tools.importexport.migration.v01_to_v02': ['aiida.backends.tests.tools.importexport.migration.test_v01_to_v02'],
        'tools.importexport.migration.v02_to_v03': ['aiida.backends.tests.tools.importexport.migration.test_v02_to_v03'],
        'tools.importexport.migration.v03_to_v04': ['aiida.backends.tests.tools.importexport.migration.test_v03_to_v04'],
        'tools.importexport.migration.v04_to_v05': ['aiida.backends.tests.tools.importexport.migration.test_v04_to_v05'],
        'tools.importexport.migration.v05_to_v06': ['aiida.backends.tests.tools.importexport.migration.test_v05_to_v06'],
        'tools.importexport.migration.v06_to_v07': ['aiida.backends.tests.tools.importexport.migration.test_v06_to_v07'],
        'tools.importexport.orm.attributes': ['aiida.backends.tests.tools.importexport.orm.test_attributes'],
        'tools.importexport.orm.calculations': ['aiida.backends.tests.tools.importexport.orm.test_calculations'],
        'tools.importexport.orm.codes': ['aiida.backends.tests.tools.importexport.orm.test_codes'],
        'tools.importexport.orm.comments': ['aiida.backends.tests.tools.importexport.orm.test_comments'],
        'tools.importexport.orm.computers': ['aiida.backends.tests.tools.importexport.orm.test_computers'],
        'tools.importexport.orm.extras': ['aiida.backends.tests.tools.importexport.orm.test_extras'],
        'tools.importexport.orm.groups': ['aiida.backends.tests.tools.importexport.orm.test_groups'],
        'tools.importexport.orm.links': ['aiida.backends.tests.tools.importexport.orm.test_links'],
        'tools.importexport.orm.logs': ['aiida.backends.tests.tools.importexport.orm.test_logs'],
        'tools.importexport.orm.users': ['aiida.backends.tests.tools.importexport.orm.test_users'],
        'tools.visualization.graph': ['aiida.backends.tests.tools.visualization.test_graph']
    }
}


def get_db_test_names():
    """
    Return a sorted list of test names
    """
    retlist = []
    for backend in DB_TEST_LIST:
        for name in DB_TEST_LIST[backend]:
            retlist.append(name)

    # Explode the list so that if I have a.b.c,
    # I can run it also just with 'a' or with 'a.b'
    final_list = [_ for _ in retlist]
    for k in retlist:
        if '.' in k:
            parts = k.split('.')
            for last_idx in range(1, len(parts)):
                parentkey = '.'.join(parts[:last_idx])
                final_list.append(parentkey)

    # return the list of possible names, without duplicates
    return sorted(set(final_list))


def get_db_test_list():
    """
    This function returns the DB_TEST_LIST for the current backend,
    merged with the 'common' tests.

    :note: This function should be called only after setting the
      backend, and then it returns only the tests for this backend, and the common ones.
    """
    from collections import defaultdict
    from aiida.common.exceptions import ConfigurationError
    from aiida.manage import configuration

    try:
        be_tests = DB_TEST_LIST[configuration.PROFILE.database_backend]
    except KeyError:
        raise ConfigurationError('No backend configured yet')

    # Could be undefined, so put to empty dict by default
    try:
        common_tests = DB_TEST_LIST['common']
    except KeyError:
        raise ConfigurationError("A 'common' key must always be defined!")

    retdict = defaultdict(list)
    for k, tests in common_tests.items():
        for test in tests:
            retdict[k].append(test)
    for k, tests in be_tests.items():
        for test in tests:
            retdict[k].append(test)

    # Explode the dictionary so that if I have a.b.c,
    # I can run it also just with 'a' or with 'a.b'
    final_retdict = defaultdict(list)
    for key, val in retdict.items():
        final_retdict[key] = val
    for key, val in retdict.items():
        if '.' in key:
            parts = key.split('.')
            for last_idx in range(1, len(parts)):
                parentkey = '.'.join(parts[:last_idx])
                final_retdict[parentkey].extend(val)

    return dict(final_retdict)
