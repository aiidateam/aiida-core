#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"

load_dbenv()

import sys
import os

from aiida.common.exceptions import NotExistent

from aiida.orm import Code, DataFactory
from aiida.orm.data.float import FloatData

if __name__ == "__main__":
    
    codename = 'sum@theospc22'

    ParameterData = DataFactory('parameter')
    
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
    code.set_input_plugin_name('floatsum')


    calc = code.new_calc()
    calc.label = "Test sum"
    calc.description = "Test calculation with the sum code"
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 2})

    f1 = FloatData()
    f1.value = 2.1
    calc.use_floatdata1(f1)
    f2 = FloatData()
    f2.value = 3.2
    calc.use_floatdata2(f2)

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

