# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm.data.base import Float, Str
from aiida.work.run import run, async
from examples.work.diamond_fcc import rescale, create_diamond_fcc
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.work import workfunction as wf
from examples.work.equation_of_state import generate_scf_input_params
from aiida.work.globals import enable_rmq_all

PwProcess = PwCalculation.process()


@wf
def eos(structure, codename, pseudo_family):
    results = {}
    for s in (0.98, 0.99, 1.0, 1.02, 1.04):
        rescaled = rescale(structure, Float(s))
        inputs = generate_scf_input_params(rescaled, codename, pseudo_family)
        outputs = run(PwProcess, **inputs)
        results[str(s)] = outputs['output_parameters']
        print("{}: {}".format(s, outputs))

    return results


@wf
def eos_async(structure, codename, pseudo_family):
    futures = {}
    for s in (0.98, 0.99, 1.0, 1.02, 1.04):
        # for s in [1 - (f/100.) for f in range(-50, 50)]:
        rescaled = rescale(structure, Float(s))
        inputs = generate_scf_input_params(rescaled, codename, pseudo_family)
        # PwProcess.new(inputs).calc.submit()
        futures[s] = async(PwProcess, **inputs)

    # Collect all the results
    results = {}
    for s, future in futures.iteritems():
        outputs = future.result()['output_parameters']
        results[str(s)] = outputs
        print("{}: {}".format(s, outputs))

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Equation of states example.')
    parser.add_argument('--pseudo', type=str, dest='pseudo',
                        help='The pseudopotential family', required=True)
    parser.add_argument('--code', type=str, dest='code',
                        help='The codename to use', required=True)
    parser.add_argument('--async', action='store_true')

    args = parser.parse_args()

    my_structure = create_diamond_fcc(Str("Si"), Float(5.41))

    enable_rmq_all()
    if args.async:
        eos_async(my_structure, Str(args.code), Str(args.pseudo))
    else:
        eos(my_structure, Str(args.code), Str(args.pseudo))
