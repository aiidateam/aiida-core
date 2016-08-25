## Pagination defaults
LIMIT_DEFAULT = 400
PERPAGE_DEFAULT = 20

##Version prefix for all the URLs
PREFIX="/api/v2"

## Flask app configs.
#DEBUG: True/False. enables debug mode N.B.
#!!!For production run use ALWAYS False!!!
#PROPAGATE_EXCEPTIONS: True/False serve REST exceptions to the client (and not a
# generic 500: Internal Server Error exception)
APP_CONFIG = {
              'DEBUG': False,
              'PROPAGATE_EXCEPTIONS': True,
              }

## Caching
#memcached: backend caching system
cache_config={'CACHE_TYPE': 'memcached'}
#Caching TIMEOUTS (in seconds)
TIMEOUT_NODES = 10
TIMEOUT_COMPUTERS = 10*60
TIMEOUT_DATAS = 10*60
TIMEOUT_GROUPS = 10*60
TIMEOUT_CODES = 10*60

