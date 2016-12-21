# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

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
        'restapi': ['aiida.backends.tests.restapi']
    }
}

def get_db_test_names():
    retlist = []
    for backend in db_test_list:
        for name in db_test_list[backend]:
            retlist.append(name)

    # return the list of possible names, without duplicates
    return sorted(set(retlist))


def get_db_test_list():
    """
    This function returns the db_test_list for the current backend, 
    merged with the 'common' tests.

    :note: This function should be called only after setting the
    backend, and then it returns only the tests for this backend, and the common ones.
    """
    from aiida.backends import settings
    from aiida.common.exceptions import ConfigurationError, InternalError
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

    return dict(retdict)


