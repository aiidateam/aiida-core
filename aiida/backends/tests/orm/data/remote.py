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
import errno
import os
import shutil
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.backends import construct_backend
from aiida.orm.data.remote import RemoteData

from aiida.orm import User


class TestRemoteData(AiidaTestCase):
    """Test for the RemoteData class."""

    @classmethod
    def setUpClass(cls):
        super(TestRemoteData, cls).setUpClass()
        backend = construct_backend()
        user = User.objects.get_default()
        authinfo = backend.authinfos.create(cls.computer, user)
        authinfo.store()

    def setUp(self):
        """Create a dummy RemoteData on the default computer."""
        self.tmp_path = tempfile.mkdtemp()
        self.remote = RemoteData(computer=self.computer)
        self.remote.set_remote_path(self.tmp_path)

        with open(os.path.join(self.tmp_path, 'file.txt'), 'w') as handle:
            handle.write('test string')

        self.remote.set_computer(self.computer)
        self.remote.store()

    def tearDown(self):
        """Delete the temporary path for the dummy RemoteData node."""
        try:
            shutil.rmtree(self.tmp_path)
        except OSError as exception:
            if exception.errno == errno.ENOENT:
                pass
            elif exception.errno == errno.ENOTDIR:
                os.remove(self.tmp_path)
            else:
                raise IOError(exception)

    def test_clean(self):
        """Try cleaning a RemoteData node."""
        self.assertFalse(self.remote.is_empty())
        self.remote._clean()
        self.assertTrue(self.remote.is_empty())
