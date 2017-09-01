import sys
import os
from aiida.restapi.api import App, AiidaApi
from aiida.restapi.run_api import run_api

AIIDA_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    os.pardir, os.pardir, os.pardir, 'aiida/')

sys.path = [AIIDA_DIR] + sys.path

config_file_path = os.path.dirname(os.path.abspath(__file__))

(application, api) = run_api(App, AiidaApi,
                             '--config-dir', config_file_path,
                             hookup=False,
                             catch_internal_server=False)