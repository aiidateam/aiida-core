# -*- coding: utf-8 -*-
from aiida.orm import Data


__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class RemoteData(Data):
    """
    Store a link to a file or folder on a remote machine.
    
    Remember to pass a computer!
    """
    def get_dbcomputer(self):
        return self.dbnode.dbcomputer

    def get_remote_path(self):
        return self.get_attr('remote_path')

    def set_remote_path(self,val):
        self._set_attr('remote_path', val)

    def add_path(self,src_abs,dst_filename=None):
        """
        Disable adding files or directories to a RemoteData
        """
        from aiida.common.exceptions import ModificationNotAllowed
        raise ModificationNotAllowed("Cannot add files or directories to a RemoteData object")

    def _validate(self):
        from aiida.common.exceptions import ValidationError

        super(RemoteData,self)._validate()
        
        try:
            self.get_remote_path()
        except AttributeError:
            raise ValidationError("attribute 'remote_path' not set.")

        computer = self.get_computer()
        if computer is None:
            raise ValidationError("Remote computer not set.")
    
