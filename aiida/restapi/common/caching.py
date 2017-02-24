from flask_cache import Cache
from aiida.restapi.api import app
from aiida.restapi.common.config import cache_config

#Would be nice to be able to specify here what has to be cached or not!
#Probably this is not doable because cachced and memoize only work as decorators
cache = Cache(app, config=cache_config)
