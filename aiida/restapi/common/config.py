## Pagination defaults
LIMIT_DEFAULT = 400
PERPAGE_DEFAULT = 20

##Version prefix for all the URLs
PREFIX="/api/v2"

## Caching
# General configs
cache_config={'CACHE_TYPE': 'memcached'}
#Caching TIMEOUTS (in seconds)
TIMEOUT_NODES = 10
TIMEOUT_COMPUTERS = 10*60
TIMEOUT_DATAS = 10*60
TIMEOUT_GROUPS = 10*60
TIMEOUT_CODES = 10*60

