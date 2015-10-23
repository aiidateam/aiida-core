#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"

in_file = sys.argv[1]
out_file = sys.argv[2]

print "Sum executable filename"

with open(in_file) as f:
    in_dict = json.load(f)

out_dict = { 'sum':in_dict['x1']+in_dict['x2'] }

with open(out_file,'w') as f:
    json.dump(out_dict,f)

