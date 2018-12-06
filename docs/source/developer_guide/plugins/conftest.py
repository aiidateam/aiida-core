"""
For pytest
initialise a text database and profile
This file should be put into the root directory of the package to make
the fixtures available to all tests
"""
from __future__ import absolute_import
import tempfile
import shutil
import pytest
import os

from aiida.utils.fixtures import fixture_manager


def get_backend_str():
    """ Return database backend string.

    Reads from 'TEST_AIIDA_BACKEND' environment variable.
    Defaults to django backend.
    """
    from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
    backend_env = os.environ.get('TEST_AIIDA_BACKEND')
    if not backend_env:
        return BACKEND_DJANGO
    elif  backend_env in (BACKEND_DJANGO, BACKEND_SQLA):
        return backend_env

    raise ValueError("Unknown backend '{}' read from TEST_AIIDA_BACKEND environment variable".format(backend_env))


@pytest.fixture(scope='session')
def aiida_profile():
    """setup a test profile for the duration of the tests"""
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope='function')
def new_database(aiida_profile):
    """Get a the database for the test and clean it up after it finishes"""
    aiida_profile.reset_db()
    return


@pytest.fixture(scope='function')
def new_workdir():
    """get a new temporary folder to use as the computer's wrkdir"""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)
