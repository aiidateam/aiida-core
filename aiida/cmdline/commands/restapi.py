# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to hook-up the AiIDA built-in RESTful API.
Main advantage of doing this by means of a verdi command is that different
profiles can be selected at hook-up (-p flag).

"""

from aiida.cmdline.baseclass import VerdiCommand

class Restapi(VerdiCommand):
    """
    verdi command used to hook up the AiIDA REST API.
    Example Usage:

    verdi -p <profile_name> restapi --host 127.0.0.5 --port 6789
    --config-dir <location of the onfig.py file>

    """
    import os
    import aiida.restapi

    # Defaults defined at class level
    default_host = "127.0.0.1"
    default_port = "5000"
    default_config_dir = os.path.join(os.path.split(os.path.abspath(
        aiida.restapi.__file__))[0], 'common')
    parse_aiida_profile = False

    def run(self, *args):
        """
        Hook up the default RESTful API of AiiDA.
        args include port, host, config_file
        """
        from aiida.restapi.api import App, AiidaApi
        from aiida.restapi.run_api import run_api

        # Construct dparameter dictionary
        kwargs = dict(
            hookup=True,
            prog_name=self.get_full_command_name(),
            default_host=self.default_host,
            default_port=self.default_port,
            default_config=self.default_config_dir,
            parse_aiida_profile=self.parse_aiida_profile)

        # Invoke the runner
        run_api(App, AiidaApi, *args, **kwargs)

    def complete(self, subargs_idx, subargs):
        """
        No particular completion features required
        """
        return ""
