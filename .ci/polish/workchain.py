# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import os
import errno
from collections import deque
from string import Template
from expression import OPERATORS

INDENTATION_WIDTH = 4

BLOCK_TPL_INI = '{indent:}cls.setup,\n'
BLOCK_TPL_ADD_BASE = '{indent:}if_(cls.is_positive)(\n{indent_inner:}cls.add\n{indent:}).else_(\n{indent_inner:}cls.subtract\n{indent:}),\n'
BLOCK_TPL_ADD_WORK = '{indent:}if_(cls.is_positive)(\n{indent_inner:}cls.add\n{indent:}).else_(\n{indent_inner:}cls.subtract_workfunction\n{indent:}),\n'
BLOCK_TPL_ADD_CALC = '{indent:}if_(cls.is_positive)(\n{indent_inner:}cls.add_calculation,\n{indent_inner:}cls.post_add,\n{indent:}).else_(\n{indent_inner:}cls.subtract\n{indent:}),\n'
BLOCK_TPL_ADD_BOTH = '{indent:}if_(cls.is_positive)(\n{indent_inner:}cls.add_calculation,\n{indent_inner:}cls.post_add,\n{indent:}).else_(\n{indent_inner:}cls.subtract_workfunction\n{indent:}),\n'
BLOCK_TPL_MUL = '{indent:}cls.pre_iterate,\n{indent:}while_(cls.iterate)(\n{block:}{indent:}),\n'
BLOCK_TPL_POW = '{indent:}cls.raise_power,\n{indent:}cls.post_raise_power,\n'
BLOCK_TPL_END = '{indent:}cls.results'


def generate_outlines(expression):
    """
    For a given expression in Reverse Polish Notation, generate the nested symbolic structure of the outlines.

    :param expression: a valid 
    :return: a nested list structure of strings representing the structure of the outlines
    """
    stack = deque()
    values = []
    outline = [['add']]

    for i in expression.split():

        if not i in OPERATORS.keys():
            stack.appendleft(i)
            values.append(i)
        else:
            stack.popleft()

            sub_outline = outline[-1]

            if i == '+':
                sub_outline.append('add')
            elif i == '*':
                sub_outline = outline.pop()
                outline.append([sub_outline])
            elif i == '^':
                outline.append(['pow'])

    for sub_outline in outline:
        sub_outline.append('ini')
        sub_outline.append('end')

    return outline, values


def format_outlines(outlines, use_calculations=False, use_workfunctions=False):
    """
    Given the symbolic structure of the workchain outlines produced by ``generate_outlines``, format the actual
    string form of those workchain outlines

    :param outlines: the list of symbolic outline structures
    :param use_calculations: use JobCalculations for the add operations
    :param use_workfunctions: use workfunctions for the subtract operations
    :return: a list of outline strings
    """
    outline_strings = []

    for sub_outline in outlines:

        outline_string = ''

        for instruction in sub_outline:
            if instruction == 'ini':
                outline_string = BLOCK_TPL_INI.format(indent=format_indent()) + outline_string
            elif instruction == 'add':
                outline_string = format_block(instruction, 0, use_calculations, use_workfunctions) + outline_string
            elif instruction == 'pow':
                outline_string += BLOCK_TPL_POW.format(indent=format_indent())
            elif instruction == 'end':
                outline_string += BLOCK_TPL_END.format(indent=format_indent())
            else:
                outline_string += format_block(instruction, 0, use_calculations, use_workfunctions)

        outline_strings.append(outline_string)

    return outline_strings


def format_block(instruction, level=0, use_calculations=False, use_workfunctions=False):
    """
    Format the instruction into its proper string form

    :param use_calculations: use JobCalculations for the add operations
    :param use_workfunctions: use workfunctions for the subtract operations
    :return: the string representation of the instruction
    """
    block = ''
    string = ''

    if isinstance(instruction, list):
        for sub_instruction in instruction:
            if sub_instruction == 'add':
                block = format_block(sub_instruction, level + 1, use_calculations, use_workfunctions) + block
            else:
                block += format_block(sub_instruction, level + 1, use_calculations, use_workfunctions)

        string += BLOCK_TPL_MUL.format(indent=format_indent(level), level=level, block=block)

    elif instruction == 'pow':
        string += BLOCK_TPL_POW.format(indent=format_indent(level))

    elif instruction == 'add':
        if use_calculations and use_workfunctions:
            string = BLOCK_TPL_ADD_BOTH.format(indent=format_indent(level), indent_inner=format_indent(level + 1))
        elif use_calculations:
            string = BLOCK_TPL_ADD_CALC.format(indent=format_indent(level), indent_inner=format_indent(level + 1))
        elif use_workfunctions:
            string = BLOCK_TPL_ADD_WORK.format(indent=format_indent(level), indent_inner=format_indent(level + 1))
        else:
            string = BLOCK_TPL_ADD_BASE.format(indent=format_indent(level), indent_inner=format_indent(level + 1))

    return string


def format_indent(level=0, width=INDENTATION_WIDTH):
    """
    Format the indentation for the given indentation level and indentation width

    :param level: the level of indentation
    :param width: the width in spaces of a single indentation
    :return: the indentation string
    """
    return ' ' * level * width


def write_workchain(outlines, directory=None, filename=None):
    """
    Given a list of string formatted outlines, write the corresponding workchains to file
    """
    dirpath = os.path.dirname(os.path.realpath(__file__))
    template_dir = os.path.join(dirpath, 'template')
    template_file_base = os.path.join(template_dir, 'base.tpl')
    template_file_workchain = os.path.join(template_dir, 'workchain.tpl')

    if directory is None:
        directory = os.path.join(dirpath, 'polish_workchains')

    if filename is None:
        filename = os.path.join(directory, 'polish.py')
    else:
        filename = os.path.join(directory, filename)

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    try:
        init_file = os.path.join(directory, '__init__.py')
        os.utime(init_file, None)
    except OSError:
        open(init_file, 'a').close()

    with open(template_file_base, 'r') as handle:
        template_base = handle.readlines()

    with open(template_file_workchain, 'r') as handle:
        template_workchain = Template(handle.read())

    with open(filename, 'w') as handle:

        for line in template_base:
            handle.write(line)
        handle.write('\n\n')

        counter = len(outlines) - 1
        for outline in outlines:

            outline_string = ''
            for subline in outline.split('\n'):
                outline_string += '\t\t\t{}\n'.format(subline)

            if counter == len(outlines) - 1:
                child_class = None
            else:
                child_class = 'Polish{:02d}WorkChain'.format(counter + 1)

            subs = {
                'class_name': 'Polish{:02d}WorkChain'.format(counter),
                'child_class': child_class,
                'outline': outline_string,
            }
            handle.write(template_workchain.substitute(**subs))
            handle.write('\n\n')

            counter -= 1

    return filename
