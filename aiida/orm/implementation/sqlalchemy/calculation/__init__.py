# -*- coding: utf-8 -*-

from aiida.orm.implementation.general.calculation import AbstractCalculation
from aiida.orm.implementation.sqlalchemy.node import Node



class Calculation(AbstractCalculation, Node):
    pass
