# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-builtin
"""Utilities for the backup functionality."""

import datetime
import sys

import dateutil
import click


def ask_question(question, reply_type, allow_none_as_answer=True):
    """
    This method asks a specific question, tries to parse the given reply
    and then it verifies the parsed answer.
    :param question: The question to be asked.
    :param reply_type: The type of the expected answer (int, datetime etc). It
    is needed for the parsing of the answer.
    :param allow_none_as_answer: Allow empty answers?
    :return: The parsed reply.
    """
    final_answer = None

    if allow_none_as_answer:
        default = 'No Answer'
    else:
        default = None

    if reply_type == datetime.datetime:
        while final_answer is None:
            try:
                final_answer = click.prompt(
                    question, default=default, value_proc=dateutil.parser.parse, confirmation_prompt=True
                )
            except ValueError:
                sys.stdout.write(f'The given value could not be parsed. pType expected: {reply_type}\n')
                continue

    else:
        final_answer = click.prompt(question, default=default, type=reply_type, confirmation_prompt=True)

    if final_answer == 'No Answer':
        return None
    return final_answer


def query_yes_no(question, default='yes') -> bool:
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning
    an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    if default:
        answer = click.confirm(question, default=default)
    else:
        answer = click.prompt(question, type=bool, prompt_suffix=' [y/n]:')

    return answer


def query_string(question, default) -> str:
    """
    Asks a question (with the option to have a default, predefined answer,
    and depending on the default answer and the answer of the user the
    following options are available:
    - If the user replies (with a non empty answer), then his answer is
    returned.
    - If the default answer is None then the user has to reply with a non-empty
    answer.
    - If the default answer is not None, then it is returned if the user gives
    an empty answer. In the case of empty default answer and empty reply from
    the user, None is returned.
    :param question: The question that we want to ask the user.
    :param default: The default answer (if there is any) to the question asked.
    :return: The returned reply.
    """

    reply = click.prompt(text=question, default=default)

    return reply
