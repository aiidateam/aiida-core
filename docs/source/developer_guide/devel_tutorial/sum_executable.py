#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys

in_file = sys.argv[1]
out_file = sys.argv[2]

print "Some output from the code"

with open(in_file) as f:
    in_dict = json.load(f)

out_dict = { 'sum':in_dict['x1']+in_dict['x2'] }

with open(out_file,'w') as f:
    json.dump(out_dict,f)

