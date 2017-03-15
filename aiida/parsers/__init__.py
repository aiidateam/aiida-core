# -*- coding: utf-8 -*-
from aiida.parsers.parser import Parser



def ParserFactory(module):
    """
    Return a suitable Parser subclass.
    """
    from aiida.common.pluginloader import BaseFactory

    return BaseFactory(module, Parser, "aiida.parsers.plugins")