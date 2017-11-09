# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import subprocess
import sys
import time
from aiida.common.exceptions import NotExistent
from aiida.orm import DataFactory
from aiida.orm.data.base import Int
from aiida.work.run import submit
from workchains import ParentWorkChain

ParameterData = DataFactory('parameter')

codename = 'doubler@torquessh'
timeout_secs = 4 * 60 # 4 minutes
number_calculations = 30 # Number of calculations to submit
number_workchains = 30 # Number of workchains to submit

def print_daemon_log():
    home = os.environ['HOME']
    print "Output of 'cat {}/.aiida/daemon/log/aiida_daemon.log':".format(home)
    try:
        print subprocess.check_output(
            ["cat", "{}/.aiida/daemon/log/aiida_daemon.log".format(home)], 
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print "Note: the command failed, message: {}".format(e.message)

def jobs_have_finished(pks):
    finished_list = [load_node(pk).has_finished() for pk in pks]
    num_finished = len([_ for _ in finished_list if _])
    print "{}/{} finished".format(num_finished, len(finished_list))
    return not (False in finished_list)

def print_logshow(pk):
    print "Output of 'verdi calculation logshow {}':".format(pk)
    try:
        print subprocess.check_output(
            ["verdi", "calculation", "logshow", "{}".format(pk)],
            stderr=subprocess.STDOUT,
            )
    except subprocess.CalledProcessError as e2:
        print "Note: the command failed, message: {}".format(e2.message)

def validate_calculations(expected_results):
    valid = True
    actual_dict = {}
    for pk, expected_dict in expected_results.iteritems():
        calc = load_node(pk)
        if not calc.has_finished_ok():
            print 'Calculation<{}> status was not FINISHED'.format(pk)
            print_logshow(pk)
            return False

        try:
            actual_dict = calc.out.output_parameters.get_dict()
        except (KeyError, AttributeError) as exception:
            print 'Could not retrieve output_parameters node for Calculation<{}>'.format(pk)
            print_logshow(pk)
            return False

        try:
            actual_dict['retrieved_temporary_files'] = dict(actual_dict['retrieved_temporary_files'])
        except KeyError:
            # If the retrieval fails we simply pass as the following check of the actual value will fail anyway
            pass

        if actual_dict != expected_dict:
            print "* UNEXPECTED VALUE {} for calc pk={}: I expected {}".format(
                actual_dict, pk, expected_dict)
            valid = False

    return valid

def validate_workchains(expected_results):
    valid = True
    for pk, expected_value in expected_results.iteritems():
        try:
            calc = load_node(pk)
            actual_value = calc.out.output
        except (NotExistent, AttributeError) as exception:
            print "* UNABLE TO RETRIEVE VALUE for workchain pk={}: I expected {}, I got {}: {}".format(
                pk, expected_value, type(exception), exception)

        if actual_value != expected_value:
            print "* UNEXPECTED VALUE {} for workchain pk={}: I expected {}".format(
                actual_value, pk, expected_value)
            valid = False

    return valid

def main():

    # Submitting the Calculations
    print "Submitting {} calculations to the daemon".format(number_calculations)
    code = Code.get_from_string(codename)
    expected_results_calculations = {}
    for counter in range(1, number_calculations + 1):
        inputval = counter
        parameters = ParameterData(dict={'value': inputval})
        template = ParameterData(dict={
                'cmdline_params': ["{}".format(counter % 3)], # Sleep time
                'input_file_template': "{value}", # File just contains the value to double
                'input_file_name': 'value_to_double.txt',
                'output_file_name': 'output.txt',
                'retrieve_temporary_files': ['triple_value.tmp']
                })
        calc = code.new_calc()
        calc.set_max_wallclock_seconds(5 * 60)  # 5 min
        calc.set_resources({"num_machines": 1})
        calc.set_withmpi(False)
        calc.set_parser_name('simpleplugins.templatereplacer.test.doubler')
        
        calc.use_parameters(parameters)
        calc.use_template(template)
        calc.store_all()
        print "[{}] created calculation {}, pk={}".format(
            counter, calc.uuid, calc.dbnode.pk)
        expected_results_calculations[calc.pk] = {
            'value': inputval * 2,
            'retrieved_temporary_files': {
                'triple_value.tmp': str(inputval * 3)
            }
        }
        calc.submit()
        print "[{}] calculation submitted.".format(counter)

    # Submitting the Workchains
    print "Submitting {} workchains to the daemon".format(number_workchains)
    expected_results_workchains = {}
    for index in range(1, number_workchains + 1):
        inp = Int(index)
        future = submit(ParentWorkChain, inp=inp)
        expected_results_workchains[future.pid] = index * 2


    calculation_pks = sorted(expected_results_calculations.keys())
    workchains_pks = sorted(expected_results_workchains.keys())
    pks = calculation_pks + workchains_pks

    print "Wating for end of execution..."
    start_time = time.time()
    exited_with_timeout = True
    while time.time() - start_time < timeout_secs:
        time.sleep(15) # Wait a few seconds
        
        # Print some debug info, both for debugging reasons and to avoid
        # that the test machine is shut down because there is no output

        print "#"*78
        print "####### TIME ELAPSED: {} s".format(time.time() - start_time)
        print "#"*78
        print "Output of 'verdi calculation list -a':"
        try:
            print subprocess.check_output(
                ["verdi", "calculation", "list", "-a"], 
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print "Note: the command failed, message: {}".format(e.message)

        print "Output of 'verdi work list':"
        try:
            print subprocess.check_output(
                ['verdi', 'work', 'list'], 
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print "Note: the command failed, message: {}".format(e.message)

        print "Output of 'verdi daemon status':"
        try:
            print subprocess.check_output(
                ["verdi", "daemon", "status"], 
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print "Note: the command failed, message: {}".format(e.message)

        if jobs_have_finished(pks):
            print "Calculation terminated its execution"
            exited_with_timeout = False
            break

    if exited_with_timeout:
        print_daemon_log()
        print ""
        print "Timeout!! Calculation did not complete after {} seconds".format(
            timeout_secs)
        sys.exit(2)
    else:
        if (validate_calculations(expected_results_calculations)
            and validate_workchains(expected_results_workchains)):
            print_daemon_log()
            print ""
            print "OK, all calculations have the expected parsed result"
            sys.exit(0)
        else:
            print_daemon_log()
            print ""
            print "ERROR! Some return values are different from the expected value"
            sys.exit(3)


if __name__ == '__main__':
    main()
