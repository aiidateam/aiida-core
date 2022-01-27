# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions to dynamically generate a WorkChain from a reversed polish notation expression."""

import collections
import hashlib
import os
from pathlib import Path
from string import Template

from .expression import OPERATORS  # pylint: disable=relative-beyond-top-level

INDENTATION_WIDTH = 4

BLOCK_TPL_INI = '{indent:}cls.setup,\n'
BLOCK_TPL_ADD_BASE = """
    {indent:}if_(cls.is_positive)(
    {indent_inner:}cls.add
    {indent:}).else_(
    {indent_inner:}cls.subtract
    {indent:}),
    """

BLOCK_TPL_ADD_WORK = """
    {indent:}if_(cls.is_positive)(
    {indent_inner:}cls.add
    {indent:}).else_(
    {indent_inner:}cls.subtract_calcfunction
    {indent:}),
    """

BLOCK_TPL_ADD_CALC = """
    {indent:}if_(cls.is_positive)(
    {indent_inner:}cls.add_calculation,
    {indent_inner:}cls.post_add,
    {indent:}).else_(
    {indent_inner:}cls.subtract
    {indent:}),
    """

BLOCK_TPL_ADD_BOTH = """
    {indent:}if_(cls.is_positive)(
    {indent_inner:}cls.add_calculation,
    {indent_inner:}cls.post_add,
    {indent:}).else_(
    {indent_inner:}cls.subtract_calcfunction
    {indent:}),
    """

BLOCK_TPL_MUL = """
    {indent:}cls.pre_iterate,
    {indent:}while_(cls.iterate)(
    {block:}{indent:}),
    """

BLOCK_TPL_POW = """
    {indent:}cls.raise_power,
    {indent:}cls.post_raise_power,
    """

BLOCK_TPL_END = """
    {indent:}cls.results
    """


def generate_outlines(expression):
    """
    For a given expression in Reverse Polish Notation, generate the nested symbolic structure of the outlines.

    :param expression: a valid expression
    :return: a nested list structure of strings representing the structure of the outlines
    """
    stack = collections.deque()
    values = []
    outline = [['add']]

    for part in expression.split():

        if part not in OPERATORS.keys():
            stack.appendleft(part)
            values.append(part)
        else:
            stack.popleft()

            sub_outline = outline[-1]

            if part == '+':
                sub_outline.append('add')
            elif part == '*':
                sub_outline = outline.pop()
                outline.append([sub_outline])
            elif part == '^':
                outline.append(['pow'])

    for sub_outline in outline:
        sub_outline.append('ini')
        sub_outline.append('end')

    return outline, values


def format_outlines(outlines, use_calculations=False, use_calcfunctions=False):
    """
    Given the symbolic structure of the workchain outlines produced by ``generate_outlines``, format the actual
    string form of those workchain outlines

    :param outlines: the list of symbolic outline structures
    :param use_calculations: use CalcJobs for the add operations
    :param use_calcfunctions: use calcfunctions for the subtract operations
    :return: a list of outline strings
    """
    outline_strings = []

    for sub_outline in outlines:

        outline_string = ''

        for instruction in sub_outline:
            if instruction == 'ini':
                outline_string = BLOCK_TPL_INI.format(indent=format_indent()) + outline_string
            elif instruction == 'add':
                outline_string = format_block(instruction, 0, use_calculations, use_calcfunctions) + outline_string
            elif instruction == 'pow':
                outline_string += BLOCK_TPL_POW.format(indent=format_indent())
            elif instruction == 'end':
                outline_string += BLOCK_TPL_END.format(indent=format_indent())
            else:
                outline_string += format_block(instruction, 0, use_calculations, use_calcfunctions)

        outline_strings.append(outline_string)

    return outline_strings


def format_block(instruction, level=0, use_calculations=False, use_calcfunctions=False):
    """
    Format the instruction into its proper string form

    :param use_calculations: use CalcJobs for the add operations
    :param use_calcfunctions: use calcfunctions for the subtract operations
    :return: the string representation of the instruction
    """
    block = ''
    string = ''

    if isinstance(instruction, list):
        for sub_instruction in instruction:
            if sub_instruction == 'add':
                block = format_block(sub_instruction, level + 1, use_calculations, use_calcfunctions) + block
            else:
                block += format_block(sub_instruction, level + 1, use_calculations, use_calcfunctions)

        string += BLOCK_TPL_MUL.format(indent=format_indent(level), level=level, block=block)

    elif instruction == 'pow':
        string += BLOCK_TPL_POW.format(indent=format_indent(level))

    elif instruction == 'add':
        if use_calculations and use_calcfunctions:
            string = BLOCK_TPL_ADD_BOTH.format(indent=format_indent(level), indent_inner=format_indent(level + 1))
        elif use_calculations:
            string = BLOCK_TPL_ADD_CALC.format(indent=format_indent(level), indent_inner=format_indent(level + 1))
        elif use_calcfunctions:
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


def write_workchain(outlines, directory=None) -> Path:
    """
    Given a list of string formatted outlines, write the corresponding workchains to file

    :returns: file path
    """
    dirpath = os.path.dirname(os.path.realpath(__file__))
    template_dir = os.path.join(dirpath, 'template')
    template_file_base = os.path.join(template_dir, 'base.tpl')
    template_file_workchain = os.path.join(template_dir, 'workchain.tpl')

    if directory is None:
        directory = os.path.join(dirpath, os.path.pardir, 'polish_workchains')

    directory = Path(directory)

    directory.mkdir(parents=True, exist_ok=True)
    (directory / '__init__.py').touch()

    with open(template_file_base, 'r', encoding='utf8') as handle:
        template_base = handle.readlines()

    with open(template_file_workchain, 'r', encoding='utf8') as handle:
        template_workchain = Template(handle.read())

    code_strings = []

    for line in template_base:
        code_strings.append(line)
    code_strings.append('\n')

    counter = len(outlines) - 1
    for outline in outlines:

        outline_string = ''
        for subline in outline.split('\n'):
            outline_string += f'\t\t\t{subline}\n'

        if counter == len(outlines) - 1:
            child_class = None
        else:
            child_class = f'Polish{counter + 1:02d}WorkChain'

        subs = {
            'class_name': f'Polish{counter:02d}WorkChain',
            'child_class': child_class,
            'outline': outline_string,
        }
        code_strings.append(template_workchain.substitute(**subs))
        code_strings.append('\n\n')

        counter -= 1

    code_string = '\n'.join(code_strings)
    hashed = hashlib.md5(code_string.encode('utf8')).hexdigest()

    filepath = directory / f'polish_{hashed}.py'

    filepath.write_text(code_string)

    return filepath
