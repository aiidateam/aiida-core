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

################################################################
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')
RemoteData = DataFactory('remote')

# Used to test the parent calculation
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

    calc = parentcalc.create_restart(use_output_structure=True)
    calc.label = "Test QE pw.x band structure"
    calc.description = "Test restart calculation with the Quantum ESPRESSO pw.x code"

else:
    print >> sys.stderr, ("Parent calculation should be a pw.x "
                          "calculation.")
    sys.exit(1)

######
try:
    settings_dict = calc.inp.settings.get_dict()
except AttributeError:
    settings_dict = {}
settings_dict.update({'also_bands': True,
                      'PARENT_FOLDER_SYMLINK': True})

new_input_dict = calc.inp.parameters.get_dict()
if not parentcalc.res.smearing_method:
    num_elec = parentcalc.res.number_of_electrons
    new_input_dict['SYSTEM']['nbnd'] = int(num_elec/2)+max(4,int(0.125*num_elec))

new_input_dict['CONTROL'].update({'calculation': 'bands'})
try:
    new_input_dict['ELECTRONS']['diago_full_acc'] = True
except KeyError:
    new_input_dict['ELECTRONS'] = {'diago_full_acc': True}

kpoints = KpointsData()
kpoints.set_cell(calc.inp.structure.cell, calc.inp.structure.pbc)
kpoints.set_kpoints_path(kpoint_distance = 0.05)

calc.use_kpoints(kpoints)
calc.use_parameters(ParameterData(dict=new_input_dict))
calc.use_settings(ParameterData(dict=settings_dict))

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
    print "created calculation; calc=Calculation(uuid='{}') # ID: {}".format(
        calc.uuid,calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID: {}".format(
        calc.uuid,calc.dbnode.pk)

