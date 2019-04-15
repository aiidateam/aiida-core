# -*- coding: utf-8 -*-

setup = """
import ultrajson
from functools import partial
json_loads = partial(ultrajson.loads, precise_float=True)

import re
date_reg = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(\+\d{2}:\d{2})?$')

def loads_json_rec(s):
    ret = json_loads(s)

    def f(d):
        if isinstance(d, list):
            for i, val in enumerate(d):
                d[i] = f(val)
            return d
        elif isinstance(d, dict):
            for k, v in d.iteritems():
                d[k] = f(v)
            return d
        elif isinstance(d, basestring):
            if date_reg.match(d):
                try:
                    return parser.parse(d)
                except (ValueError, TypeError):
                    return d
            return d
        return d

    return f(ret)

def loads_json_ite(s):
    ret = json_loads(s)

    if isinstance(ret, dict):
        stack = [(ret, it[0], it[1]) for it in ret.iteritems()]
    elif isinstance(ret, list):
        stack = [(ret, i, key) for i, key in enumerate(ret)]
    else:
        return ret

    while stack:
        curr, key, val = stack.pop()
        if isinstance(val, dict):
            stack.extend([(val, sub_key, sub_val) for sub_key, sub_val in val.iteritems()])
        if isinstance(val, list):
            stack.extend([(val, i, sub_val) for i, sub_val in enumerate(val)])
        if isinstance(val, basestring):
            if date_reg.match(val):
                try:
                    curr[key] = parser.parse(val)
                except (ValueError, TypeError):
                    pass

    return ret


j = ('{"kinds":[{"symbols":["C"],"weights":[1.0],"mass":12.011,"name":"C"}],'
'"pbc3":true,"pbc2":true,"pbc1":true,"sites":[{"position":[1.26105,0.728067557,38.35413465],"kind_name":"C"}'
',{"position":[1.26105,0.728067557,33.72086535],"kind_name":"C"},{"position":[1.26105,0.728067557,39.89884605]'
',"kind_name":"C"},{"position":[1.26105,0.728067557,32.17615395],"kind_name":"C"},{"position":[0.0,0.0,35.7800481]'
',"kind_name":"C"},{"position":[0.0,1.4561351139,36.2949519],"kind_name":"C"},{"position":[0.0,0.0,31.6613943],"kind_name":"C"}'
',{"position":[0.0,1.4561351139,40.4136057],"kind_name":"C"},{"position":[0.0,0.0,42.4726443],"kind_name":"C"}'
',{"position":[0.0,1.4561351139,29.6023557],"kind_name":"C"},{"position":[0.0,0.0,30.11711535],"kind_name":"C"}'
',{"position":[0.0,1.4561351139,41.95788465],"kind_name":"C"},{"position":[0.0,0.0,34.23576915],"kind_name":"C"}'
',{"position":[0.0,1.4561351139,37.83923085],"kind_name":"C"},{"position":[0.0,1.4561351139,9.52413465],"kind_name":"C"}'
',{"position":[0.0,1.4561351139,4.89086535],"kind_name":"C"},{"position":[0.0,1.4561351139,11.06884605],"kind_name":"C"}'
',{"position":[0.0,1.4561351139,3.34615395],"kind_name":"C"},{"position":[1.26105,0.728067557,6.9500481],"kind_name":"C"}'
',{"position":[0.0,0.0,7.4649519],"kind_name":"C"},{"position":[1.26105,0.728067557,2.8313943],"kind_name":"C"}'
',{"position":[0.0,0.0,11.5836057],"kind_name":"C"},{"position":[1.26105,0.728067557,13.6426443],"kind_name":"C"}'
',{"position":[2.5221,0.0,0.7723557],"kind_name":"C"},{"position":[1.26105,0.728067557,1.28711535],"kind_name":"C"}'
',{"position":[2.5221,0.0,13.12788465],"kind_name":"C"},{"position":[1.26105,0.728067557,5.40576915],"kind_name":"C"}'
',{"position":[0.0,0.0,9.00923085],"kind_name":"C"},{"position":[0.0,0.0,23.93913465],"kind_name":"C"}'
',{"position":[0.0,0.0,19.30586535],"kind_name":"C"},{"position":[0.0,0.0,25.48384605],"kind_name":"C"}'
',{"position":[0.0,0.0,17.76115395],"kind_name":"C"},{"position":[0.0,1.4561351139,21.3650481],"kind_name":"C"}'
',{"position":[1.26105,0.728067557,21.8799519],"kind_name":"C"},{"position":[0.0,1.4561351139,17.2463943],"kind_name":"C"}'
',{"position":[1.26105,0.728067557,25.9986057],"kind_name":"C"},{"position":[0.0,1.4561351139,28.0576443],"kind_name":"C"}'
',{"position":[1.26105,0.728067557,15.1873557],"kind_name":"C"},{"position":[0.0,1.4561351139,15.70211535],"kind_name":"C"}'
',{"position":[1.26105,0.728067557,27.54288465],"kind_name":"C"},{"position":[0.0,1.4561351139,19.82076915],"kind_name":"C"}'
',{"position":[1.26105,0.728067557,23.42423085],"kind_name":"C"}]'
',"cell":[[2.5221,0.0,0.0],[-1.26105,2.1842026709,0.0],[0.0,0.0,43.245]]}')
"""


import timeit

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

if __name__ == "__main__":
    rec_res = timeit.timeit('loads_json_rec(j)', setup=setup, number=100000)
    ite_res = timeit.timeit('loads_json_ite(j)', setup=setup, number=100000)

    print("Recursive time: {} | Iterative time: {}".format(rec_res, ite_res))
