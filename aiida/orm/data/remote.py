# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm import Data




class RemoteData(Data):
    """
    Store a link to a file or folder on a remote machine.
    
    Remember to pass a computer!
    """

    def get_dbcomputer(self):
        return self.dbnode.dbcomputer

    def get_remote_path(self):
        return self.get_attr('remote_path')

    def set_remote_path(self, val):
        self._set_attr('remote_path', val)

    def add_path(self, src_abs, dst_filename=None):
        """
        Disable adding files or directories to a RemoteData
        """
        from aiida.common.exceptions import ModificationNotAllowed

        raise ModificationNotAllowed("Cannot add files or directories to a RemoteData object")

    def is_empty(self):
        """
        Check if remote folder is empty
        """
        from aiida.backends.utils import get_authinfo

        authinfo = get_authinfo(computer=self.get_computer(),
                                aiidauser=self.get_user())
        t = authinfo.get_transport()

        with t:
            try:
                t.chdir(self.get_remote_path())
            except IOError as e:
                if e.errno == 2:  # directory not existing
                    return True  # is indeed empty, i.e. unusable
            return not t.listdir()

    def _clean(self):
        """
        Remove all content of the remote folder on the remote computer
        """
        from aiida.backends.utils import get_authinfo
        import os

        authinfo = get_authinfo(computer=self.get_computer(),
                                aiidauser=self.get_user())
        t = authinfo.get_transport()

        remote_dir = self.get_remote_path()
        pre, post = os.path.split(remote_dir)

        with t:
            try:
                t.chdir(pre)
                t.rmtree(post)
            except IOError as e:
                if e.errno == 2:  # directory not existing
                    pass

    def _validate(self):
        from aiida.common.exceptions import ValidationError

        super(RemoteData, self)._validate()

        try:
            self.get_remote_path()
        except AttributeError:
            raise ValidationError("attribute 'remote_path' not set.")

        computer = self.get_computer()
        if computer is None:
            raise ValidationError("Remote computer not set.")
    
