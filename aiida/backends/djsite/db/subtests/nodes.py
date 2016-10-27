# -*- coding: utf-8 -*-
"""
Tests for nodes, attributes and links
"""


from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.nodes import (
    TestDataNode, TestTransitiveNoLoops, TestTransitiveClosureDeletion,
    TestQueryWithAiidaObjects, TestNodeBasic, TestSubNodesAndLinks)

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestDataNodeDjango(AiidaTestCase, TestDataNode):
    """
    These tests check the features of Data nodes that differ from the base Node
    """
    pass


class TestTransitiveNoLoopsDjango(AiidaTestCase, TestTransitiveNoLoops):
    """
    Test the creation of the transitive closure table
    """
    pass


class TestTransitiveClosureDeletion(AiidaTestCase, TestTransitiveClosureDeletion):
    pass


class TestQueryWithAiidaObjectsDjango(AiidaTestCase, TestQueryWithAiidaObjects):
    pass


class TestNodeBasicDango(AiidaTestCase, TestNodeBasic):
    pass


class TestSubNodesAndLinksDjango(AiidaTestCase, TestSubNodesAndLinks):
    pass