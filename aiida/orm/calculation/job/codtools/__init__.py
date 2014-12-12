# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

def commandline_params_from_dict(dictionary):
    commandline_params = []
    for k in dictionary.keys():
        v = dictionary[k]
        if v is None:
            continue
        if not isinstance(v, list):
            v = [ v ]
        key = None
        if len( k ) == 1:
            key = "-{}".format( k )
        else:
            key = "--{}".format( k )
        for val in v:
            if isinstance(val, bool) and val == False:
                continue
            commandline_params.append( key )
            if not isinstance(val, bool):
                commandline_params.append( val )
    return commandline_params
