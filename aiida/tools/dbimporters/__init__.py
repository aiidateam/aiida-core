# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"

def DbImporterFactory(pluginname):
    """
    This function loads the correct DbImporter plugin class
    """
    from aiida.common.pluginloader import BaseFactory
    from aiida.tools.dbimporters.baseclasses import DbImporter
    
    return BaseFactory(pluginname, DbImporter, "aiida.tools.dbimporters.plugins")

    raise NotImplementedError

