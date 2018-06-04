# -*- coding: utf-8 -*-
import sys
import click


def echo(message, bold=False, prefix=None, nl=True):
    """
    Print a normal message through click's echo function to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param prefix: an optional string that will be printed before the message
    :param nl: whether to print a newline at the end of the message
    """
    if prefix is not None:
        click.secho(prefix)

    click.secho(message, bold=bold, nl=nl)


def echo_info(message, bold=False, prefix=None, nl=True):
    """
    Print an info message through click's echo function to stdout, prefixed with 'Info:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param prefix: an optional string that will be printed before the message. Note that it does not automatically
        include a newline character
    :param nl: whether to print a newline at the end of the message
    """
    if prefix is not None:
        click.secho(prefix, nl=False)

    click.secho('Info: ', fg='blue', bold=True, nl=False)
    click.secho(message, bold=bold, nl=nl)


def echo_success(message, bold=False, prefix=None, nl=True):
    """
    Print a success message through click's echo function to stdout, prefixed with 'Success:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param prefix: an optional string that will be printed before the message. Note that it does not automatically
        include a newline character
    :param nl: whether to print a newline at the end of the message
    """
    if prefix is not None:
        click.secho(prefix, nl=False)

    click.secho('Success: ', fg='green', bold=True, nl=False)
    click.secho(message, bold=bold, nl=nl)


def echo_warning(message, bold=False, prefix=None, nl=True):
    """
    Print a warning message through click's echo function to stdout, prefixed with 'Warning:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param prefix: an optional string that will be printed before the message. Note that it does not automatically
        include a newline character
    :param nl: whether to print a newline at the end of the message
    """
    if prefix is not None:
        click.secho(prefix, nl=False)

    click.secho('Warning: ', fg='yellow', bold=True, nl=False)
    click.secho(message, bold=bold, nl=nl)


def echo_error(message, bold=False, prefix=None, nl=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Error:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param prefix: an optional string that will be printed before the message. Note that it does not automatically
        include a newline character
    :param nl: whether to print a newline at the end of the message
    """
    if prefix is not None:
        click.secho(prefix, nl=False)

    click.secho('Error: ', fg='red', bold=True, nl=False, err=True)
    click.secho(message, bold=bold, nl=nl, err=True)


def echo_critical(message, bold=False, prefix=None, nl=True, exit_status=1):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Critical:'
    and then calls sys.exit with the give exit_status. This should be used to print messages for errors
    that cannot be recovered from and so the script should be directly terminated with a non-zero exit
    status to indicate that the command failed

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param prefix: an optional string that will be printed before the message. Note that it does not automatically
        include a newline character
    :param nl: whether to print a newline at the end of the message
    :param exit_status: the integer to pass to the sys.exit() call
    """
    if prefix is not None:
        click.secho(prefix, nl=False)

    click.secho('Critical: ', fg='red', bold=True, nl=False, err=True)
    click.secho(message, bold=bold, nl=nl, err=True)
    sys.exit(exit_status)
