# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



def DbImporterFactory(pluginname):
    """
    This function loads the correct DbImporter plugin class
    """
    from aiida.common.pluginloader import BaseFactory
    from aiida.tools.dbimporters.baseclasses import DbImporter

    return BaseFactory(pluginname, DbImporter, "aiida.tools.dbimporters.plugins")

    raise NotImplementedError
