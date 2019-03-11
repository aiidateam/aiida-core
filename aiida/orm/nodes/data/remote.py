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
import os

from .data import Data
from aiida.orm import AuthInfo

__all__ = ('RemoteData',)


class RemoteData(Data):
    """
    Store a link to a file or folder on a remote machine.

    Remember to pass a computer!
    """

    def __init__(self, remote_path=None, **kwargs):
        super(RemoteData, self).__init__(**kwargs)
        if remote_path is not None:
            self.set_remote_path(remote_path)

    def get_computer_name(self):
        return self.computer.name

    def get_remote_path(self):
        return self.get_attribute('remote_path')

    def set_remote_path(self, val):
        self.set_attribute('remote_path', val)

    @property
    def is_empty(self):
        """
        Check if remote folder is empty
        """
        authinfo = self.get_authinfo()
        transport = authinfo.get_transport()

        with transport:
            try:
                transport.chdir(self.get_remote_path())
            except IOError:
                # If the transport IOError the directory no longer exists and was deleted
                return True

            return not transport.listdir()

    def getfile(self, relpath, destpath):
        """
        Connects to the remote folder and gets a string with the (full) content of the file.

        :param relpath: The relative path of the file to show.
        :param destpath: A path on the local computer to get the file
        :return: a string with the file content
        """
        authinfo = self.get_authinfo()
        t = authinfo.get_transport()

        with t:
            try:
                full_path = os.path.join(self.get_remote_path(), relpath)
                t.getfile(full_path, destpath)
            except IOError as e:
                if e.errno == 2:  # file not existing
                    raise IOError("The required remote file {} on {} does not exist or has been deleted.".format(
                        full_path, self.computer.name
                    ))
                else:
                    raise

            return t.listdir()

    def listdir(self, relpath="."):
        """
        Connects to the remote folder and lists the directory content.

        :param relpath: If 'relpath' is specified, lists the content of the given subfolder.
        :return: a flat list of file/directory names (as strings).
        """
        authinfo = self.get_authinfo()
        t = authinfo.get_transport()

        with t:
            try:
                full_path = os.path.join(self.get_remote_path(), relpath)
                t.chdir(full_path)
            except IOError as e:
                if e.errno == 2 or e.errno == 20:  # directory not existing or not a directory
                    exc = IOError(
                        "The required remote folder {} on {} does not exist, is not a directory or has been deleted.".format(
                            full_path, self.computer.name
                        ))
                    exc.errno = e.errno
                    raise exc
                else:
                    raise

            try:
                return t.listdir()
            except IOError as e:
                if e.errno == 2 or e.errno == 20:  # directory not existing or not a directory
                    exc = IOError(
                        "The required remote folder {} on {} does not exist, is not a directory or has been deleted.".format(
                            full_path, self.computer.name
                        ))
                    exc.errno = e.errno
                    raise exc
                else:
                    raise

    def listdir_withattributes(self, path="."):
        """
        Connects to the remote folder and lists the directory content.

        :param relpath: If 'relpath' is specified, lists the content of the given subfolder.
        :return: a list of dictionaries, where the documentation is in :py:class:Transport.listdir_withattributes.
        """
        authinfo = self.get_authinfo()
        t = authinfo.get_transport()

        with t:
            try:
                full_path = os.path.join(self.get_remote_path(), path)
                t.chdir(full_path)
            except IOError as e:
                if e.errno == 2 or e.errno == 20:  # directory not existing or not a directory
                    exc = IOError(
                        "The required remote folder {} on {} does not exist, is not a directory or has been deleted.".format(
                            full_path, self.computer.name
                        ))
                    exc.errno = e.errno
                    raise exc
                else:
                    raise

            try:
                return t.listdir_withattributes()
            except IOError as e:
                if e.errno == 2 or e.errno == 20:  # directory not existing or not a directory
                    exc = IOError(
                        "The required remote folder {} on {} does not exist, is not a directory or has been deleted.".format(
                            full_path, self.computer.name
                        ))
                    exc.errno = e.errno
                    raise exc
                else:
                    raise

    def _clean(self):
        """
        Remove all content of the remote folder on the remote computer
        """
        from aiida.orm.utils.remote import clean_remote

        authinfo = self.get_authinfo()
        transport = authinfo.get_transport()
        remote_dir = self.get_remote_path()

        with transport:
            clean_remote(transport, remote_dir)

    def _validate(self):
        from aiida.common.exceptions import ValidationError

        super(RemoteData, self)._validate()

        try:
            self.get_remote_path()
        except AttributeError:
            raise ValidationError("attribute 'remote_path' not set.")

        computer = self.computer
        if computer is None:
            raise ValidationError("Remote computer not set.")

    def get_authinfo(self):
        return AuthInfo.objects.get(dbcomputer=self.computer, aiidauser=self.user)
