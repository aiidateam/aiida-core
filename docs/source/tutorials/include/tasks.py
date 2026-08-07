"""Shared calcfunctions for the tutorial pipeline.

``prepare_input`` and ``parse_output`` are plain AiiDA calcfunctions (also
shown inline in module 2): the first turns a parameter dict into a ``gsrd``
input file, the second recovers the headline diagnostics from a ``gsrd`` run's
stdout. They are reused across modules 2-6.

Module-specific tasks live alongside this file: ``tasks_module_3b.py`` (the
sweep reduction plot) and ``tasks_module_6.py`` (the adaptive-workflow tasks).
"""

from typing import TypedDict

import yaml
from include.constants import MEAN_RE, VARIANCE_RE

from aiida import engine, orm


class ParseOutputs(TypedDict):
    """Named outputs produced by :func:`parse_output`."""

    variance_V: float
    mean_V: float


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.value)
    return orm.SinglefileData.from_string(content, filename='input.yaml')


@engine.calcfunction
def parse_output(stdout: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V scalars from the ``gsrd`` stdout log.

    :param stdout: captured stdout of a ``gsrd`` run (as produced by
        ``aiida-shell``). ``gsrd`` prints the headline diagnostics only to
        stdout, so we recover them with a simple regex.
    """
    text = stdout.get_content(mode='r')
    variance_match = VARIANCE_RE.search(text)
    mean_match = MEAN_RE.search(text)
    if variance_match is None or mean_match is None:
        msg = "gsrd stdout did not contain 'Variance of V field' / 'Mean of V field' diagnostics"
        raise ValueError(msg)
    return {
        'variance_V': orm.Float(float(variance_match.group(1))),
        'mean_V': orm.Float(float(mean_match.group(1))),
    }
