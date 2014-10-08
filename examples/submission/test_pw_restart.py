#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

from aiida.common.utils import load_django

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

load_django()

from aiida.common import aiidalogger
import logging
from aiida.common.exceptions import NotExistent
aiidalogger.setLevel(logging.INFO)

from aiida.orm import Code
from aiida.orm import CalculationFactory, DataFactory

# test pw restart:
# do first a pw calculation (e.g. ./test_pw.py --send pw_codename, or 
# ./test_pw_vcrelax.py --send pw_codename)
# then use a this one with the previous pw calculation as parent
# (no need to specify codename):
# ./test_pw_restart --send pw_parent_calc_pk


################################################################
if __name__ == '__main__':
    UpfData = DataFactory('upf')
    ParameterData = DataFactory('parameter')
    StructureData = DataFactory('structure')
    RemoteData = DataFactory('remote')

    # Used to test the parent calculation
    Calculation = CalculationFactory('Calculation')
    QEPwCalc = CalculationFactory('quantumespresso.pw') 

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

    try:
        parent_id = sys.argv[2]
    except IndexError:
        print >> sys.stderr, ("Must provide as second parameter the parent ID")
        sys.exit(1)

    
    #####
    # test parent
    
    try:
        int(parent_id)
    except ValueError:
        raise ValueError('Parent_id not an integer: {}'.format(parent_id))

    parentcalc = Calculation.get_subclass_from_pk(parent_id)

    queue = None
    #queue = "P_share_queue"
    
    #####

    if isinstance(parentcalc,QEPwCalc):

        # do a restart pw calculation
        if ( (parentcalc.get_state()=='FAILED') and
            ('Maximum CPU time exceeded' in parentcalc.res.warnings) ):
        
            calc = parentcalc.create_restart(restart_if_failed=True)
            calc.label = "Test QE pw.x restart"
            calc.description = "Test restart calculation with the Quantum ESPRESSO pw.x code"
        
        else:
            print >> sys.stderr, ("Parent calculation did not fail or did "
                                  "not stop because of maximum CPU time limit.")
            sys.exit(1)
            
    
    else:
        print >> sys.stderr, ("Parent calculation should be a pw.x "
                              "calculation.")
        sys.exit(1)
    
    ######

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

