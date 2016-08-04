#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from aiida.workflows.wf_XTiO3 import WorkflowXTiO3_EOS
import sys
from aiida.common.example_helpers import test_and_get_code

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

# This example runs a set of calculation for at various lattice parameter
# and fit a BirchMurnaghan equation of state.
# Requires pylab installed

############# INPUT #############

element = 'Ba'  # cation in XTiO3
starting_alat = 4.  # central point of the Murnaghan curve

#################################

UpfData = DataFactory('upf')

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
    codename = sys.argv[2]
except IndexError:
    codename = None
code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')

valid_pseudo_groups = UpfData.get_upf_groups(filter_elements=[element, 'Ti', 'O'])
try:
    pseudo_family = sys.argv[3]
except IndexError:
    print >> sys.stderr, "Error, you must pass as second parameter the pseudofamily"
    print >> sys.stderr, "Valid UPF families are:"
    print >> sys.stderr, "\n".join("* {}".format(i.name) for i in valid_pseudo_groups)
    sys.exit(1)

try:
    UpfData.get_upf_group(pseudo_family)
except NotExistent:
    print >> sys.stderr, "You set pseudo_family='{}',".format(pseudo_family)
    print >> sys.stderr, "but no group with such a name found in the DB."
    print >> sys.stderr, "Valid UPF groups are:"
    print >> sys.stderr, ",".join(i.name for i in valid_pseudo_groups)
    sys.exit(1)

ParameterData = DataFactory('parameter')

params_dict = {'pw_codename': codename,
               'num_machines': 1,
               'max_wallclock_seconds': 60 * 20,
               'pseudo_family': pseudo_family,
               'x_material': element,
               'starting_alat': starting_alat,
               'alat_steps': 10,
}

w = WorkflowXTiO3_EOS()
w.set_params(params_dict)

if not submit_test:
    w.store()
    w.start()
