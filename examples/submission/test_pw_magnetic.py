#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

load_dbenv()

import sys
import os

from aiida.common.exceptions import NotExistent

from aiida.orm import Code, DataFactory

################################################################

if __name__ == "__main__":
    UpfData = DataFactory('upf')
    ParameterData = DataFactory('parameter')
    KpointsData = DataFactory('array.kpoints')
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
        print >> sys.stderr, ("The second parameter is the codename")
        codename = None

    expected_code_type='quantumespresso.pw'
 
    queue = None
    #queue = "Q_aries_free"
    settings = None
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

    # Iron bcc crystal structure
    from ase.lattice.spacegroup import crystal
    a = 2.83265 # lattic parameter in Angstrom
    Fe_ase = crystal('Fe', [(0,0,0)], spacegroup=229,
                     cellpar=[a, a, a, 90, 90, 90],  primitive_cell=True)
    s = StructureData(ase=Fe_ase).store()

    elements = list(s.get_symbols_set())

    valid_pseudo_groups = UpfData.get_upf_groups(filter_elements=elements)

    try:
        pseudo_family = sys.argv[3]
    except IndexError:
        print >> sys.stderr, "Error, you need to pass as third parameter"
        print >> sys.stderr, "the pseudo family name."
        print >> sys.stderr, "Valid UPF families are:"
        print >> sys.stderr, "\n".join("* {}".format(i.name) for i in valid_pseudo_groups)
        sys.exit(1)

    try:
        UpfData.get_upf_group(pseudo_family)
    except NotExistent:
        print >> sys.stderr, "pseudo_family='{}',".format(pseudo_family)
        print >> sys.stderr, "but no group with such a name found in the DB."
        print >> sys.stderr, "Valid UPF groups are:"
        print >> sys.stderr, ",".join(i.name for i in valid_pseudo_groups)
        sys.exit(1)

    max_seconds = 1000
    
    # parameters are adapted from D. Dragoni (but much less converged...)
    parameters = ParameterData(dict={
                'CONTROL': {
                    'calculation': 'scf',
                    'restart_mode': 'from_scratch',
                    'wf_collect': True,
                    'max_seconds': max_seconds,
                    'tstress': True,
                    'tprnfor': True,
                    },
                'SYSTEM': {
                    'ecutwfc': 50.,
                    'ecutrho': 600.,
                    'occupations': 'smearing',
                    'smearing': 'marzari-vanderbilt',
                    'degauss': 0.01,
                    'nspin': 2,
                    'starting_magnetization': 0.36,
                    'nosym': True,
                    },
                'ELECTRONS': {
                    'electron_maxstep': 100,
                    'mixing_beta' : 0.2,
                    'conv_thr': 1.e-10,
                    }})

    kpoints = KpointsData()
    kpoints_mesh = 10
    kpoints.set_kpoints_mesh([kpoints_mesh,kpoints_mesh,kpoints_mesh],
                             offset=[0.5, 0.5, 0.5])
    
    calc = code.new_calc()
    calc.label = "Test QE pw.x"
    calc.description = "Test calculation with the Quantum ESPRESSO pw.x code (magnetic material)"
    calc.set_max_wallclock_seconds(max_seconds)
    # Valid only for Slurm and PBS (using default values for the
    # number_cpus_per_machine), change for SGE-like schedulers 
    calc.set_resources({"num_machines": 1})
    ## Otherwise, to specify a given # of cpus per machine, uncomment the following:
    # calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 8})

    #calc.set_prepend_text("#SBATCH --account=ch3")

    if queue is not None:
        calc.set_queue_name(queue)

    calc.use_structure(s)
    calc.use_parameters(parameters)

    try:
        calc.use_pseudos_from_family(pseudo_family)
        print "Pseudos successfully loaded from family {}".format(pseudo_family)
    except NotExistent:
        print ("Pseudo or pseudo family not found. You may want to load the "
               "pseudo family, or set auto_pseudos to False.")
        raise

    calc.use_kpoints(kpoints)

    if settings is not None:
        calc.use_settings(settings)
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

