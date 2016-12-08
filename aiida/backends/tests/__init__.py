# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO

# GP: In the future, keep only the list of tests that are *specific* to a given
# backend in the backend dictionaries, and put all the rest in the 'common'
# dictionary to be used for both.
# Even better, define only folders in which tests should be put, and each
# file defines a new test
db_test_list = {
    BACKEND_DJANGO: {
        'generic': ['aiida.backends.djsite.db.subtests.generic'],
        'nodes': ['aiida.backends.djsite.db.subtests.nodes'],
        'nwchem': ['aiida.backends.djsite.db.subtests.nwchem'],
        'dataclasses': ['aiida.backends.djsite.db.subtests.dataclasses'],
        'qepw': ['aiida.backends.djsite.db.subtests.quantumespressopw'],
        'codtools': ['aiida.backends.djsite.db.subtests.codtools'],
        'dbimporters': ['aiida.backends.djsite.db.subtests.dbimporters'],
        'export_and_import': ['aiida.backends.djsite.db.subtests.export_and_import'],
        'migrations': ['aiida.backends.djsite.db.subtests.migrations'],
        'parsers': ['aiida.backends.djsite.db.subtests.parsers'],
        'qepwinputparser': ['aiida.backends.djsite.db.subtests.pwinputparser'],
        'qepwimmigrant': ['aiida.backends.djsite.db.subtests.quantumespressopwimmigrant'],
        'tcodexporter': ['aiida.backends.djsite.db.subtests.tcodexporter'],
        'workflows': ['aiida.backends.djsite.db.subtests.workflows'],
        'query': ['aiida.backends.djsite.db.subtests.query'],
        'backup': ['aiida.backends.djsite.db.subtests.backup_script',
                   'aiida.backends.djsite.db.subtests.backup_setup_script'],
        'calculation_node': ['aiida.backends.djsite.db.subtests.calculation_node'],
    },
    BACKEND_SQLA: {
        'generic': ['aiida.backends.sqlalchemy.tests.generic'],
        'nodes': ['aiida.backends.sqlalchemy.tests.nodes'],
        'nwchem': ['aiida.backends.sqlalchemy.tests.nwchem'],
        'dataclasses': ['aiida.backends.sqlalchemy.tests.dataclasses'],
        'qepw': ['aiida.backends.sqlalchemy.tests.quantumespressopw'],
        'codtools': ['aiida.backends.sqlalchemy.tests.codtools'],
        'dbimporters': ['aiida.backends.sqlalchemy.tests.dbimporters'],
        'export_and_import': ['aiida.backends.sqlalchemy.tests.export_and_import'],
        'migrations': ['aiida.backends.sqlalchemy.tests.migrations'],
        'parsers': ['aiida.backends.sqlalchemy.tests.parsers'],
        'qepwinputparser': ['aiida.backends.sqlalchemy.tests.pwinputparser'],
        'qepwimmigrant': ['aiida.backends.sqlalchemy.tests.quantumespressopwimmigrant'],
        'tcodexporter': ['aiida.backends.sqlalchemy.tests.tcodexporter'],
        'workflows': ['aiida.backends.sqlalchemy.tests.workflows'],
        'query': ['aiida.backends.sqlalchemy.tests.query'],
        'backup': ['aiida.backends.sqlalchemy.tests.backup_script',
                   'aiida.backends.sqlalchemy.tests.backup_setup_script'],
        'calculation_node': ['aiida.backends.sqlalchemy.tests.calculation_node'],
    },
    # Must be always defined (in the worst case, an empty dict)
    'common': {
        'nodes': ['aiida.backends.tests.nodes'],
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


