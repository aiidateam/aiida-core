# -*- coding: utf-8 -*-
# wsgi script for AiiDA profile 'myprofile'
from aiida.restapi.run_api import configure_api
from aiida.manage.configuration import load_profile

load_profile('myprofile')

api = configure_api()
application = api.app
