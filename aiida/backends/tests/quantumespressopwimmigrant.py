# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for the pwimmigrant plugin for Quantum Espresso.

The directory, ``./pwtestjobs/``, contains small QE jobs that are used to test
the parsing and units conversion of an immigration. The test jobs should all
contain the same structure, input parameters, ect., but the units of the
input files differ, in order to test the unit and coordinate transformations
of the PwInputTools methods. The only thing that should vary between some of
them is the type of  k-points (manual, gamma, and automatic). For this
reason, their are three separate tests.

Note: It was necessary to break these tests up into individual classes to
prevent the SQL database from being overloaded [resulting in the error
"DatabaseError: too many SQL variables"]. Breaking up the tests into
individual classes causes the setUpClass and tearDownClass methods to be
called for each group of test jabs.

In each test, the group of test jobs with the same type of kpoints are
immigrated to create a PwimmigrantCalculation node. The inherited method,
``submit_test``, is used to create an Aiida-standard input file in a temporary
directory. The text contained in this input is read in and later compared
against the input texts of the other jobs in the group. These input texts
should match identically, with the exception of small deviations in the
numerical values contained within.

The daemon process, ``retrieve_jobs``, is called upon immigration of the group
of jobs, in order to test the correct preparation of the PwimmigrantCalculation.
"""
# TODO: Test exception handling of user errors.
import os

from aiida.orm.calculation.job.quantumespresso.pwimmigrant import PwimmigrantCalculation
from aiida.daemon.execmanager import retrieve_jobs
from aiida.common.folders import SandboxFolder
from aiida.tools.codespecific.quantumespresso.qeinputparser import str2val
from aiida.orm import Code
from aiida.backends.testbase import AiidaTestCase



# Define the path to the directory containing the test PW runs.
TEST_JOB_DIR = os.path.join(os.path.dirname(__file__), 'pwtestjobs')

# Get the prefixes of all the test jobs. The prefix defines the input and
# output file names.
PEFIXES = [fnm.strip('.in') for fnm in os.listdir(TEST_JOB_DIR)
           if fnm.endswith('.in')]


class LocalSetup(AiidaTestCase):
    """
    Setup functions that are common to all backends
    Base class for the tests.
    """

    @classmethod
    def setUpClass(cls):
        super(LocalSetup, cls).setUpClass()

        # Change transport type to local
        cls.computer.set_transport_type('local')

        # # Configure authinfo for cls.computer and cls.user.
        # authinfo = DbAuthInfo(dbcomputer=cls.computer.dbcomputer,
        #                       aiidauser=cls.user)
        # authinfo.set_auth_params({})
        # authinfo.save()

        cls.code = Code()
        cls.code.set_remote_computer_exec((cls.computer, '/x.x'))
        cls.code.store()

    def run_tests_on_calcs_with_prefixes(self, prefixes):
        """
        Test immigration, retrieval, and parsing of calcs for all prefixes.

        Prefixes should be a group of prefixes that refer to calculations whose
        Aiida-generated input files should be identical.

        :param prefixes: A group of prefixes that refer to calculations whose
            Aiida-generated input files should be identical.
        :type prefixes: list of str
        """

        # Get the computer's transport and create instance.
        Transport = self.computer.get_transport_class()
        transport = Transport()

        # Initialize arrays for storing data for each job.
        inpt_txts = []

        # Open the transport for the duration of immigrations, so it's not
        # reopened for each one. This would really matter for ssh tranports.
        with transport as t:
            # Loop over all manual prefixes.
            for prefix in prefixes:

                # Define the calc's initialization parameters. These result in
                # calling of the `set_` methods with the specified values.
                init_params = {
                    'computer': self.computer,
                    'resources': {'num_machines': 1,
                                  'num_mpiprocs_per_machine': 1},
                    'remote_workdir': TEST_JOB_DIR,
                    'input_file_name': prefix + '.in',
                    'output_file_name': prefix + '.out'
                }
                # Initialize the calculation using the `set_` methods.
                calc = PwimmigrantCalculation(**init_params)
                # Set the code.
                calc.use_code(self.code)

                # Create the input nodes.
                try:
                    calc.create_input_nodes(t)  # Open transport passed.
                except Exception as error:
                    self.fail(
                        "Error creating input nodes for prefix '{}':\n{}\n\n"
                        "".format(prefix, error)
                    )

                # Submit a test submission in a temporary directory and store
                # the input file's contents. Need to do this before now,
                # because calc's state is NEW.
                with SandboxFolder() as folder:
                    # Submit test and get the subfolder containing the input
                    # file.
                    subfolder = calc.submit_test(folder, prefix)[0]
                    # Get the path of the input file.
                    inpt_path = os.path.join(subfolder.abspath, prefix + '.in')
                    # Open the input file, read and store it's contents.
                    with open(inpt_path) as f:
                        inpt_txts.append(f.read())

                # Prepare the calc for retrieval and parsing.
                calc.prepare_for_retrieval_and_parsing(transport)

        # Call the daemon's retrieval function, so all immigrated calcs get
        # retrieved and parsed.
        try:
            retrieve_jobs()
        except Exception as error:
            self.fail("Error during retrieval of immigrated calcs:\n{}\n\n"
                      "".format(error)
            )

        # Test the create_input_nodes method by comparing the input files
        # generated above by the submit_test method. The first input file
        # will serve as the reference.
        ref_words = inpt_txts[0].split()
        for txt, prefix in zip(inpt_txts[1:], prefixes[1:]):
            # Loop over the words of the reference and current input files.
            for w1, w2 in zip(ref_words, txt.split()):

                # If the words are not the same, and the reference word is
                # not the calculation's prefix parameter...
                if w2 != w1 and w1.strip("'") not in prefixes:

                    # Try using the regex-based str2val function of
                    # pwinputparser to convert the word strings into python
                    # values.
                    try:
                        val1, val2 = [str2val(x) for x in (w1, w2)]
                    except Exception as error:
                        self.fail(
                            "The strings, '{}' and '{}', of the submit_test "
                            "input files for calcs with prefixes {} and {} "
                            "were not equal and could not be converted to "
                            "python values using the str2val function of "
                            "pwinputparser.\nThe exception thrown was:\n{"
                            "}\n\n".format(
                                w1, w2, prefixes[0], prefix, error
                            )
                        )

                    # If both values were converted to floats...
                    if all([type(v) is float for v in val1, val2]):
                        # Test if they differ by more than a specified
                        # tolerance.
                        self.assertAlmostEqual(
                            val1, val2, 4,
                            msg="The values, {} and {}, of the submit_test "
                                "input files for calcs with prefixes {} and {} "
                                "are not within the specified number of "
                                "decimal places."
                                "".format(
                                val1, val2, prefixes[0], prefix
                            )
                        )

                    # If they weren't floats, then they should have been
                    # identical, so the test fails.
                    else:
                        self.assertEqual(
                            val1, val2,
                            msg="The values, {} and {}, of the submit_test "
                                "input files for calcs with prefixes {} and {} "
                                "did not match. They should have been "
                                "identical!".format(
                                val1, val2, prefixes[0], prefix
                            )
                        )


class TestPwImmigrantCalculationManual(LocalSetup):
    """
    Tests for immigration, retrieval, and parsing of manual kpoint jobs.
    """

    def test_manual(self):
        """
        Test immigration, retrieval, and parsing of manual kpoint jobs.
        """

        # Filter out all prefixes with manually specified kpoints.
        manual_prefixes = filter(
            lambda x: 'automatic' not in x and 'gamma' not in x, PEFIXES
        )

        # Test this group of prefixes.
        self.run_tests_on_calcs_with_prefixes(manual_prefixes)


class TestPwImmigrantCalculationAutomatic(LocalSetup):
    """
    Tests for immigration, retrieval, and parsing of automatic kpoint jobs.
    """

    def test_automatic(self):
        """
        Test immigration, retrieval, and parsing of automatic kpoint jobs.
        """

        # Filter out all prefixes with automatic kpoints.
        automatic_prefixes = filter(lambda x: 'automatic' in x, PEFIXES)

        # Test this group of prefixes.
        self.run_tests_on_calcs_with_prefixes(automatic_prefixes)


class TestPwImmigrantCalculationGamma(LocalSetup):
    """
    Tests for immigration, retrieval, and parsing of gamma kpoint jobs.
    """

    def test_gamma(self):
        """
        Test immigration, retrieval, and parsing of gamma kpoint jobs.
        """

        # Filter out all prefixes with gamma kpoints.
        gamma_prefixes = filter(lambda x: 'gamma' in x, PEFIXES)

        # Test this group of prefixes.
        self.run_tests_on_calcs_with_prefixes(gamma_prefixes)
