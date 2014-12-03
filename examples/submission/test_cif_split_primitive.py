#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

load_dbenv()

import sys
import os

from aiida.common.exceptions import NotExistent

from aiida.orm import Code, Computer, DataFactory

################################################################
# Test for cif_filter script from cod-tools package.
# Input plugin: codtools
# Accepted codes: cif_filter
################################################################

if __name__ == "__main__":
    CifData = DataFactory('cif')
    ParameterData = DataFactory('parameter')
    submit_test = None
    codename = None
    options = {}
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
            options[argkey].append( argval )
        else:
            files.append( arg )

    expected_code_type = "codtools.cifsplitprimitive"

    try:
        if codename is None:
            raise ValueError
        code = Code.get_from_string(codename)
        if code.get_input_plugin_name() != expected_code_type:
            raise ValueError
    except (NotExistent, ValueError):
        valid_code_labels = [c.label for c in Code.query(
                dbattributes__key="input_plugin",
                dbattributes__tval=expected_code_type)]
        if valid_code_labels:
            print >> sys.stderr, "Pass as further parameter a valid code label."
            print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_code_type)
            for l in valid_code_labels:
                print >> sys.stderr, "*", l
        else:
            print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_code_type)
            print >> sys.stderr, "    verdi code setup"
        sys.exit(1)

    cif = None
    if len(files) == 1:
        cif = CifData(file=os.path.abspath(files[0]))
    else:
        raise ValueError("Please specify a single CIF file")

    parameters = ParameterData(dict=options)
    computer = Computer.get( Computer.list_names()[0] )

    calc = code.new_calc()
    calc.label = "Test cod-tools cif_split_primitive"
    calc.description = "Test calculation with the cod-tools cif_split_primitive"
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_resources({"num_machines": 1})
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
            calc.uuid,calc.dbnode.pk)
        calc.submit()
        print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
            calc.uuid,calc.dbnode.pk)
