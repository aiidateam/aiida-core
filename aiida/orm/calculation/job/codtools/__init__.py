# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi, Martin Uhrin"


def commandline_params_from_dict(dictionary):
    commandline_params = []
    for k in dictionary.keys():
        v = dictionary[k]
        if v is None:
            continue
        if not isinstance(v, list):
            v = [v]
        key = None
        if len(k) == 1:
            key = "-{}".format(k)
        else:
            key = "--{}".format(k)
        for val in v:
            if isinstance(val, bool) and val == False:
                continue
            commandline_params.append(key)
            if not isinstance(val, bool):
                commandline_params.append(val)
    return commandline_params
