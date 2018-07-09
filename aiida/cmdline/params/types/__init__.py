# -*- coding: utf-8 -*-
"""Provides all parameter types."""

from .choice import LazyChoice
from .calculation import CalculationParamType
from .code import CodeParamType
from .computer import ComputerParamType, ShebangParamType, MpirunCommandParamType
from .data import DataParamType
from .group import GroupParamType
from .identifier import IdentifierParamType
from .node import NodeParamType
from .multiple import MultipleValueParamType
from .nonemptystring import NonemptyStringParamType
from .path import AbsolutePathParamType
from .user import UserParamType
from .plugin import PluginParamType

from .legacy_workflow import LegacyWorkflowParamType

__all__ = [
    'LazyChoice', 'IdentifierParamType', 'CalculationParamType', 'CodeParamType', 'ComputerParamType', 'DataParamType',
    'GroupParamType', 'NodeParamType', 'MpirunCommandParamType', 'MultipleValueParamType', 'NonemptyStringParamType',
    'PluginParamType', 'AbsolutePathParamType', 'ShebangParamType', 'LegacyWorkflowParamType', 'UserParamType'
]
