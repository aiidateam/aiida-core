"""Utilities for logging in the command line interface context."""

import logging
import sys

import click

from .echo import COLORS


class CliHandler(logging.Handler):
    """Handler for writing to the console using click."""

    # Capture `sys` as a default since module globals may be cleared during interpreter shutdown.
    # See https://stackoverflow.com/questions/67902926/python-importerror-in-del-how-to-solve-this
    def emit(self, record, _sys=sys):
        """Emit log record via click.

        Can make use of special attributes 'nl' (whether to add newline) and 'err' (whether to print to stderr), which
        can be set via the 'extra' dictionary parameter of the logging methods.
        """
        try:
            nl = record.nl
        except AttributeError:
            nl = True

        try:
            err = record.err
        except AttributeError:
            err = False

        try:
            prefix = record.prefix
        except AttributeError:
            prefix = True

        record.prefix = prefix

        try:
            msg = self.format(record)
            click.echo(msg, err=err, nl=nl)
        except Exception:
            if _sys.is_finalizing():
                try:
                    msg = record.getMessage()
                    if prefix:
                        msg = f'{record.levelname.capitalize()}: {msg}'
                    stream = _sys.__stderr__ if err else _sys.__stdout__
                    if stream is not None:
                        stream.write(f'{msg}\n' if nl else msg)
                        stream.flush()
                except Exception:
                    pass
                return

            self.handleError(record)


class CliFormatter(logging.Formatter):
    """Formatter that automatically prefixes log messages with a colored version of the log level."""

    def format(self, record):
        """Format the record using the style required for the command line interface."""
        try:
            fg = COLORS[record.levelname.lower()]
        except (KeyError, TypeError):
            fg = 'white'

        try:
            prefix = record.prefix
        except AttributeError:
            prefix = None

        formatted = super().format(record)

        if prefix:
            try:
                prefix = click.style(record.levelname.capitalize(), fg=fg, bold=True)
            except Exception:
                prefix = record.levelname.capitalize()
            return f'{prefix}: {formatted}'

        return formatted
