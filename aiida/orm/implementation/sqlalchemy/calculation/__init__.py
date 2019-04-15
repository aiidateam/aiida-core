# -*- coding: utf-8 -*-

from aiida.orm.implementation.sqlalchemy.node import Node
from aiida.orm.implementation.general.calculation import AbstractCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class Calculation(AbstractCalculation, Node):
    pass
