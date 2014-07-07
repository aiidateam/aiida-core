# -*- coding: utf-8 -*-
from aiida.orm import Node

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

'''
Specifications of the Data class:
AiiDA Data objects are subclasses of Node and should have 

Multiple inheritance must be suppoted, i.e. Data should have methods for querying and
be able to inherit other library objects such as ASE for structures.

Architecture note:
The code plugin is responsible for converting a raw data object produced by code
to AiiDA standard object format. The data object then validates itself according to its
method. This is done independently in order to allow cross-validation of plugins.

'''

class Data(Node):
    _updatable_attributes = tuple() 
               
    def _add_link_from(self,src,label=None):
        from aiida.orm.calculation import Calculation

        if len(self.get_inputs()) > 0:
            raise ValueError("At most one node can enter a data node")
        
        if not isinstance(src, Calculation):
            raise ValueError("Links entering a data object can only be of type calculation")
        
        return super(Data,self)._add_link_from(src,label)
    
    def can_link_as_output(self,dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        
        An output of a data can only be a calculation
        """
        from aiida.orm import Calculation
        
        if not isinstance(dest, Calculation):
            raise ValueError("The output of a data node can only be a calculation")

        return super(Data, self).can_link_as_output(dest)
    
    
