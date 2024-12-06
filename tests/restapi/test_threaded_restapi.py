###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `aiida.restapi` module, using it in threaded mode.

Threaded mode is the default (and only) way to run the AiiDA REST API (see `aiida.restapi.run_api:run_api()`).
This test file's layout is inspired by https://gist.github.com/prschmid/4643738
"""

import time
from threading import Thread

import pytest
import requests

NO_OF_REQUESTS = 100


# This fails with SQLite backend:
# ERROR tests/restapi/test_threaded_restapi.py::test_run_threaded_server - assert 30.0 == 1
# where 30.0 = <bound method QueuePool.timeout of <sqlalchemy.pool.impl.QueuePool object at 0x>>()
# where <bound method QueuePool.timeout of <sqlalchemy.pool.impl.QueuePool object at 0x>> =
# <sqlalchemy.pool.impl.QueuePool object at 0x>.timeout
# where <sqlalchemy.pool.impl.QueuePool object at 0x> = Engine(sqlite:////tmp/.../database.sqlite).pool
# where Engine(sqlite:////tmp/.../database.sqlite) = <sqlalchemy.orm.session.Session object at 0x>.bind
@pytest.mark.requires_psql
@pytest.mark.usefixtures('restrict_db_connections')
def test_run_threaded_server(restapi_server, server_url, aiida_localhost):
    """Run AiiDA REST API threaded in a separate thread and perform many sequential requests.

    This test will fail, if database connections are not being properly closed by the end-point calls.
    """
    server = restapi_server()

    # Create a thread that will contain the running server,
    # since we do not wish to block the main thread
    server_thread = Thread(target=server.serve_forever)
    _server_url = server_url(port=server.server_port)

    computer_id = aiida_localhost.uuid

    try:
        server_thread.start()

        for _ in range(NO_OF_REQUESTS):
            response = requests.get(f'{_server_url}/computers/{computer_id}', timeout=10)

            assert response.status_code == 200

            try:
                response_json = response.json()
            except ValueError:
                pytest.fail(f'Could not turn response into JSON. Response: {response.raw}')
            else:
                assert 'data' in response_json

    except Exception as exc:
        pytest.fail(f'Something went terribly wrong! Exception: {exc!r}')
    finally:
        server.shutdown()

        # Wait a total of 1 min (100 x 0.6 s) for the Thread to close/join, else fail
        for _ in range(100):
            if server_thread.is_alive():
                time.sleep(0.6)
            else:
                break
        else:
            pytest.fail('Thread did not close/join within 1 min after REST API server was called to shutdown')


@pytest.mark.skip('Is often failing on Python 3.8 and 3.9: see https://github.com/aiidateam/aiida-core/issues/4281')
@pytest.mark.usefixtures('restrict_db_connections')
def test_run_without_close_session(restapi_server, server_url, aiida_localhost, capfd):
    """Run AiiDA REST API threaded in a separate thread and perform many sequential requests"""
    from aiida.restapi.api import AiidaApi
    from aiida.restapi.resources import Computer

    class NoCloseSessionApi(AiidaApi):
        """Add Computer to this API (again) with a new endpoint, but pass an empty list for `get_decorators`"""

        def __init__(self, app=None, **kwargs):
            super().__init__(app=app, **kwargs)

            # This is a copy of adding the `Computer` resource,
            # but only a few URLs are added, and `get_decorators` is passed with an empty list.
            extra_kwargs = kwargs.copy()
            extra_kwargs.update({'get_decorators': []})
            self.add_resource(
                Computer,
                '/computers_no_close_session/',
                '/computers_no_close_session/<id>/',
                endpoint='computers_no_close_session',
                strict_slashes=False,
                resource_class_kwargs=extra_kwargs,
            )

    server = restapi_server(NoCloseSessionApi)
    computer_id = aiida_localhost.uuid

    # Create a thread that will contain the running server,
    # since we do not wish to block the main thread
    server_thread = Thread(target=server.serve_forever)

    try:
        server_thread.start()

        for _ in range(NO_OF_REQUESTS):
            requests.get(f'{server_url}/computers_no_close_session/{computer_id}', timeout=10)
        pytest.fail(f'{NO_OF_REQUESTS} requests were not enough to raise a SQLAlchemy TimeoutError!')

    except (requests.exceptions.ConnectionError, OSError):
        pass
    except Exception as exc:
        pytest.fail(f'Something went terribly wrong! Exception: {exc!r}')
    finally:
        server.shutdown()

        # Wait a total of 1 min (100 x 0.6 s) for the Thread to close/join, else fail
        for _ in range(100):
            if server_thread.is_alive():
                time.sleep(0.6)
            else:
                break
        else:
            pytest.fail('Thread did not close/join within 1 min after REST API server was called to shutdown')

    captured = capfd.readouterr()
    assert 'sqlalchemy.exc.TimeoutError: QueuePool limit of size ' in captured.err
