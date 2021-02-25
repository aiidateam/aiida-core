# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name,unused-argument
"""
Collection of pytest fixtures using the TestManager for easy testing of AiiDA plugins.

 * aiida_profile
 * clear_database
 * aiida_localhost
 * aiida_local_code_factory

"""
import asyncio
import shutil
import tempfile
import pytest

from aiida.common.log import AIIDA_LOGGER
from aiida.manage.tests import test_manager, get_test_backend_name, get_test_profile_name


@pytest.fixture(scope='function')
def aiida_caplog(caplog):
    """A copy of pytest's caplog fixture, which allows ``AIIDA_LOGGER`` to propagate."""
    propogate = AIIDA_LOGGER.propagate
    AIIDA_LOGGER.propagate = True
    yield caplog
    AIIDA_LOGGER.propagate = propogate


@pytest.fixture(scope='session', autouse=True)
def aiida_profile():
    """Set up AiiDA test profile for the duration of the tests.

    Note: scope='session' limits this fixture to run once per session. Thanks to ``autouse=True``, you don't actually
     need to depend on it explicitly - it will activate as soon as you import it in your ``conftest.py``.
    """
    with test_manager(backend=get_test_backend_name(), profile_name=get_test_profile_name()) as manager:
        yield manager
    # Leaving the context manager will automatically cause the `TestManager` instance to be destroyed


@pytest.fixture(scope='function')
def clear_database(clear_database_after_test):
    """Alias for 'clear_database_after_test'.

    Clears the database after each test. Use of the explicit
    'clear_database_after_test' is preferred.
    """


@pytest.fixture(scope='function')
def clear_database_after_test(aiida_profile):
    """Clear the database after the test."""
    yield
    aiida_profile.reset_db()


@pytest.fixture(scope='function')
def clear_database_before_test(aiida_profile):
    """Clear the database before the test."""
    aiida_profile.reset_db()
    yield


@pytest.fixture(scope='class')
def clear_database_before_test_class(aiida_profile):
    """Clear the database before a test class."""
    aiida_profile.reset_db()
    yield


@pytest.fixture(scope='function')
def temporary_event_loop():
    """Create a temporary loop for independent test case"""
    current = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield
    finally:
        loop.close()
        asyncio.set_event_loop(current)


@pytest.fixture(scope='function')
def temp_dir():
    """Get a temporary directory.

    E.g. to use as the working directory of an AiiDA computer.

    :return: The path to the directory
    :rtype: str

    """
    try:
        dirpath = tempfile.mkdtemp()
        yield dirpath
    finally:
        # after the test function has completed, remove the directory again
        shutil.rmtree(dirpath)


@pytest.fixture(scope='function')
def aiida_localhost(temp_dir):
    """Get an AiiDA computer for localhost.

    Usage::

      def test_1(aiida_localhost):
          label = aiida_localhost.get_label()
          # proceed to set up code or use 'aiida_local_code_factory' instead


    :return: The computer node
    :rtype: :py:class:`aiida.orm.Computer`
    """
    from aiida.orm import Computer
    from aiida.common.exceptions import NotExistent

    label = 'localhost-test'

    try:
        computer = Computer.objects.get(label=label)
    except NotExistent:
        computer = Computer(
            label=label,
            description='localhost computer set up by test manager',
            hostname=label,
            workdir=temp_dir,
            transport_type='local',
            scheduler_type='direct'
        )
        computer.store()
        computer.set_minimum_job_poll_interval(0.)
        computer.configure()

    return computer


@pytest.fixture(scope='function')
def aiida_local_code_factory(aiida_localhost):
    """Get an AiiDA code on localhost.

    Searches in the PATH for a given executable and creates an AiiDA code with provided entry point.

    Usage::

      def test_1(aiida_local_code_factory):
          code = aiida_local_code_factory('quantumespresso.pw', '/usr/bin/pw.x')
          # use code for testing ...

    :return: A function get_code(entry_point, executable) that returns the `Code` node.
    :rtype: object
    """

    def get_code(entry_point, executable, computer=aiida_localhost, label=None, prepend_text=None, append_text=None):
        """Get local code.

        Sets up code for given entry point on given computer.

        :param entry_point: Entry point of calculation plugin
        :param executable: name of executable; will be searched for in local system PATH.
        :param computer: (local) AiiDA computer
        :param prepend_text: a string of code that will be put in the scheduler script before the execution of the code.
        :param append_text: a string of code that will be put in the scheduler script after the execution of the code.
        :return: the `Code` either retrieved from the database or created if it did not yet exist.
        :rtype: :py:class:`aiida.orm.Code`
        """
        from aiida.common import exceptions
        from aiida.orm import Code, Computer, QueryBuilder

        if label is None:
            label = executable

        builder = QueryBuilder().append(Computer, filters={'uuid': computer.uuid}, tag='computer')
        builder.append(Code, filters={'label': label, 'attributes.input_plugin': entry_point}, with_computer='computer')

        try:
            code = builder.one()[0]
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            code = None
        else:
            return code

        executable_path = shutil.which(executable)
        if not executable_path:
            raise ValueError(f'The executable "{executable}" was not found in the $PATH.')

        code = Code(input_plugin_name=entry_point, remote_computer_exec=[computer, executable_path])
        code.label = label
        code.description = label

        if prepend_text is not None:
            code.set_prepend_text(prepend_text)

        if append_text is not None:
            code.set_append_text(append_text)

        return code.store()

    return get_code
