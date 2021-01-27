# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the configuration options from `aiida.restapi.common.config` when running the REST API."""
# pylint: disable=redefined-outer-name
import pytest


@pytest.fixture
def create_app():
    """Set up Flask App"""
    from aiida.restapi.run_api import configure_api

    def _create_app(**kwargs):
        catch_internal_server = kwargs.pop('catch_internal_server', True)
        api = configure_api(catch_internal_server=catch_internal_server, **kwargs)
        api.app.config['TESTING'] = True
        return api.app

    return _create_app


def test_posting(create_app):
    """Test CLI_DEFAULTS['POSTING'] configuration"""
    from aiida.restapi.common.config import API_CONFIG

    app = create_app(posting=False)

    url = f'{API_CONFIG["PREFIX"]}/querybuilder'
    for method in ('get', 'post'):
        with app.test_client() as client:
            response = getattr(client, method)(url)

        assert response.status_code == 404
        assert response.status == '404 NOT FOUND'

    del app
    app = create_app(posting=True)

    url = f'{API_CONFIG["PREFIX"]}/querybuilder'
    for method in ('get', 'post'):
        with app.test_client() as client:
            response = getattr(client, method)(url)

        assert response.status_code != 404
        assert response.status != '404 NOT FOUND'
