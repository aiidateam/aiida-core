import sys
import json
import shutil
import tempfile
import operator
import subprocess
from os.path import join

import pytest


@pytest.fixture
def build_dir():
    # Python 2 doesn't have tempfile.TemporaryDirectory
    dirname = tempfile.mkdtemp()
    try:
        yield dirname
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(dirname)


@pytest.fixture
def build_sphinx(build_dir):
    def inner(source_dir, builder='xml'):
        doctree_dir = join(build_dir, 'doctrees')
        out_dir = join(build_dir, builder)

        subprocess.check_call([
            sys.executable, '-m', 'sphinx', '-b', builder, '-d', doctree_dir,
            source_dir, out_dir
        ])

        return out_dir

    return inner


@pytest.fixture
def test_name(request):
    """Returns module_name.function_name for a given test"""
    return request.module.__name__ + '/' + request._parent_request._pyfuncitem.name


@pytest.fixture
def compare_data(request, test_name, scope="session"):
    """Returns a function which either saves some data to a file or (if that file exists already) compares it to pre-existing data using a given comparison function."""

    def inner(compare_fct, data, tag=None):
        full_name = test_name + (tag or '')
        val = request.config.cache.get(full_name, None)
        if val is None:
            request.config.cache.set(full_name, json.loads(json.dumps(data)))
            raise ValueError('Reference data does not exist.')
        else:
            assert compare_fct(val, json.loads(json.dumps(data))
                               )  # get rid of json-specific quirks

    return inner


@pytest.fixture
def compare_equal(compare_data):
    return lambda data, tag=None: compare_data(operator.eq, data, tag)
