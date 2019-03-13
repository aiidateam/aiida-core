# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for the backup functionality."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import datetime
import sys

import dateutil

from six.moves import input


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

    while True:
        answer = query_string(question, "")

        # If the reply is empty
        if not answer:
            if not allow_none_as_answer:
                continue
        # Otherwise, try to parse it
        else:
            try:
                if reply_type == int:
                    final_answer = int(answer)
                elif reply_type == float:
                    final_answer = float(answer)
                elif reply_type == datetime.datetime:
                    final_answer = dateutil.parser.parse(answer)
                else:
                    raise ValueError
            # If it is not parsable...
            except ValueError:
                sys.stdout.write("The given value could not be parsed. Type expected: {}\n".format(reply_type))
                # If the timestamp could not have been parsed,
                # ask again the same question.
                continue

        if query_yes_no("{} was parsed. Is it correct?".format(final_answer), default="yes"):
            break
    return final_answer


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning
    an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = input(question + prompt).lower()
        if default is not None and not choice:
            return valid[default]

        if choice in valid:
            return valid[choice]

        sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def query_string(question, default):
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

    if default is None or not default:
        prompt = ""
    else:
        prompt = " [{}]".format(default)

    while True:
        reply = input(question + prompt)
        if default is not None and not reply:
            # If the default answer is an empty string.
            if not default:
                return None

            return default

        if reply:
            return reply

        sys.stdout.write("Please provide a non empty answer.\n")
