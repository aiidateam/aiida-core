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
from __future__ import print_function
from __future__ import absolute_import

from six.moves import range
from aiida.plugins.entry_point import ENTRYPOINT_MANAGER
from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO

db_test_list = {
    BACKEND_DJANGO: {
        'generic': ['aiida.backends.djsite.db.subtests.test_generic'],
        'nodes': ['aiida.backends.djsite.db.subtests.test_nodes'],
        'migrations': ['aiida.backends.djsite.db.subtests.test_migrations'],
        'query': ['aiida.backends.djsite.db.subtests.test_query'],
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
        'backup_script': ['aiida.backends.tests.test_backup_script'],
        'backup_setup_script': ['aiida.backends.tests.test_backup_setup_script'],
        'base_dataclasses': ['aiida.backends.tests.test_base_dataclasses'],
        'caching_config': ['aiida.backends.tests.test_caching_config'],
        'calculation_node': ['aiida.backends.tests.test_calculation_node'],
        'cmdline.commands.calcjob': ['aiida.backends.tests.cmdline.commands.test_calcjob'],
        'cmdline.commands.code': ['aiida.backends.tests.cmdline.commands.test_code'],
        'cmdline.commands.comment': ['aiida.backends.tests.cmdline.commands.test_comment'],
        'cmdline.commands.computer': ['aiida.backends.tests.cmdline.commands.test_computer'],
        'cmdline.commands.config': ['aiida.backends.tests.cmdline.commands.test_config'],
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
        'cmdline.params.types.calculation': ['aiida.backends.tests.cmdline.params.types.test_calculation'],
        'cmdline.params.types.code': ['aiida.backends.tests.cmdline.params.types.test_code'],
        'cmdline.params.types.computer': ['aiida.backends.tests.cmdline.params.types.test_computer'],
        'cmdline.params.types.data': ['aiida.backends.tests.cmdline.params.types.test_data'],
        'cmdline.params.types.group': ['aiida.backends.tests.cmdline.params.types.test_group'],
        'cmdline.params.types.identifier': ['aiida.backends.tests.cmdline.params.types.test_identifier'],
        'cmdline.params.types.node': ['aiida.backends.tests.cmdline.params.types.test_node'],
        'cmdline.params.types.plugin': ['aiida.backends.tests.cmdline.params.types.test_plugin'],
        'cmdline.utils.common': ['aiida.backends.tests.cmdline.utils.test_common'],
        'common.archive': ['aiida.backends.tests.common.test_archive'],
        'common.extendeddicts': ['aiida.backends.tests.common.test_extendeddicts'],
        'common.folders': ['aiida.backends.tests.common.test_folders'],
        'common.hashing': ['aiida.backends.tests.common.test_hashing'],
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
        'export_and_import': ['aiida.backends.tests.test_export_and_import'],
        'generic': ['aiida.backends.tests.test_generic'],
        'manage.configuration.config.': ['aiida.backends.tests.manage.configuration.test_config'],
        'manage.configuration.migrations.': ['aiida.backends.tests.manage.configuration.migrations.test_migrations'],
        'manage.configuration.options.': ['aiida.backends.tests.manage.configuration.test_options'],
        'manage.configuration.profile.': ['aiida.backends.tests.manage.configuration.test_profile'],
        'manage.external.postgres': ['aiida.backends.tests.manage.external.test_postgres'],
        'nodes': ['aiida.backends.tests.test_nodes'],
        'orm.authinfos': ['aiida.backends.tests.orm.test_authinfos'],
        'orm.comments': ['aiida.backends.tests.orm.test_comments'],
        'orm.computers': ['aiida.backends.tests.orm.test_computers'],
        'orm.data.remote': ['aiida.backends.tests.orm.data.test_remote'],
        'orm.data.singlefile': ['aiida.backends.tests.orm.data.test_singlefile'],
        'orm.data.upf': ['aiida.backends.tests.orm.data.test_upf'],
        'orm.entities': ['aiida.backends.tests.orm.test_entities'],
        'orm.groups': ['aiida.backends.tests.orm.test_groups'],
        'orm.implementation.backend': ['aiida.backends.tests.orm.implementation.test_backend'],
        'orm.implementation.nodes': ['aiida.backends.tests.orm.implementation.test_nodes'],
        'orm.implementation.comments': ['aiida.backends.tests.orm.implementation.test_comments'],
        'orm.logs': ['aiida.backends.tests.orm.test_logs'],
        'orm.mixins': ['aiida.backends.tests.orm.test_mixins'],
        'orm.node': ['aiida.backends.tests.orm.node.test_node'],
        'orm.utils.calcjob': ['aiida.backends.tests.orm.utils.test_calcjob'],
        'orm.utils.node': ['aiida.backends.tests.orm.utils.test_node'],
        'orm.utils.loaders': ['aiida.backends.tests.orm.utils.test_loaders'],
        'orm.utils.repository': ['aiida.backends.tests.orm.utils.test_repository'],
        'parsers': ['aiida.backends.tests.test_parsers'],
        'plugin_loader': ['aiida.backends.tests.test_plugin_loader'],
        'query': ['aiida.backends.tests.test_query'],
        'restapi': ['aiida.backends.tests.test_restapi'],
    }
}


