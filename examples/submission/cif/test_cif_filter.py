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

from aiida.common.example_helpers import test_and_get_code

################################################################
# Test for cif_filter script from cod-tools package.
# Input plugin: codtools
# Accepted codes: cif_filter
################################################################

CifData = DataFactory('cif')
ParameterData = DataFactory('parameter')
submit_test = None
codename = None
options = {"use-perl-parser": True}
files = []

sys.argv.pop(0)
while len(sys.argv) > 0:
    arg = sys.argv.pop(0)
    if arg == '--send':
        submit_test = False
        codename = sys.argv.pop(0)
    elif arg == '--dont-send':
        submit_test = True
        codename = sys.argv.pop(0)
    elif arg == '--arg':
        argkey = None
        argval = None
        if '=' in sys.argv[0]:
            argkey, argval = sys.argv.pop(0).split('=', 1)
        else:
            argkey = sys.argv.pop(0)
            argval = True
        if argkey not in options.keys():
            options[argkey] = []
        options[argkey].append(argval)
    else:
        files.append(arg)

code = test_and_get_code(codename, expected_code_type="codtools.ciffilter")

cif = None
if len(files) == 1:
    cif = CifData(file=os.path.abspath(files[0]))
else:
    raise ValueError("Please specify a single CIF file")

parameters = ParameterData(dict=options)
computer = Computer.get(Computer.list_names()[0])

calc = code.new_calc()
calc.label = "Test cod-tools cif_filter"
calc.description = "Test calculation with the cod-tools cif_filter"
calc.set_max_wallclock_seconds(30 * 60)  # 30 min
calc.set_resources({"num_machines": 1,
                    "num_mpiprocs_per_machine": 1})
calc.set_computer(computer)

calc.use_cif(cif)
calc.use_parameters(parameters)

if submit_test:
    subfolder, script_filename = calc.submit_test()
    print "Test_submit for calculation (uuid='{}')".format(
        calc.uuid)
    print "Submit file in {}".format(os.path.join(
        os.path.relpath(subfolder.abspath),
        script_filename
    ))
else:
    calc.store_all()
    print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk)
