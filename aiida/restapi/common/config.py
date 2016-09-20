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

##JSON serialization config. Leave this dictionary empty if default Flask
# serializer is desired.
SERIALIZER_CONFIG = {'datetime_format': 'default'}
# Here is a list a all supported fields. If a field is not present in the
# dictionary its value is assumed to be 'default'.
# DATETIME_FORMAT: allowed values are 'asinput' and 'default'.

## Caching
#memcached: backend caching system
cache_config={'CACHE_TYPE': 'memcached'}

#Caching TIMEOUTS (in seconds)
CACHING_TIMEOUTS = {
    'nodes': 10,
    'users': 10,
    'calculations': 10,
    'computers': 10,
    'datas': 10,
    'groups': 10,
    'codes': 10,
}
