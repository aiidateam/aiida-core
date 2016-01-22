# -*- coding: utf-8 -*-

from ..node import Node
from aiida.orm.implementation.general.calculation import AbstractCalculation

class Calculation(AbstractCalculation, Node):
    pass
