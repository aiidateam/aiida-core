#!/usr/bin/env python
# -*- coding: utf-8 -*-
import importlib
import sys
import click
from aiida.utils.cli import command
from aiida.utils.cli import options
from expression import generate, validate, evaluate
from workchain import generate_outlines, format_outlines, write_workchain


@command()
@click.argument('expression', type=click.STRING, required=False)
@options.code(callback_kwargs={'entry_point': 'simpleplugins.arithmetic.add'}, required=False,
    help='Code to perform the add operations with. Required if -C flag is specified')
@click.option('-C', '--use-calculations', is_flag=True, default=False,
    help='Use job calculations to perform all additions')
@click.option('-W', '--use-workfunctions', is_flag=True, default=False,
    help='Use workfunctions to perform all substractions')
@click.option('-n', '--dry-run', is_flag=True, default=False,
    help='Only evaluate the expression and generate the workchain but do not launch it')
def launch(expression, code, use_calculations, use_workfunctions, dry_run):
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
    from aiida.orm.data.str import Str
    from aiida.work.launch import run_get_node, submit

    if expression is None:
        expression = generate()

    valid, error = validate(expression)
    
    if not valid:
        click.echo("the expression '{}' is invalid: {}".format(expression, error))
        sys.exit(1)

    evaluated = evaluate(expression)
    outlines, stack = generate_outlines(expression)
    outlines_string = format_outlines(outlines, use_calculations, use_workfunctions)
    workchain_filename = write_workchain(outlines_string)

    if not dry_run:
        try:
            workchain_module = 'workchains.polish'
            workchains = importlib.import_module(workchain_module)
        except ImportError:
            click.echo('could not import the {} module'.format(workchain_module))
            sys.exit(1)

        result, workchain = run_get_node(workchains.Polish00WorkChain, code=code, operands=Str(' '.join(stack)))

    click.echo('Expression: {}'.format(expression))
    click.echo('Evaluated : {}'.format(evaluated))

    if not dry_run:
        click.echo('Workchain : {} <{}>'.format(result['result'], result['result'].pk))

        if result['result'] != evaluated:
            click.secho('Failed: ', fg='red', bold=True, nl=False)
            click.secho('the workchain result did not match the evaluated value', bold=True)
            sys.exit(1)
        else:
            click.secho('Success: ', fg='green', bold=True, nl=False)
            click.secho('the workchain accurately reproduced the evaluated value', bold=True)
            sys.exit(0)

if __name__ == '__main__':
    launch()
