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

from aiida.orm import Code, DataFactory

################################################################

if __name__ == "__main__":
    
    codename = 'put here the name of the installed code'

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
    
    #####
    
    code = Code.get(codename)
    
    parameters = ParameterData(dict={'x1': 2,'x2':2,})
    
    calc = code.new_calc()
    calc.label = "Test sum"
    calc.description = "Test calculation with the sum code"
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_withmpi(False)
    # Valid only for Slurm and PBS (using default values for the
    # number_cpus_per_machine), change for SGE-like schedulers 
    calc.set_resources({"num_machines": 1})
    
    ## Otherwise, to specify a given # of cpus per machine, uncomment the following:
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

