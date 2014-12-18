#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

if __name__ == "__main__":
    try:
        computername = sys.argv[1]
    except IndexError:
        print >> sys.stderr, "Pass the machine name."
        sys.exit(1)

    from aiida import load_dbenv
    load_dbenv()

    from aiida.common import aiidalogger
    import logging
    aiidalogger.setLevel(logging.INFO)

    import tempfile
    import datetime

    from aiida.orm import Code, Computer, CalculationFactory
    from aiida.orm.data.parameter import ParameterData
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.orm.data.remote import RemoteData

    from aiida.common.exceptions import NotExistent

    # print ParameterData.__module__

    # A string with the version of this script, used to recreate a code when necessary
    current_version = "1.0.5"
    queue = None
    # queue = "P_share_queue"


    def get_or_create_code():
        useful_codes = Code.query(dbattributes__key="_local_executable",
                                  dbattributes__tval="sum.py").filter(
                                      dbattributes__key="version", dbattributes__tval=current_version)

        if not(useful_codes):
            print >> sys.stderr, "Creating the code..."
            with tempfile.NamedTemporaryFile() as f:
                f.write("""#!/usr/bin/env python
    import sys

    try:
        with open('factor.dat') as f:
           factor = float(f.read().strip())
    except IOError:
        print >> sys.stderr, "No factor file found, using factor = 1"
    except ValueError:
        print >> sys.stderr, "The value in factor.dat is not a valid number"
        sys.exit(1)

    try:
        print factor*float(sys.argv[1])+float(sys.argv[2])
    except KeyError:
        print >> sys.stderr, "Pass two numbers on the command line"
        sys.exit(1)
    except ValueError:
        print >> sys.stderr, "The values on the command line are not valid numbers"
        sys.exit(1)

    try:
        with open('check.txt') as f:
            print '*'*80
            print "Read from file check.txt:"
            print f.read()
            print '*'*80
    except IOError:
        print >> sys.stderr, "No check file found!"
        sys.exit(1)
    """)
                f.flush()
                code = Code(local_executable="sum.py")
                code.add_path(f.name, "sum.py")
                code.store()
                code.set_extra("version", current_version)
            return code

        elif len(useful_codes) == 1:
            print >> sys.stderr, "Using the existing code {}...".format(useful_codes[0].uuid)
            return useful_codes[0]
        else:
            raise ValueError("More than one valid code!")


    #####

    try:
        computer = Computer.get(computername)
    except NotExistent:
        print >> sys.stderr, ("Unknown computer '{0}'. Use "
          "'verdi computer setup {0}' first.".format(computername))
        sys.exit(1)
    code = get_or_create_code()

    template_data = ParameterData(dict={
        'input_file_template': "{factor}\n",
        # TODO: pass only input_file_name and no template and see if an error is raised
        'input_file_name': "factor.dat",
        'cmdline_params': ["{add1}", "{add2}"],
        'output_file_name': "result.txt",
        'files_to_copy': [('the_only_local_file', 'check.txt'),
                          ('the_only_remote_node', 'bashrc-copy')],
        }).store()

    parameters = ParameterData(dict={
        'add1': 3.45,
        'add2': 7.89,
        'factor': 2,
        }).store()

    with tempfile.NamedTemporaryFile() as f:
        f.write("double check, created @ {}".format(datetime.datetime.now()))
        f.flush()
        # I don't worry of the name with which it is internally stored
        fileparam = SinglefileData(file=f.name).store()

    remoteparam = RemoteData(computer=computer,
                             remote_path="/etc/inittab").store()

    CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
    calc = CustomCalc(computer=computer, withmpi=True)
    calc.set_max_wallclock_seconds(12 * 60)  # 12 min
    jr_class = computer.get_scheduler()._job_resource_class

    from aiida.scheduler.datastructures import NodeNumberJobResource, ParEnvJobResource

    if issubclass(jr_class, NodeNumberJobResource):
        calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
    elif issubclass(jr_class, ParEnvJobResource):
        calc.set_resources({"parallel_env": 'smp', "tot_num_mpiprocs": 1})
    else:
        print >> sys.stderr, "Unknown Job resource type: {}".format(str(jr_class))
        sys.exit(1)

    if queue is not None:
        calc.set_queue_name(queue)
    calc.store()
    print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk)

    calc.use_code(code)
    # # Just for debugging purposes, I check that I can 'reset' the code
    # calc.use_code(code)

    # Should not be done by hand... To improve
    calc._add_link_from(template_data, label="template")
    calc._add_link_from(parameters, label="parameters")
    calc._add_link_from(fileparam, label="the_only_local_file")
    calc._add_link_from(remoteparam, label="the_only_remote_node")

    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk)

