# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import operator as operators
import random
from collections import deque


OPERATORS = {
    '+': operators.add,
    '*': operators.mul,
    '^': operators.pow,
}


def generate(min_operator_count=3, max_operator_count=5, min_operand_value=-5, max_operand_value=5):
    """
    Generate a random valid expression in Reverse Polish Notation. There are a few limitations:

        * Only integers are supported
        * Only the addition, multiplication and power operators (+, * and ^, respectively) are supported
        * Every intermediate result should be an integer, so no raising a number to a negative power
        * Operands for power operator are limited to the range [1, 3]
        * Expression has only a single sequence of numbers followed by single continuous sequence of operators

    :param min_operator_count: the minimum number of operators the expression should have
    :param max_operator_count: the maximum number of operators the expression should have
    :param min_operand_value: the minimum value of all the operands
    :param max_operand_value: the minimum value of all the operands
    :return: a string representing an expression in Reverse Polish Notation
    """
    operator_count = random.randint(min_operator_count, max_operator_count)
    operand_range = list(range(min_operand_value, max_operand_value + 1))
    operand_range.remove(0)
    operand_range_pow = [1, 3]

    # We start with the initial operand
    symbols = [str(random.choice(operand_range))]

    for i in range(operator_count):
        operator = random.choice(OPERATORS.keys())

        if OPERATORS[operator] == operators.pow:
            operand = random.choice(operand_range_pow)
        else:
            operand = random.choice(operand_range)

        symbols.append(operator)
        symbols.insert(0, str(operand))

    return ' '.join(symbols)


def validate(expression):
    """
    Validate an expression in Reverse Polish Notation. In addition to normal rules, the following restrictions apply:

        * Only integers are supported
        * Only the addition, multiplication and power operators (+, * and ^, respectively) are supported
        * Every intermediate result should be an integer, so no raising a number to a negative power
        * Expression has only a single sequence of numbers followed by single continuous sequence of operators

    :param expression: the expression in Reverse Polish Notation
    :return: tuple(Bool, list) indicating whether expression is valid and if not a list of error messages
    """
    try:
        symbols = expression.split()
    except Exception as exception:
        return False, 'failed to split the expression into symbols: {}'.format(exception)

    while len(symbols) > 1:
        try:
            operand = symbols.pop(0)
            operator = symbols.pop()
        except IndexError:
            return False, 'expression contains incongruent number of symbols'

        try:
            operand = int(operand)
        except ValueError:
            return False, 'the operand {} is not a valid integer'.format(operand)

        if operator not in OPERATORS.keys():
            return False, 'the operator {} is not supported'.format(operator)

        if OPERATORS[operator] == operators.pow and operand < 0:
            return False, 'a negative operand {} was found for the ^ operator, which is not allowed'.format(operand)

    # At this point the symbols list should only contain the initial operand
    try:
        operand = int(symbols.pop())
    except ValueError:
        return False, 'the operand {} is not a valid integer'.format(operand)

    if symbols:
        return False, 'incorrect number of symbols found, should contain N operands followed by (N - 1) operators'

    return True, None


def evaluate(expression, modulo=None):
    """
    Evaluate an expression in Reverse Polish Notation. There are a few limitations:

        * Only integers are supported
        * Only the addition, multiplication and power operators (+, * and ^, respectively) are supported

    :param expression: the expression in Reverse Polish Notation
    :return: the result of the evaluted expression 
    """
    stack = deque()
    result = 0

    for i in expression.split():
        if not i in OPERATORS.keys():
            stack.appendleft(i)
        else:
            op = OPERATORS[i]

            x = int(stack.popleft())
            y = int(stack.popleft())
            result = op(x, y)
            stack.appendleft(unicode(result))

    if modulo is not None:
        return int(result % modulo)
    else:
        return int(result)
