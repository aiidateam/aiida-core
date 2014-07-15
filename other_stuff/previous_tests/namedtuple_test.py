from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])

p = Point(3,4)

print p
print p.x
print p._replace(x=6, y=7)


t = p._asdict()
t['x'] = 5
print t['x']

setattr(p,'c',7)  # will fail