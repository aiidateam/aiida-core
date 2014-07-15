#!/usr/bin/env python
"""
Some sample tests of how to use the slumber client (when the server is simply
run with
./manage runserver
and can be reached at http://localhost:8000/)

Note that to work, this example requires that the server is running, and that
there is some data in the database.

Note also that, unless in api.py the apply_filters is overridden, using the
.distinct() method, there may be duplicates in the results for very complicated
queries.
"""
import slumber

print "Connecting..."

# localhost testing, no auth for the moment
api = slumber.API("http://localhost:8000/api/v1")

print "Connected."

print "***********************************************"
print "Query #1: http://localhost:8000/api/v1/structure/?incalculations__calcattrnumval__value__gt=7&incalculations__calcattrnumval__attribute__name=energy&format=json"
print "##"
print "## Explanation: get all structures that are inputs of a calculation with"
print "## a (numerical) attribute named 'energy' and with value greater than 7."
print "##"

validstructures = api.structure.get(incalculations__calcattrnumval__value__gt=7,incalculations__calcattrnumval__attribute__name='energy')

print "Total objects found: {}".format(validstructures['meta']['total_count'])
print ""
print "Structures in this page:"
for i, structure in enumerate(validstructures['objects']):
    print "-> Structure # {}:".format(validstructures['meta']['offset'] + i),
    print structure['resource_uri']

print "***********************************************"
print "Query #2:  http://localhost:8000/api/v1/structure/?incalculations__calcattrnumval__value__gt=9&incalculations__calcattrnumval__attribute__name__in=energy2&incalculations__calcattrnumval__attribute__name__in=energy&format=json"
print "##"
print "## Explanation: get all structures that are inputs of a calculation with"
print "## a (numerical) attribute either named 'energy' or 'energy2' (note how"
print "## the __in filter is used) and with value greater than 9."
print "##"

validstructures = api.structure.get(incalculations__calcattrnumval__value__gt=9,incalculations__calcattrnumval__attribute__name__in=['energy2','energy'])

print "Total objects found: {}".format(validstructures['meta']['total_count'])
print ""
print "Structures in this page:"
for i, structure in enumerate(validstructures['objects']):
    print "-> Structure # {}:".format(validstructures['meta']['offset'] + i),
    print structure['resource_uri']
    

