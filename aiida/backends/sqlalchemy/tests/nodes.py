# -*- coding: utf-8 -*-
"""
Tests for nodes, attributes and links
"""

from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.nodes import (
    TestDataNode, TestTransitiveNoLoops, TestTransitiveClosureDeletion,
    TestQueryWithAiidaObjects, TestNodeBasic, TestSubNodesAndLinks)

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestDataNodeSQLA(SqlAlchemyTests, TestDataNode):
    """
    These tests check the features of Data nodes that differ from the base Node
    """
    pass


class TestTransitiveNoLoopsSQLA(SqlAlchemyTests, TestTransitiveNoLoops):
    """
    Test the creation of the transitive closure table
    """
    pass


class TestTransitiveClosureDeletionSQLA(SqlAlchemyTests, TestTransitiveClosureDeletion):
    pass


class TestQueryWithAiidaObjectsSQLA(SqlAlchemyTests, TestQueryWithAiidaObjects):
    pass


class TestNodeBasicSQLA(SqlAlchemyTests, TestNodeBasic):
    pass


class TestSubNodesAndLinksSQLA(SqlAlchemyTests, TestSubNodesAndLinks):
    pass