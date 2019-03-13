# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic tests that need the use of the DB."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida import orm


class TestCode(AiidaTestCase):
    """
    Test the Code class.
    """

    def test_code_local(self):
        import tempfile

        from aiida.orm import Code
        from aiida.common.exceptions import ValidationError

        code = Code(local_executable='test.sh')
        with self.assertRaises(ValidationError):
            # No file with name test.sh
            code.store()

        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write("#/bin/bash\n\necho test run\n")
            fhandle.flush()
            code.put_object_from_filelike(fhandle, 'test.sh')

        code.store()
        self.assertTrue(code.can_run_on(self.computer))
        self.assertTrue(code.get_local_executable(), 'test.sh')
        self.assertTrue(code.get_execname(), 'stest.sh')

    def test_remote(self):
        import tempfile

        from aiida.orm import Code
        from aiida.common.exceptions import ValidationError

        with self.assertRaises(ValueError):
            # remote_computer_exec has length 2 but is not a list or tuple
            Code(remote_computer_exec='ab')

        # invalid code path
        with self.assertRaises(ValueError):
            Code(remote_computer_exec=(self.computer, ''))

        # Relative path is invalid for remote code
        with self.assertRaises(ValueError):
            Code(remote_computer_exec=(self.computer, 'subdir/run.exe'))

        # first argument should be a computer, not a string
        with self.assertRaises(TypeError):
            Code(remote_computer_exec=('localhost', '/bin/ls'))

        code = Code(remote_computer_exec=(self.computer, '/bin/ls'))
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write("#/bin/bash\n\necho test run\n")
            fhandle.flush()
            code.put_object_from_filelike(fhandle, 'test.sh')

        with self.assertRaises(ValidationError):
            # There are files inside
            code.store()

        # If there are no files, I can store
        code.delete_object('test.sh')
        code.store()

        self.assertEquals(code.get_remote_computer().pk, self.computer.pk)
        self.assertEquals(code.get_remote_exec_path(), '/bin/ls')
        self.assertEquals(code.get_execname(), '/bin/ls')

        self.assertTrue(code.can_run_on(self.computer))
        othercomputer = orm.Computer(
            name='another_localhost',
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro',
            workdir='/tmp/aiida').store()
        self.assertFalse(code.can_run_on(othercomputer))


class TestBool(AiidaTestCase):

    def test_bool_conversion(self):
        for val in [True, False]:
            self.assertEqual(val, bool(orm.Bool(val)))

    def test_int_conversion(self):
        for val in [True, False]:
            self.assertEqual(int(val), int(orm.Bool(val)))
