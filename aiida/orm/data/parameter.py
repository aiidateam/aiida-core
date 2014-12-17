# -*- coding: utf-8 -*-
from aiida.orm import Data

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

class ParameterData(Data):
    """
    Pass as input in the init a dictionary, and it will get stored as internal
    attributes.

    Usual rules for attribute names apply (in particular, keys cannot start with
    an underscore). If this is the case, a ValueError will be raised.
    
    You can then change/delete/add more attributes before storing with the
    usual methods of aiida.orm.Node
    """
    def set_dict(self, dict):
        # I set the keys
        for k, v in dict.iteritems():
            self._set_attr(k, v)

    def get_dict(self):
        """
        Return a dict with the parameters
        """
        return dict(self.iterattrs())
    
    def keys(self):
        """
        Iterator of valid keys stored in the ParameterData object
        """
        for k in self.attrs():
            yield k

    def add_path(self, *args, **kwargs):
        from aiida.common.exceptions import ModificationNotAllowed
        raise ModificationNotAllowed("Cannot add files or directories to a ParameterData object")

    #    def validate(self):
    #        # There should be nothing specific to check
    #        super(ParameterData,self).validate()
