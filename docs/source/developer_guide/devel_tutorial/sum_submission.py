#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys
import os

from aiida.common.exceptions import NotExistent
ParameterData = DataFactory('parameter')

# The name of the code setup in AiiDA
codename = 'sum'
computer_name = 'localhost'

################################################################
try:
    dontsend = sys.argv[1]
    if dontsend == "--dont-send":
        submit_test = True
    elif dontsend == "--send":
        submit_test = False
    else:
        raise IndexError
except IndexError:
    print >> sys.stderr, ("The first parameter can only be either "
                          "--send or --dont-send")
    sys.exit(1)

code = Code.get_from_string(codename)
# The following line is only needed for local codes, otherwise the
# computer is automatically set from the code
computer = Computer.get(computer_name) 

# These are the two numbers to sum
parameters = ParameterData(dict={'x1':2,'x2':3})

calc = code.new_calc()
calc.label = "Test sum"
calc.description = "Test calculation with the sum code"
calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_computer(computer)
calc.set_withmpi(False)
calc.set_resources({"num_machines": 1})

calc.use_parameters(parameters)

if submit_test:
    subfolder, script_filename = calc.submit_test()
    print "Test submit file in {}".format(os.path.join(
        os.path.relpath(subfolder.abspath),
        script_filename
        ))
else:
    calc.store_all()
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)