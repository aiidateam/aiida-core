#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

load_dbenv()

import sys
import os

import numpy

from aiida.common.exceptions import NotExistent

from aiida.orm import Code, Calculation, DataFactory

################################################################
if __name__ == "__main__":
    ParameterData = DataFactory('parameter')
    KpointsData = DataFactory('array.kpoints')
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
        codename = sys.argv[3]
    except IndexError:
        print >> sys.stderr, ("Must provide as further parameters the parent ID and "
                         "a matdyn codename")
        sys.exit(1)

    num_machines = 1 # node numbers
    queue = None

    #####
    expected_code_type='quantumespresso.matdyn'

    try:
        parent_id = int(parent_id)
    except ValueError:
        print >> sys.stderr, 'Parent_id not an integer: {}'.format(parent_id)
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
        if valid_code_labels:
            print >> sys.stderr, "Pass as first parameter a valid code label."
            print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_code_type)
            for l in valid_code_labels:
                print >> sys.stderr, "*", l
        else:
            print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_code_type)
            print >> sys.stderr, "    verdi code setup"
        sys.exit(1)

    computer = code.get_remote_computer()

    parameters = ParameterData(dict={
                'INPUT': {
                    'asr': 'simple',
                    },
                })
    
    # additional settings specifying that we want to retrieve also the file with
    # phonon displacements
    settings = ParameterData(dict={
                'additional_retrieve_list': ['phonon_displacements.dat'],
                })

    parentcalc = Calculation.get_subclass_from_pk(parent_id)

    kpoints = KpointsData()
    try:
        structure = parentcalc.inp.parent_calc_folder.inp.retrieved.inp.parent_calc_folder.inp.remote_folder.inp.structure
        kpoints.set_cell_from_structure(structure)
        kpoints.set_kpoints_path()
    except AttributeError:
        kpoints.set_kpoints([[i,i,0] for i in numpy.linspace(0,1,10)])

    calc = code.new_calc(computer=computer)
    calc.label = "Test QE matdyn.x"
    calc.description = "Test calculation with the Quantum ESPRESSO matdyn.x code"
    calc.set_max_wallclock_seconds(60*30) # 30 min
    calc.set_resources({"num_machines":num_machines})

    calc.use_parameters(parameters)
    calc.use_settings(settings) # additional settings (comment if you don't want to retrieve the phonon displacements file)
    calc.use_kpoints(kpoints)
    calc.use_parent_calculation(parentcalc)

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
