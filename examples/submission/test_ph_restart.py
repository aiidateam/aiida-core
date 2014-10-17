#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

from aiida import load_dbenv

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

load_dbenv()

from aiida.common import aiidalogger
import logging
from aiida.common.exceptions import NotExistent
aiidalogger.setLevel(logging.INFO)

from aiida.orm import Code
from aiida.orm import CalculationFactory, DataFactory

# test phonon restart:
# do first a pw calculation (e.g. ./test_pw.py --send pw_codename)
# then use a first time this one with the previous pw calculation as parent:
# ./test_ph_restart --send pw_parent_calc_pk ph_codename
# and finally use it again with the first ph calculation as parent (no need to specify codename)
# ./test_ph_restart --send ph_parent_calc_pk


################################################################
if __name__ == '__main__':
    UpfData = DataFactory('upf')
    ParameterData = DataFactory('parameter')
    StructureData = DataFactory('structure')
    RemoteData = DataFactory('remote')

    # Used to test the parent calculation
    Calculation = CalculationFactory('Calculation')
    QEPwCalc = CalculationFactory('quantumespresso.pw') 
    QEPhCalc = CalculationFactory('quantumespresso.ph') 

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
        # parent is a pw calculation -> do a first phonon calculation
        expected_code_type='quantumespresso.ph'
        try:
            codename = sys.argv[3]
        except IndexError:
            print >> sys.stderr, ("If parent is a pw calculation, must provide "
                                  "as third parameter a phonon codename")
            sys.exit(1)
    
        try:
            if codename is None:
                raise ValueError
            code = Code.get(codename)
            if code.get_input_plugin_name() != expected_code_type: 
                raise ValueError
        except (NotExistent, ValueError):
            valid_code_labels = [c.label for c in Code.query(
                    dbattributes__key="input_plugin",
                    dbattributes__tval=expected_code_type)]
            # TODO: query also only for codes that are on the same computer
            if valid_code_labels:
                print >> sys.stderr, "Pass as first parameter a valid code label."
                print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_code_type)
                for l in valid_code_labels:
                    print >> sys.stderr, "*", l
            else:
                print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_code_type)
                print >> sys.stderr, "    verdi code setup"
            sys.exit(1)

        
        parameters = ParameterData(dict={
                    'INPUTPH': {
                        'max_seconds': 60,
                        'tr2_ph' : 1.0e-8,
                        'epsil' : True,
                        'ldisp' : True,
                        'nq1' : 2,
                        'nq2' : 2,
                        'nq3' : 2,
                        }})
    
        calc = code.new_calc()
        calc.label = "Test QE ph.x"
        calc.description = "Test calculation with the Quantum ESPRESSO ph.x code"
    
        calc.set_max_wallclock_seconds(30*60) # 30 min
        calc.set_resources({"num_machines": 1})
        if queue is not None:
            calc.set_queue_name(queue)
    
        calc.use_parameters(parameters)
        calc.use_parent_calculation( parentcalc )

    elif isinstance(parentcalc,QEPhCalc):

        # parent is a ph calculation -> do a restart phonon calculation
        if ( (parentcalc.get_state()=='FAILED') and
            ('Maximum CPU time exceeded' in parentcalc.res.warnings) ):
        
            calc = parentcalc.create_restart(restart_if_failed=True)
            calc.label = "Test QE ph.x restart"
            calc.description = "Test restart calculation with the Quantum ESPRESSO ph.x code"
        
        else:
            print >> sys.stderr, ("Parent calculation did not fail or did "
                                  "not stop because of maximum CPU time limit.")
            sys.exit(1)
            
    
    else:
        print >> sys.stderr, ("Parent calculation should be a pw.x or ph.x "
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

