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

from aiida.orm import load_node
from aiida.orm.data.base import Float, Str
from aiida.work.run import run
from examples.work.diamond_fcc import rescale, create_diamond_fcc
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.work.workfunction import workfunction as wf
from examples.work.equation_of_state import generate_scf_input_params


@wf
def eos(structure, codename, pseudo_family):
    Proc = PwCalculation.process()
    results = {}
    for s in (0.98, 0.99, 1.0, 1.02, 1.04):
        rescaled = rescale(structure, Float(s))
        inputs = generate_scf_input_params(rescaled, codename, pseudo_family)
        outputs = run(Proc, **inputs)
        res = outputs['output_parameters'].dict
        results[str(s)] = res

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Equation of states example.')
    parser.add_argument('--pseudo', type=str, dest='pseudo',
                        help='The pseudopotential family', required=True)
    parser.add_argument('--code', type=str, dest='code',
                        help='The codename to use', required=True)

    args = parser.parse_args()

    my_structure = create_diamond_fcc(Str("Si"), Float(5.41))

    eos(my_structure, Str(args.code), Str(args.pseudo))


