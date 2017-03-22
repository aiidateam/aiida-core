# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



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
