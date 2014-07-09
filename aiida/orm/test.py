# -*- coding: utf-8 -*-
"""
Classes needed for tests.
Must be here because subclasses of 'Node' must be within aiida.orm
"""
from aiida.orm import Node

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class myNodeWithFields(Node):
    # State can be updated even after storing
    _updatable_attributes = ('state',) 
