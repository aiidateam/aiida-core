#!/usr/bin/env python
from aida.common.utils import load_django
load_django()

def shorten(v):
    limit = 60
    text = unicode(v)
    text.replace('\n','').replace('\r','')
    if len(text) > limit:
        return text[:limit-3] + u"..."
    else:
        return text

import sys
from aida.orm import Node, Calculation

try:
    uuid = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Pass a UUID"
    sys.exit(1)

n = Node(uuid=uuid)
print '\n'.join('{}={}'.format(k,shorten(v)) for k,v in n.iterattrs())

c = Calculation(uuid=uuid)

