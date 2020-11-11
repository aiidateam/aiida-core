# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""pytest fixtures for use with the aiida.restapi tests"""
import pytest


@pytest.fixture(scope='function')
def restapi_server():
    """Make REST API server"""
    from werkzeug.serving import make_server

    from aiida.restapi.common.config import CLI_DEFAULTS
    from aiida.restapi.run_api import configure_api

    def _restapi_server(restapi=None):
        if restapi is None:
            flask_restapi = configure_api()
        else:
            flask_restapi = configure_api(flask_api=restapi)

        return make_server(
            host=CLI_DEFAULTS['HOST_NAME'],
            port=int(CLI_DEFAULTS['PORT']),
            app=flask_restapi.app,
            threaded=True,
            processes=1,
            request_handler=None,
            passthrough_errors=True,
            ssl_context=None,
            fd=None
        )

    return _restapi_server


@pytest.fixture
def server_url():
    from aiida.restapi.common.config import CLI_DEFAULTS, API_CONFIG

    return f"http://{CLI_DEFAULTS['HOST_NAME']}:{CLI_DEFAULTS['PORT']}{API_CONFIG['PREFIX']}"


@pytest.fixture
def restrict_sqlalchemy_queuepool(aiida_profile):
    """Create special SQLAlchemy engine for use with QueryBuilder - backend-agnostic"""
    from aiida.manage.manager import get_manager

    backend_manager = get_manager().get_backend_manager()
    backend_manager.reset_backend_environment()
    backend_manager.load_backend_environment(aiida_profile, pool_timeout=1, max_overflow=0)


@pytest.fixture
def populate_restapi_database(clear_database_before_test):
    """Populates the database with a considerable set of nodes to test the restAPI"""
    # pylint: disable=unused-argument
    from aiida import orm

    struct_forcif = orm.StructureData().store()
    orm.StructureData().store()
    orm.StructureData().store()

    orm.Dict().store()
    orm.Dict().store()

    orm.CifData(ase=struct_forcif.get_ase()).store()

    orm.KpointsData().store()

    orm.FolderData().store()

    orm.CalcFunctionNode().store()
    orm.CalcJobNode().store()
    orm.CalcJobNode().store()

    orm.WorkFunctionNode().store()
    orm.WorkFunctionNode().store()
    orm.WorkChainNode().store()
