import logging
import sys

aidalogger = logging.getLogger("aida")

# For the moment I hardcode the logger properties: in this way things go
# to stderr with a specific format
FORMAT = '[%(name)s@%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)

#fallback_handler = logging.StreamHandler(stream=sys.stderr)
#aidalogger.addHandler(fallback_handler)
