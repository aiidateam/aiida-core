# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO

# TODO: define only folders in which tests should be put, and each
#       file defines a new test
db_test_list = {
    BACKEND_DJANGO: {
        'generic': ['aiida.backends.djsite.db.subtests.generic'],
        'nodes': ['aiida.backends.djsite.db.subtests.nodes'],
        'djangomigrations': ['aiida.backends.djsite.db.subtests.djangomigrations'],
        'query': ['aiida.backends.djsite.db.subtests.query'],
    },
    BACKEND_SQLA: {
        'generic': ['aiida.backends.sqlalchemy.tests.generic'],
        'nodes': ['aiida.backends.sqlalchemy.tests.nodes'],
        'query': ['aiida.backends.sqlalchemy.tests.query'],
        'session': ['aiida.backends.sqlalchemy.tests.session'],
        'schema': ['aiida.backends.sqlalchemy.tests.schema'],
    },
    # Must be always defined (in the worst case, an empty dict)
    'common': {
        'generic': ['aiida.backends.tests.generic'],
        'nodes': ['aiida.backends.tests.nodes'],
        'nwchem': ['aiida.backends.tests.nwchem'],
        'base_dataclasses': ['aiida.backends.tests.base_dataclasses'],
        'dataclasses': ['aiida.backends.tests.dataclasses'],
        'quantumespressopw': ['aiida.backends.tests.quantumespressopw'],
        'dbimporters': ['aiida.backends.tests.dbimporters'],
        'codtools': ['aiida.backends.tests.codtools'],
        'export_and_import': ['aiida.backends.tests.export_and_import'],
        'parsers': ['aiida.backends.tests.parsers'],
        'pwinputparser': ['aiida.backends.tests.pwinputparser'],
        'quantumespressopwimmigrant': ['aiida.backends.tests.quantumespressopwimmigrant'],
        'tcodexporter': ['aiida.backends.tests.tcodexporter'],
        'query': ['aiida.backends.tests.query'],
        'workflows': ['aiida.backends.tests.workflows'],
        'calculation_node': ['aiida.backends.tests.calculation_node'],
        'backup_script': ['aiida.backends.tests.backup_script'],
        'backup_setup_script': ['aiida.backends.tests.backup_setup_script'],
        'restapi': ['aiida.backends.tests.restapi'],
        'computer': ['aiida.backends.tests.computer'],
        'examplehelpers': ['aiida.backends.tests.example_helpers'],
        'orm.data.frozendict': ['aiida.backends.tests.orm.data.frozendict'],
        'orm.log': ['aiida.backends.tests.orm.log'],
        'work.class_loader': ['aiida.backends.tests.work.class_loader'],
        'work.daemon': ['aiida.backends.tests.work.daemon'],
        'work.persistence': ['aiida.backends.tests.work.persistence'],
        'work.process': ['aiida.backends.tests.work.process'],
        'work.processSpec': ['aiida.backends.tests.work.processSpec'],
        'work.process_registry': ['aiida.backends.tests.work.process_registry'],
        'work.run': ['aiida.backends.tests.work.run'],
        'work.tickingEngine': ['aiida.backends.tests.work.tickingEngine'],
        'work.util': ['aiida.backends.tests.work.util'],
        'work.workChain': ['aiida.backends.tests.work.workChain'],
        'work.workfunction': ['aiida.backends.tests.work.workfunction'],
        'work.legacy.job_process': ['aiida.backends.tests.work.legacy.job_process'],
        'pluginloader': ['aiida.backends.tests.test_plugin_loader'],
        'daemon': ['aiida.backends.tests.daemon'],
        'verdi_commands': ['aiida.backends.tests.verdi_commands'],
    }
}

def get_db_test_names():
    retlist = []
    for backend in db_test_list:
        for name in db_test_list[backend]:
            retlist.append(name)


    # Explode the list so that if I have a.b.c,
    # I can run it also just with 'a' or with 'a.b'
    final_list = [_ for _ in retlist]
    for k in retlist:
        if '.' in k:
            parts = k.split('.')
            for last_idx in range(1,len(parts)):
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
    for k, tests in common_tests.iteritems():
        for t in tests:
            retdict[k].append(t)
    for k, tests in be_tests.iteritems():
        for t in tests:
            retdict[k].append(t)

    # Explode the dictionary so that if I have a.b.c,
    # I can run it also just with 'a' or with 'a.b'
    final_retdict = defaultdict(list)
    for k, v in retdict.iteritems():
        final_retdict[k] = v
    for k, v in retdict.iteritems():
        if '.' in k:
            parts = k.split('.')
            for last_idx in range(1,len(parts)):
                parentkey = ".".join(parts[:last_idx])
                final_retdict[parentkey].extend(v)

    return dict(final_retdict)
