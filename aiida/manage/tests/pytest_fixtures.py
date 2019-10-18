# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Collection of pytest fixtures using the TestManager for easy testing of AiiDA plugins.

 * aiida_profile
 * clear_database
 * aiida_localhost
 * aiida_local_code_factory

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import tempfile
import shutil
import pytest
from aiida.manage.tests import test_manager, get_test_backend


@pytest.fixture(scope='session', autouse=True)
def aiida_profile():
    """Set up AiiDA test profile for the duration of the tests.

    Note: scope='session' limits this fixture to run once per session. Thanks to ``autouse=True``, you don't actually
     need to depend on it explicitly - it will activate as soon as you import it in your ``conftest.py``.
    """
    # create new TestManager instance
    with test_manager(backend=get_test_backend()) as test_mgr:
        yield test_mgr
    # here, the TestManager instance has already been destroyed


@pytest.fixture(scope='function', autouse=True)
def clear_database(aiida_profile):  # pylint: disable=redefined-outer-name
    """Clear the database after each test.

    Note: Thanks to ``autouse=True``, this happens as soon as you import this fixure in your ``conftest.py``.
    """
    yield
    # after the test function has completed, reset the database
    aiida_profile.reset_db()


@pytest.fixture(scope='function')
def tempdir():
    """Get a temporary directory.

    E.g. to use as the working directory of an AiiDA computer.

    :return: The path to the directory
    :rtype: str

    """
    dirpath = tempfile.mkdtemp()
    yield dirpath
    # after the test function has completed, remove the directory again
    shutil.rmtree(dirpath)


@pytest.fixture(scope='function')
def aiida_localhost(tempdir):  # pylint: disable=redefined-outer-name
    """Get an AiiDA computer for localhost.

    Usage::

      def test_1(aiida_localhost):
          name = aiida_localhost.get_name()
          # proceed to set up code or use 'aiida_local_code_factory' instead


    :return: The computer node
    :rtype: :py:class:`aiida.orm.Computer`
    """
    from aiida.orm import Computer
    from aiida.common.exceptions import NotExistent

    name = 'localhost'

    try:
        computer = Computer.objects.get(name=name)
    except NotExistent:
        computer = Computer(
            name=name,
            description='localhost computer set up by test manager',
            hostname=name,
            workdir=tempdir,
            transport_type='local',
            scheduler_type='direct'
        )
        computer.store()
        computer.configure()

    return computer


@pytest.fixture(scope='function')
def aiida_local_code_factory(aiida_localhost):  # pylint: disable=redefined-outer-name
    """Get an AiiDA code on localhost.

    Searches in the PATH for a given executable and creates an AiiDA code with provided entry point.

    Usage::

      def test_1(aiida_local_code_factory):
          code = aiida_local_code_factory('pw.x', 'quantumespresso.pw')
          # use code for testing ...

    :return: A function get_code(executable, entry_point) that returns the Code node.
    :rtype: object
    """

    def get_code(executable, entry_point, computer=aiida_localhost):
        """Get local code.
        Sets up code for given entry point on given computer.

        :param entry_point: Entry point of calculation plugin
        :param computer: (local) AiiDA computer
        :return: The code node
        :rtype: :py:class:`aiida.orm.Code`
        """
        from aiida.orm import Code
        from aiida.common.files import which
        from aiida.common.exceptions import NotExistent

        try:
            codes = Code.objects.find(filters={'label': executable})  # pylint: disable=no-member
            code = codes[0]
        except NotExistent:
            executable_path = which(executable)
            code = Code(
                input_plugin_name=entry_point,
                remote_computer_exec=[computer, executable_path],
            )
            code.label = executable
            code.store()

        return code

    return get_code
