#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Command line interface to dynamically create and run a WorkChain that can evaluate a reversed polish expression."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options, types
from aiida.cmdline.utils import decorators


@click.command()
@click.argument('expression', type=click.STRING, required=False)
@click.option('-d', '--daemon', is_flag=True, help='Submit the workchains to the daemon.')
@options.CODE(
    type=types.CodeParamType(entry_point='arithmetic.add'),
    required=False,
    help='Code to perform the add operations with. Required if -C flag is specified')
@click.option(
    '-C',
    '--use-calculations',
    is_flag=True,
    default=False,
    show_default=True,
    help='Use job calculations to perform all additions')
@click.option(
    '-F',
    '--use-calcfunctions',
    is_flag=True,
    default=False,
    show_default=True,
    help='Use calcfunctions to perform all substractions')
@click.option(
    '-s',
    '--sleep',
    type=click.INT,
    default=5,
    show_default=True,
    help='When submitting to the daemon, the number of seconds to sleep between polling the workchain process state')
@click.option(
    '-t',
    '--timeout',
    type=click.INT,
    default=60,
    show_default=True,
    help='When submitting to the daemon, the number of seconds to wait for a workchain to finish before timing out')
@click.option(
    '-m',
    '--modulo',
    type=click.INT,
    default=1000000,
    show_default=True,
    help='Specify an integer to modulo all intermediate and the final result to avoid integer overflow')
@click.option(
    '-n',
    '--dry-run',
    is_flag=True,
    default=False,
    help='Only evaluate the expression and generate the workchain but do not launch it')
@decorators.with_dbenv()
def launch(expression, code, use_calculations, use_calcfunctions, sleep, timeout, modulo, dry_run, daemon):
    """
    Evaluate the expression in Reverse Polish Notation in both a normal way and by procedurally generating
    a workchain that encodes the sequence of operators and gets the stack of operands as an input. Multiplications
    are modelled by a 'while_' construct and addition will be done performed by an addition or a subtraction,
    depending on the sign, branched by the 'if_' construct. Powers will be simulated by nested workchains.

    The script will generate a file containing the workchains with the procedurally generated outlines. Unless the
    dry run option is specified, the workchain will also be run and its output compared with the normal evaluation
    of the expression. If the two values match the script will be exited with a zero exit status, otherwise a non-zero
    exit status will be returned, indicating failure.

    In addition to normal rules of Reverse Polish Notation, the following restrictions to the expression apply:

     \b
     * Only integers are supported
     * Only the addition, multiplication and power operators (+, * and ^, respectively) are supported
     * Every intermediate result should be an integer, so no raising a number to a negative power
     * Operands for power operator are limited to the range [1, 3]
     * Expression has only a single sequence of numbers followed by single continuous sequence of operators

    If no expression is specified, a random one will be generated that adheres to these rules
    """
    # pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-branches
    import importlib
    import sys
    import time
    import uuid
    from aiida.orm import Code, Int, Str
    from aiida.engine import run_get_node, submit
    from lib.expression import generate, validate, evaluate
    from lib.workchain import generate_outlines, format_outlines, write_workchain

    if use_calculations and not isinstance(code, Code):
        raise click.BadParameter('if you specify the -C flag, you have to specify a code as well')

    if expression is None:
        expression = generate()

    valid, error = validate(expression)

    if not valid:
        click.echo("the expression '{}' is invalid: {}".format(expression, error))
        sys.exit(1)

    filename = 'polish_{}.py'.format(str(uuid.uuid4().hex))
    evaluated = evaluate(expression, modulo)
    outlines, stack = generate_outlines(expression)
    outlines_string = format_outlines(outlines, use_calculations, use_calcfunctions)
    write_workchain(outlines_string, filename=filename)

    click.echo('Expression: {}'.format(expression))

    if not dry_run:
        try:
            workchain_module = 'polish_workchains.{}'.format(filename.replace('.py', ''))
            workchains = importlib.import_module(workchain_module)
        except ImportError:
            click.echo('could not import the {} module'.format(workchain_module))
            sys.exit(1)

        inputs = {'modulo': Int(modulo), 'operands': Str(' '.join(stack))}

        if code:
            inputs['code'] = code

        if daemon:
            workchain = submit(workchains.Polish00WorkChain, **inputs)
            start_time = time.time()
            timed_out = True

            while time.time() - start_time < timeout:
                time.sleep(sleep)

                if workchain.is_terminated:
                    timed_out = False
                    break

            if timed_out:
                click.secho('Failed: ', fg='red', bold=True, nl=False)
                click.secho(
                    'the workchain<{}> did not finish in time and the operation timed out'.format(workchain.pk),
                    bold=True)
                sys.exit(1)

            try:
                result = workchain.outputs.result
            except AttributeError:
                click.secho('Failed: ', fg='red', bold=True, nl=False)
                click.secho('the workchain<{}> did not return a result output node'.format(workchain.pk), bold=True)
                sys.exit(1)

        else:
            results, workchain = run_get_node(workchains.Polish00WorkChain, **inputs)
            result = results['result']

    click.echo('Evaluated : {}'.format(evaluated))

    if not dry_run:
        click.echo('Workchain : {} <{}>'.format(result, workchain.pk))

        if result != evaluated:
            click.secho('Failed: ', fg='red', bold=True, nl=False)
            click.secho('the workchain result did not match the evaluated value', bold=True)
            sys.exit(1)
        else:
            click.secho('Success: ', fg='green', bold=True, nl=False)
            click.secho('the workchain accurately reproduced the evaluated value', bold=True)
            sys.exit(0)


if __name__ == '__main__':
    launch()  # pylint: disable=no-value-for-parameter
