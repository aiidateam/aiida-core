# -*- coding: utf-8 -*-



def DbImporterFactory(pluginname):
    """
    This function loads the correct DbImporter plugin class
    """
    from aiida.common.pluginloader import BaseFactory
    from aiida.tools.dbimporters.baseclasses import DbImporter

    return BaseFactory(pluginname, DbImporter, "aiida.tools.dbimporters.plugins")

    raise NotImplementedError

