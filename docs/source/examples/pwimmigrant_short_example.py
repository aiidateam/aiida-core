#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Load the database environment.
from aiida import load_dbenv
load_dbenv()

from aiida.orm.code import Code
from aiida.orm import CalculationFactory


# Load the PwimmigrantCalculation class.
PwimmigrantCalculation = CalculationFactory('quantumespresso.pwimmigrant')

# Load the Code node representative of the one used to perform the calculations.
code = Code.get('pw_on_TheHive')

# Get the Computer node representative of the one the calculations were run on.
computer = code.get_remote_computer()

# Define the computation resources used for the calculations.
resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}

# Initialize the pw_job1 calculation node.
calc1 = PwimmigrantCalculation(computer=computer,
                               resources=resources,
                               remote_workdir='/scratch/',
                               input_file_name='pw_job1.in',
                               output_file_name='pw_job1.out')

# Initialize the pw_job2 calculation node.
calc2 = PwimmigrantCalculation(computer=computer,
                               resources=resources,
                               remote_workdir='/scratch/',
                               input_file_name='pw_job2.in',
                               output_file_name='pw_job2.out')

# Link the code that was used to run the calculations.
calc1.use_code(code)
calc2.use_code(code)

# Get the computer's transport and create an instance.
from aiida.backends.utils import get_authinfo, get_automatic_user
authinfo = get_authinfo(computer=computer, aiidauser=get_automatic_user())
transport = a.get_transport()

# Open the transport for the duration of the immigrations, so it's not
# reopened for each one. This is best performed using the transport's
# context guard through the ``with`` statement.
with transport as open_transport:

    # Parse the calculations' input files to automatically generate and link the
    # calculations' input nodes.
    calc1.create_input_nodes(open_transport)
    calc2.create_input_nodes(open_transport)

    # Store the calculations and their input nodes and tell the daeomon the output
    # is ready to be retrieved and parsed.
    calc1.prepare_for_retrieval_and_parsing(open_transport)
    calc2.prepare_for_retrieval_and_parsing(open_transport)