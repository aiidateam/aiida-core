# -*- coding: utf-8 -*-
"""
This allows to hook-up the AiIDA built-in RESTful API.
Main advantage of doing this by means of a verdi command is that different profiles can be selected at hook-up (-p flag).

"""

from aiida.restapi.api import app, hookup
from aiida.cmdline.baseclass import VerdiCommand

class Restapi(VerdiCommand):
    """
    Hook up the default RESTful API of AiiDA.
    No special logic required
    """

    def run(self, *args):
        hookup(app)

    def complete(self, subargs_idx, subargs):
        """
        No particular completion features required
        """
        return ""
