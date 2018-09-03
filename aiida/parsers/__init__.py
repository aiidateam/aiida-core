# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.parsers.parser import Parser
from aiida.plugins.factory import BaseFactory


def ParserFactory(entry_point):
    """
    Return the Parser plugin class for a given entry point

    :param entry_point: the entry point name of the Parser plugin
    """
    return BaseFactory('aiida.parsers', entry_point)
