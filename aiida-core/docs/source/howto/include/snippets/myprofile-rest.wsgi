# wsgi script for AiiDA profile 'myprofile'
from aiida.manage.configuration import load_profile
from aiida.restapi.run_api import configure_api

load_profile('myprofile')

api = configure_api()
application = api.app
