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
    from aiida.restapi.common.config import API_CONFIG, CLI_DEFAULTS

    return f"http://{CLI_DEFAULTS['HOST_NAME']}:{CLI_DEFAULTS['PORT']}{API_CONFIG['PREFIX']}"


@pytest.fixture
def restrict_db_connections():  # pylint: disable=unused-argument
    """Restrict the number of database connections allowed to the PSQL database."""
    from aiida.manage import get_manager

    manager = get_manager()

    # create a new profile with the engine key-word arguments
    # pool_timeout: number of seconds to wait before giving up on getting a connection from the pool.
    # max_overflow: maximum number of connections that can be opened above the pool_size (whose default is 5)
    current_profile = manager.get_profile()
    new_profile = current_profile.copy()
    new_profile.set_storage(
        new_profile.storage_backend, {
            'engine_kwargs': {
                'pool_timeout': 1,
                'max_overflow': 0
            },
            **new_profile.storage_config
        }
    )
    # load the new profile and initialise the database connection
    manager.unload_profile()
    manager.load_profile(new_profile)
    backend = manager.get_profile_storage()
    # double check that the connection is set with these parameters
    session = backend.get_session()
    assert session.bind.pool.timeout() == 1
    assert session.bind.pool._max_overflow == 0  # pylint: disable=protected-access
    yield
    # reset the original profile
    manager.unload_profile()
    manager.load_profile(current_profile)


@pytest.fixture
def populate_restapi_database():
    """Populates the database with a considerable set of nodes to test the restAPI"""
    # pylint: disable=unused-argument
    from aiida import orm

    struct_forcif = orm.StructureData(pbc=False).store()
    orm.StructureData(pbc=False).store()
    orm.StructureData(pbc=False).store()

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
