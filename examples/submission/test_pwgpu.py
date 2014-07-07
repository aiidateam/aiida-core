#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

from aiida.common.utils import load_django

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

load_django()

from aiida.common import aiidalogger
import logging
from aiida.common.exceptions import NotExistent
aiidalogger.setLevel(logging.INFO)

from aiida.orm.data.upf import UPFGROUP_TYPE
from aiida.orm import Code
from aiida.orm import DataFactory
from aiida.djsite.db.models import DbGroup

################################################################

if __name__ == "__main__":
    UpfData = DataFactory('upf')
    ParameterData = DataFactory('parameter')
    StructureData = DataFactory('structure')
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

    # If True, load the pseudos from the family specified below
    # Otherwise, use static files provided
    expected_code_type='quantumespresso.pw'
    auto_pseudos = False

    queue = None
    #queue = "Q_aries_free"

    #####

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
            print >> sys.stderr, "Pass as further parameter a valid code label."
            print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_code_type)
            for l in valid_code_labels:
                print >> sys.stderr, "*", l
        else:
            print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_code_type)
            print >> sys.stderr, "    verdi code setup"
        sys.exit(1)

    alat = 4. # angstrom
    cell = [[alat, 0., 0.,],
            [0., alat, 0.,],
            [0., 0., alat,],
           ]

    # BaTiO3 cubic structure
    s = StructureData(cell=cell)
    s.append_atom(position=(0.,0.,0.),symbols=['Ba'])
    s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
    s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
    s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
    s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])


    elements = list(s.get_symbols_set())

    if auto_pseudos:
        valid_pseudo_groups = UpfData.get_upf_groups(filter_elements=elements)

        try:
            pseudo_family = sys.argv[3]
        except IndexError:
            print >> sys.stderr, "Error, auto_pseudos set to True. You therefore need to pass as second parameter"
            print >> sys.stderr, "the pseudo family name."
            print >> sys.stderr, "Valid UPF families are:"
            print >> sys.stderr, "\n".join("* {}".format(i.name) for i in valid_pseudo_groups)
            sys.exit(1)

        try:
            UpfData.get_upf_group(pseudo_family)
        except NotExistent:
            print >> sys.stderr, "auto_pseudos is set to True and pseudo_family='{}',".format(pseudo_family)
            print >> sys.stderr, "but no group with such a name found in the DB."
            print >> sys.stderr, "Valid UPF groups are:"
            print >> sys.stderr, ",".join(i.name for i in valid_pseudo_groups)
            sys.exit(1)

    parameters = ParameterData(dict={
                'CONTROL': {
                    'calculation': 'scf',
                    'restart_mode': 'from_scratch',
                    'wf_collect': True,
                    },
                'SYSTEM': {
                    'ecutwfc': 40.,
                    'ecutrho': 320.,
                    },
                'ELECTRONS': {
                    'conv_thr': 1.e-10,
                    }})

    kpoints = ParameterData(dict={
                    'type': 'automatic',
                    'points': [4, 4, 4, 0, 0, 0],
                    })

    calc = code.new_calc()
    calc.label = "Test QE pw.x"
    calc.description = "Test calculation with the Quantum ESPRESSO pw.x code"
    calc.set_max_wallclock_seconds(30*60) # 30 min
    # Valid only for Slurm and PBS (using default values for the
    # number_cpus_per_machine), change for SGE-like schedulers 

    calc.set_custom_scheduler_commands("#SBATCH --account=ch3")

    num_machines = 2
    # num_pools can be None
    num_pools = None
    #num_pools = 2

    mpis_per_machine = 1

    calc.set_resources({"num_machines": num_machines,
                        "num_mpiprocs_per_machine": mpis_per_machine})

    # 1 MPI per node, default_mpiprocs_per_node OpenMP threads per node
    # I need to get the computer to get some properties manually
    computer = code.get_remote_computer()

    extra_mpi_params = "-N {} -d {} -cc none".format(
        str(mpis_per_machine),
        str(computer.get_default_mpiprocs_per_machine()))
    calc.set_extra_mpirun_params(extra_mpi_params.split())
    calc.set_environment_variables({
            "OMP_NUM_THREADS": str(computer.get_default_mpiprocs_per_machine()),
            "MKL_NUM_THREADS": str(computer.get_default_mpiprocs_per_machine()),
            })

    if queue is not None:
        calc.set_queue_name(queue)

    calc.use_structure(s)
    calc.use_parameters(parameters)

    if num_pools is not None:
        settings = ParameterData(dict={
                'cmdline': ['-npools', str(num_pools)]
                })
        calc.use_settings(settings)

    if auto_pseudos:
        try:
            calc.use_pseudos_from_family(pseudo_family)
            print "Pseudos successfully loaded from family {}".format(pseudo_family)
        except NotExistent:
            print ("Pseudo or pseudo family not found. You may want to load the "
                   "pseudo family, or set auto_pseudos to False.")
            raise
    else:
        raw_pseudos = [
           ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba', 'pbesol'),
           ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti', 'pbesol'),
           ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O', 'pbesol')]

        pseudos_to_use = {}
        for fname, elem, pot_type in raw_pseudos:
            absname = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                    "data",fname))
            pseudo, created = UpfData.get_or_create(
                absname,use_first=True)
            if created:
                print "Created the pseudo for {}".format(elem)
            else:
                print "Using the pseudo for {} from DB: {}".format(elem,pseudo.pk)
            pseudos_to_use[elem] = pseudo

        for k, v in pseudos_to_use.iteritems():
            calc.use_pseudo(v, kind=k)

    calc.use_kpoints(kpoints)
    #calc.use_settings(settings)
    #from aiida.orm.data.remote import RemoteData
    #calc.set_outdir(remotedata)


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
