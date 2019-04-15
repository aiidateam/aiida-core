# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


def DbImporterFactory(pluginname):
    """
    This function loads the correct DbImporter plugin class
    """
    from aiida.common.pluginloader import BaseFactory
    from aiida.tools.dbimporters.baseclasses import DbImporter

    return BaseFactory(pluginname, DbImporter, "aiida.tools.dbimporters.plugins")

    raise NotImplementedError

