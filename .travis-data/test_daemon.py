# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import time
from aiida.orm import DataFactory
ParameterData = DataFactory('parameter')

codename = 'doubler@torquessh'
timeout_secs = 10*60 # 10 minutes
num_jobs = 30 # Num jobs to submit

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


def have_finished(pks):
    finished_list = [load_node(pk).has_finished() for pk in pks]
    num_finished = len([_ for _ in finished_list if _])
    print "{}/{} finished".format(num_finished, len(finished_list))
    return not (False in finished_list)

def results_are_ok(values_to_check):
    retval = True
    actual_value = None
    for pk, exp_value in values_to_check.iteritems():
        calc = load_node(pk)
        try:
            actual_value = int(calc.out.retrieved.folder.open('path/output.txt').read())
        except (AttributeError, IOError, ValueError) as e:
            print "* UNABLE TO RETRIEVE VALUE for calc pk={}: I expected {}, I got {}: {}".format(
                pk, exp_value, type(e), e)

            print "Output of 'verdi calculation logshow {}':".format(pk)
            try:
                print subprocess.check_output(
                    ["verdi", "calculation", "logshow", "{}".format(pk)],
                    stderr=subprocess.STDOUT,
                    )
            except subprocess.CalledProcessError as e2:
                print "Note: the command failed, message: {}".format(e2.message)            
                retval = False

        if actual_value != exp_value:
            print "* UNEXPECTED VALUE {} for calc pk={}: I expected {}".format(
                actual_value, pk, exp_value)
            retval = False

    return retval

code = Code.get_from_string(codename)
values_to_check = {}
for counter in range(1, num_jobs+1):
    inputval = counter
    parameters = ParameterData(dict={'value': inputval})
    template = ParameterData(dict={
            'cmdline_params': ["{}".format(counter % 3)], # Sleep time
            'input_file_template': "{value}", # File just contains the value to double
            'input_file_name': 'value_to_double.txt',
            'output_file_name': 'output.txt',
            })
    calc = code.new_calc()
    calc.set_max_wallclock_seconds(5 * 60)  # 5 min
    calc.set_resources({"num_machines": 1})
    calc.set_withmpi(False)
    
    calc.use_parameters(parameters)
    calc.use_template(template)
    calc.store_all()
    print "[{}] created calculation {}, pk={}".format(
        counter, calc.uuid, calc.dbnode.pk)
    values_to_check[calc.pk] = inputval*2
    calc.submit()
    print "[{}] calculation submitted.".format(counter)

pks = sorted(values_to_check.keys())

print "Wating for end of execution..."
start_time = time.time()
exited_with_timeout = True
while time.time() - start_time < timeout_secs:
    time.sleep(15) # Wait a few seconds
    
    # print some debug info, both for debugging reasons and to avoid
    # that the test machine is shut down because there is no output

    print "#"*78
    print "####### TIME ELAPSED: {} s".format(time.time() - start_time)
    print "#"*78
    print "Output of 'verdi calculation list':"
    try:
        print subprocess.check_output(
            ["verdi", "calculation", "list"], 
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

    if have_finished(pks):
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
    if results_are_ok(values_to_check):
        print_daemon_log()
        print ""
        print "OK, all calculations have the expected parsed result"
        sys.exit(0)
    else:
        print_daemon_log()
        print ""
        print "ERROR! Some return values are different from the expected value"
        sys.exit(3)
        
