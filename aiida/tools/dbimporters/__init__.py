# -*- coding: utf-8 -*-

def DBImporterFactory(pluginname):
    """
    This function loads the correct DBImporter plugin class
    """
    from aiida.common.pluginloader import BaseFactory
    from aiida.tools.dbimporters.baseclasses import DBImporter
    
    return BaseFactory(pluginname, DBImporter, "aiida.tools.dbimporters.plugins")

    raise NotImplementedError

