# -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from aiida.orm import Data
from aiida.orm.data.simple import SimpleData
from collections import Mapping

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class Outputs(Mapping):
    def __init__(self, outs):
        if not isinstance(outs, dict):
            raise ValueError("Outputs must be a dictionary of labels and values")

        for k, v in outs.iteritems():
            if not isinstance(v, Data):
                raise ValueError(
                    "Output {} is not of an AiiDA data type".format(k))

        self.outs = outs

    def __getitem__(self, key):
        return self.outs.__getitem__(key)

    def __len__(self):
        return self.outs.__len__()

    def __iter__(self):
        return self.outs.__iter__()

    def __contains__(self, x):
        return self.outs.__contains__(x)


def to_db_type(value):
    if isinstance(value, Data):
        return value
    elif isinstance(value, int):
        return SimpleData(int, value)
    elif isinstance(value, float):
        return SimpleData(float, value)
    elif isinstance(value, bool):
        return SimpleData(bool, value)
    elif isinstance(value, str):
        return SimpleData(str, value)
    else:
        raise ValueError("Cannot convert value to database type")


def to_native_type(data):
    if not isinstance(data, Data):
        return data
    elif isinstance(data, SimpleData):
        return data.value
    else:
        raise ValueError("Cannot convert from database to native type")
