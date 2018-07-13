# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click


def echo_info(message, bold=False):
    """
    Print an info message through click's echo function to stdout, prefixed with 'Info:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    """
    click.secho('Info: ', fg='blue', bold=True, nl=False)
    click.secho(message, bold=bold)


def echo_warning(message, bold=False):
    """
    Print a warning message through click's echo function to stdout, prefixed with 'Warning:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    """
    click.secho('Warning: ', fg='yellow', bold=True, nl=False)
    click.secho(message, bold=bold)


def echo_error(message, bold=False):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Error:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    """
    click.secho('Error: ', fg='red', bold=True, nl=False)
    click.secho(message, bold=bold)