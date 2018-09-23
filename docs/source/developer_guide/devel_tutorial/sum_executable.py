#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import json
import sys

in_file = sys.argv[1]
out_file = sys.argv[2]

print("Some output from the code")

with open(in_file) as f:
    in_dict = json.load(f)

out_dict = { 'sum':in_dict['x1']+in_dict['x2'] }

with open(out_file,'w') as f:
    json.dump(out_dict,f)
