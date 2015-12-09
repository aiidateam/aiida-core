# -*- coding: utf-8 -*-
"""
Classes needed for tests.
Must be here because subclasses of 'Node' must be within aiida.orm
"""
from aiida.orm import Node

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"


class myNodeWithFields(Node):
    # State can be updated even after storing
    _updatable_attributes = ('state',) 
