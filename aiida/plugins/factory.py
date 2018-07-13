# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.plugins.entry_point import load_entry_point


def BaseFactory(group, name):
    """
    Return the plugin class registered under a given entry point group and name

    :param group: entry point group
    :param name: entry point name
    :return: the plugin class
    """
    return load_entry_point(group, name)
