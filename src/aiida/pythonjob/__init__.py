"""AiiDA plugin that run Python function on remote computers."""

__version__ = "0.5.2"

from aiida.node_graph import socket_spec as spec

from .calculations import MonitorPyFunction, PyFunction, PythonJob
from .decorator import pyfunction
from .launch import prepare_monitor_function_inputs, prepare_pyfunction_inputs, prepare_pythonjob_inputs
from .parsers import PythonJobParser

__all__ = (
    "MonitorPyFunction",
    "PyFunction",
    "PythonJob",
    "PythonJobParser",
    "prepare_monitor_function_inputs",
    "prepare_pyfunction_inputs",
    "prepare_pythonjob_inputs",
    "pyfunction",
    "spec",
)
