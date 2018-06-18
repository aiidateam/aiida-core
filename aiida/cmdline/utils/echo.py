# -*- coding: utf-8 -*-
""" Convenience functions for printing output from verdi commands """
import enum
import sys
import click


#pylint: disable=too-few-public-methods
class ExitCode(enum.Enum):
    """Exit codes for the verdi command line."""
    CRITICAL = 1
    DEPRECATED = 80
    UNKNOWN = 99


#pylint: disable=invalid-name
def echo(message, bold=False, nl=True):
    """
    Print a normal message through click's echo function to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    """
    click.secho(message, bold=bold, nl=nl)


def echo_info(message, bold=False, nl=True):
    """
    Print an info message through click's echo function to stdout, prefixed with 'Info:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    """
    click.secho('Info: ', fg='blue', bold=True, nl=False)
    click.secho(message, bold=bold, nl=nl)


def echo_success(message, bold=False, nl=True):
    """
    Print a success message through click's echo function to stdout, prefixed with 'Success:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
        include a newline character
    :param nl: whether to print a newline at the end of the message
    """
    click.secho('Success: ', fg='green', bold=True, nl=False)
    click.secho(message, bold=bold, nl=nl)


def echo_warning(message, bold=False, nl=True):
    """
    Print a warning message through click's echo function to stdout, prefixed with 'Warning:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    """
    click.secho('Warning: ', fg='yellow', bold=True, nl=False)
    click.secho(message, bold=bold, nl=nl)


def echo_error(message, bold=False, nl=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Error:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    """
    click.secho('Error: ', fg='red', bold=True, nl=False, err=True)
    click.secho(message, bold=bold, nl=nl, err=True)


def echo_critical(message, bold=False, nl=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Critical:'
    and then calls sys.exit with the given exit_status.

    This should be used to print messages for errors that cannot be recovered
    from and so the script should be directly terminated with a non-zero exit
    status to indicate that the command failed

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    """
    click.secho('Critical: ', fg='red', bold=True, nl=False, err=True)
    click.secho(message, bold=bold, nl=nl, err=True)
    sys.exit(ExitCode.CRITICAL.value)


#pylint: disable=redefined-builtin
def echo_deprecated(message, bold=False, nl=True, exit=False):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Deprecated:'
    and then calls sys.exit with the given exit_status.

    This should be used to indicate deprecated commands.

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param exit: whether to exit after printing the message
    """
    click.secho('Deprecated: ', fg='red', bold=True, nl=False, err=True)
    click.secho(message, bold=bold, nl=nl, err=True)

    if exit:
        sys.exit(ExitCode.DEPRECATED.value)
