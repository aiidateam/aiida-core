#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aiida.restapi.api import AiidaApi, App
from aiida.restapi.run_api import run_api
from flask_restful import Resource

class NewResource(Resource):
    """
    resource containing GET and POST methods. Description of each method
    follows:

    GET: returns id, ctime, and attributes of the latest created Dict.

    POST: creates a Dict object, stores it in the database,
    and returns its newly assigned id.

    """

    def get(self):
        from aiida.orm import QueryBuilder, Dict

        qb = QueryBuilder()
        qb.append(Dict,
                  project=['id', 'ctime', 'attributes'],
                  tag='pdata')
        qb.order_by({'pdata': {'ctime': 'desc'}})
        result = qb.first()

        # Results are returned as a dictionary, datetime objects is
        # serialized as ISO 8601
        return dict(id=result[0],
                    ctime=result[1].isoformat(),
                    attributes=result[2])

    def post(self):
        from aiida.orm import Dict

        params = dict(property1='spam', property2='egg')
        paramsData = Dict(dict=params).store()

        return {'id': paramsData.pk}

class NewApi(AiidaApi):

    def __init__(self, app=None, **kwargs):
        """
        This init serves to add new endpoints to the basic AiiDA Api

        """
        super().__init__(app=app, **kwargs)

        self.add_resource(NewResource, '/new-endpoint/', strict_slashes=False)

# processing the options and running the app

import aiida.restapi.common as common
from aiida import load_profile

CONFIG_DIR = common.__path__[0]

import click
@click.command()
@click.option('-P', '--port', type=click.INT, default=5000,
    help='Port number')
@click.option('-H', '--hostname', default='127.0.0.1',
    help='Hostname')
@click.option('-c','--config-dir','config',type=click.Path(exists=True), default=CONFIG_DIR,
    help='the path of the configuration directory')
@click.option('--debug', 'debug', is_flag=True, default=False,
    help='run app in debug mode')
@click.option('--wsgi-profile', 'wsgi_profile', is_flag=True, default=False,
    help='to use WSGI profiler middleware for finding bottlenecks in web application')
def newendpoint(**kwargs):
    """
    runs the REST api
    """
    # Invoke the runner
    run_api(App, NewApi, **kwargs)


# main program
if __name__ == '__main__':
    """
    Run the app with the provided options. For example:
    python example.py --hostname=127.0.0.2 --port=6000
    """

    load_profile()
    newendpoint()
