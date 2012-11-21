#!/usr/bin/env python

import slumber

# localhost testing, no auth for the moment
api = slumber.API("http://localhost:8000/api/v1")

print "***********************************************"
print "Query #1: incalculations__calcattrnumval__value__gt=7,incalculations__calcattrnumval__attribute__name='energy'"

validstructures = api.structure.get(incalculations__calcattrnumval__value__gt=7,incalculations__calcattrnumval__attribute__name='energy')

print "Total objects found: {}".format(validstructures['meta']['total_count'])
print ""
print "Structures in this page:"
for i, structure in enumerate(validstructures['objects']):
    print "Structure # {}:".format(validstructures['meta']['offset'] + i)
    print structure

print "***********************************************"
print "Query #2: incalculations__calcattrnumval__value__gt=9&incalculations__calcattrnumval__attribute__name__in=energy2&incalculations__calcattrnumval__attribute__name__in=energy"

validstructures = api.structure.get(incalculations__calcattrnumval__value__gt=9,incalculations__calcattrnumval__attribute__name__in=['energy2','energy'])

print "Total objects found: {}".format(validstructures['meta']['total_count'])
print ""
print "Structures in this page:"
for i, structure in enumerate(validstructures['objects']):
    print "Structure # {}:".format(validstructures['meta']['offset'] + i)
    print structure
    

