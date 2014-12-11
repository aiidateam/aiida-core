#!/usr/bin/env python
import json
import sys

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

in_file = sys.argv[1]
out_file = sys.argv[2]

with open(in_file) as f:
    in_dict = json.load(f)

out_dict = { 'sum':in_dict['x1']+in_dict['x2'] }

with open(out_file,'w') as f:
    json.dump(out_dict,f)

