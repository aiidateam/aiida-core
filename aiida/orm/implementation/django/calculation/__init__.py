# -*- coding: utf-8 -*-

from aiida.orm.implementation.django.node import Node
from aiida.orm.implementation.general.calculation import AbstractCalculation



class Calculation(AbstractCalculation, Node):
    pass
