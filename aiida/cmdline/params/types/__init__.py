# -*- coding: utf-8 -*-
"""Provides all parameter types."""
from .choice import LazyChoice
from .calculation import CalculationParamType
from .code import CodeParamType
from .computer import ComputerParamType
from .data import DataParamType
from .group import GroupParamType
from .identifier import IdentifierParamType
from .node import NodeParamType
from .multiple import MultipleValueParamType
from .nonemptystring import NonemptyStringParamType
from .shebang import ShebangParamType
from .plugin import PluginParamType
from .legacy_workflow import LegacyWorkflowParamType

__all__ = [
    'LazyChoice', 'IdentifierParamType', 'CalculationParamType', 'CodeParamType', 'ComputerParamType', 'DataParamType',
    'GroupParamType', 'NodeParamType', 'MultipleValueParamType', 'NonemptyStringParamType', 'PluginParamType',
    'ShebangParamType', 'LegacyWorkflowParamType'
]