def get_db_test_names():
    retlist = []
    for backend in db_test_list:
        for name in db_test_list[backend]:
            retlist.append(name)

    # This is a temporary solution to be able to run tests in plugins. Once the plugin fixtures
    # have been made working and are released, we can replace this logic with them
    for ep in [ep for ep in ENTRYPOINT_MANAGER.iter_entry_points(group='aiida.tests')]:
        retlist.append(ep.name)

    # Explode the list so that if I have a.b.c,
    # I can run it also just with 'a' or with 'a.b'
    final_list = [_ for _ in retlist]
    for k in retlist:
        if '.' in k:
            parts = k.split('.')
            for last_idx in range(1, len(parts)):
                parentkey = ".".join(parts[:last_idx])
                final_list.append(parentkey)

    # return the list of possible names, without duplicates
    return sorted(set(final_list))


def get_db_test_list():
    """
    This function returns the db_test_list for the current backend,
    merged with the 'common' tests.

    :note: This function should be called only after setting the
      backend, and then it returns only the tests for this backend, and the common ones.
    """
    from aiida.backends import settings
    from aiida.common.exceptions import ConfigurationError
    from collections import defaultdict

    current_backend = settings.BACKEND
    try:
        be_tests = db_test_list[current_backend]
    except KeyError:
        raise ConfigurationError("No backend configured yet")

    # Could be undefined, so put to empty dict by default
    try:
        common_tests = db_test_list["common"]
    except KeyError:
        raise ConfigurationError("A 'common' key must always be defined!")

    retdict = defaultdict(list)
    for k, tests in common_tests.items():
        for t in tests:
            retdict[k].append(t)
    for k, tests in be_tests.items():
        for t in tests:
            retdict[k].append(t)

    # This is a temporary solution to be able to run tests in plugins. Once the plugin fixtures
    # have been made working and are released, we can replace this logic with them
    for ep in [ep for ep in ENTRYPOINT_MANAGER.iter_entry_points(group='aiida.tests')]:
        retdict[ep.name].append(ep.module_name)

    # Explode the dictionary so that if I have a.b.c,
    # I can run it also just with 'a' or with 'a.b'
    final_retdict = defaultdict(list)
    for k, v in retdict.items():
        final_retdict[k] = v
    for k, v in retdict.items():
        if '.' in k:
            parts = k.split('.')
            for last_idx in range(1, len(parts)):
                parentkey = ".".join(parts[:last_idx])
                final_retdict[parentkey].extend(v)

    return dict(final_retdict)
