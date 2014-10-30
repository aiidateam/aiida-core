# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

def DbImporterFactory(pluginname):
    """
    This function loads the correct DbImporter plugin class
    """
    from aiida.common.pluginloader import BaseFactory
    from aiida.tools.dbimporters.baseclasses import DbImporter
    
    return BaseFactory(pluginname, DbImporter, "aiida.tools.dbimporters.plugins")

    raise NotImplementedError

