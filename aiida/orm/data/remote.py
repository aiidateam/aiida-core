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

from aiida.orm import Data
from aiida.orm import AuthInfo


class RemoteData(Data):
    """
    Store a link to a file or folder on a remote machine.

    Remember to pass a computer!
    """

    def get_dbcomputer(self):
        return self.dbnode.dbcomputer

    def get_computer_name(self):
        return self.get_computer().name

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
        authinfo = self._get_authinfo()
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
        authinfo = self._get_authinfo()
        t = authinfo.get_transport()

        with t:
            try:
                full_path = os.path.join(self.get_remote_path(), relpath)
                t.getfile(full_path, destpath)
            except IOError as e:
                if e.errno == 2:  # file not existing
                    raise IOError("The required remote file {} on {} does not exist or has been deleted.".format(
                        full_path, self.get_computer().name
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
        authinfo = self._get_authinfo()
        t = authinfo.get_transport()

        with t:
            try:
                full_path = os.path.join(self.get_remote_path(), relpath)
                t.chdir(full_path)
            except IOError as e:
                if e.errno == 2 or e.errno == 20:  # directory not existing or not a directory
                    exc = IOError(
                        "The required remote folder {} on {} does not exist, is not a directory or has been deleted.".format(
                            full_path, self.get_computer().name
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
                            full_path, self.get_computer().name
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
        authinfo = self._get_authinfo()
        t = authinfo.get_transport()

        with t:
            try:
                full_path = os.path.join(self.get_remote_path(), path)
                t.chdir(full_path)
            except IOError as e:
                if e.errno == 2 or e.errno == 20:  # directory not existing or not a directory
                    exc = IOError(
                        "The required remote folder {} on {} does not exist, is not a directory or has been deleted.".format(
                            full_path, self.get_computer().name
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
                            full_path, self.get_computer().name
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

        authinfo = self._get_authinfo()
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

        computer = self.get_computer()
        if computer is None:
            raise ValidationError("Remote computer not set.")

    def _get_authinfo(self):
        return AuthInfo.objects(backend=self._backend).find(self.get_computer(), self.get_user())[0]
