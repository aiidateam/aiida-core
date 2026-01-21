from someworkchain import SomeWorkchain

from aiida import engine, load_profile, orm

load_profile()

x = orm.QueryBuilder().append(orm.Group, filters={'label': {'==': 'some'}}).first(flat=True)

if x is None:
    x = orm.Group(label='some').store()

node = engine.run(SomeWorkchain, x=x)
l = node['result']
print([node for node in l.nodes])
