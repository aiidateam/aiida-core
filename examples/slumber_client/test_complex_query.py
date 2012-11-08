#!/usr/bin/env python

import slumber

# localhost testing, no auth for the moment
api = slumber.API("http://localhost:8000/api/v1")

validstructures = api.struc.get(inpcalc__calcattrnumval__val__gt=10,inpcalc__calcattrnumval__attr__title='energy')

print "Total objects found: {}".format(validstructures['meta']['total_count'])
print ""
print "Structures in this page:"
for i, structure in enumerate(validstructures['objects']):
    print "Structure # {}:".format(validstructures['meta']['offset'] + i)
    print structure
    

