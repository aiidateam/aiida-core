About Groups
------------

Groups are a tool to organize the nodes of the provenance graph into sub sets. Any
number of groups can be created and each group can contain any number of nodes of any type.

Typically, you want to put multiple nodes into a group because they share some common property,
and through the group they can easily be referenced. Unlike nodes, groups can be
modified at any time. Here we profide a list of typical operations that may
be performed with groups:

.. note:: Any deletion operation related to groups won't affect the nodes themselves.
  For example if you delete a group, the nodes that belonged to the group will remain
  in the database. The same happens if you delete nodes from the group -- they will remain
  in the database but won't belong to the group anymore.


Create a new Group
------------------

From the command line interface::

    verdi group create test_group

From the python interface::

    In [1]: group = Group(label="test_group")

    In [2]: group.store()
    Out[2]: <Group: "test_group" [type user], of user xxx@xx.com>


List available Groups
---------------------

Example::

    verdi group list

By default ``verdi group list`` only shows groups of the type *user*.
In case you want to show groups of another type use ``-t/--type`` option. If
you want to show groups of all types, use the ``-a/--all-types`` option.

From the command line interface::

    verdi group list -t user

From the python interface::

    In [1]: query = QueryBuilder()

    In [2]: query.append(Group, filters={'type_string':'user'})
    Out[2]: <aiida.orm.querybuilder.QueryBuilder at 0x7f20db413ef0>

    In [3]: query.all()
    Out[3]:
    [[<Group: "another_group" [type user], of user xxx@xx.com>],
    [<Group: "old_group" [type user], of user xxx@xx.com>],
    [<Group: "new_group" [type user], of user xxx@xx.com>]]


Add nodes to a Group
--------------------

Once the ``test_group`` has been created, we can add nodes to it. To add the node with ``pk=1`` to the group we need to do the following.

From the command line interface::

    verdi group add-nodes -G test_group 1
    Do you really want to add 1 nodes to Group<test_group>? [y/N]: y

From the python interface::

    In [1]: group = Group.get(label='test_group')
    In [2]: from aiida.orm import Dict
    In [3]: p = Dict().store()
    In [4]: p
    Out[4]: <Dict: uuid: 09b3d52a-d0c4-4e3c-823c-6157f84af920 (pk: 2)>
    In [5]: group.add_nodes(p)


Show information about a Group
------------------------------

From the command line interface::

    verdi group show test_group
    -----------------  ----------------
    Group label        test_group
    Group type_string  user
    Group description  <no description>
    -----------------  ----------------
    # Nodes:
    PK    Type    Created
    ----  ------  ---------------
     1    Code    26D:21h:45m ago


Remove nodes from a Group
-------------------------

From the command line interface::

    verdi group remove-nodes -G test_group 1
    Do you really want to remove 1 nodes from Group<test_group>? [y/N]: y

From the python interface::

    In [1]: group = Group.get(label='test_group')
    In [2]: group.clear()


Rename Group
------------

From the command line interface::

      verdi group relabel test_group old_group
      Success: Label changed to old_group

From the python interface::

    In [1]: group = Group.get(label='old_group')
    In [2]: group.label = "another_group"


Delete Group
------------

From the command line interface::

      verdi group delete another_group
      Are you sure to delete Group<another_group>? [y/N]: y
      Success: Group<another_group> deleted.


Copy one group into another
---------------------------

This operation will copy the nodes of the source group into the destination
group. Moreover, if the destination group did not exist before, it will
be created automatically.

From the command line interface::

    verdi group copy source_group dest_group
    Success: Nodes copied from group<source_group> to group<dest_group>

From the python interface::

    In [1]: src_group = Group.objects.get(label='source_group')
    In [2]: dest_group = Group(label='destination_group').store()
    In [3]: dest_group.add_nodes(list(src_group.nodes))


Create a `Group` subclass
-------------------------
It is possible to create a subclass of `Group` to implement custom functionality.
To make the instances of the subclass storable and loadable, it has to be registered through an entry point in the ``aiida.groups`` entry point category.
For example, assuming we have a subclass ``SubClassGroup`` in the module ``aiida_plugin.groups.sub_class:SubClassGroup``, to register it, one has to add the following to the ``setup.py`` of the plugin package::

    "entry_points": {
        "aiida.groups": [
            "plugin.sub_class = aiida_plugin.groups.sub_class:SubClassGroup"
        ]
    }

Now that the subclass is properly registered, instances can be stored::

    group = SubClassGroup(label='sub-class-group')
    group.store()

The ``type_string`` of the group instance corresponds to the entry point name and so in this example is ``plugin.sub_class``.
This is what AiiDA uses to load the correct class when reloading the group from the database::

    group = load_group(group.pk)
    assert isinstance(group, SubClassGroup)

If the entry point is not currently registered, because the corresponding plugin package is not installed for example, AiiDA will issue a warning and fallback onto the ``Group`` base class.

Group hierarchies with `GroupPath`
----------------------------------

Groups in AiiDA are inherently "flat", in that groups may only contain nodes and not other groups.
However, the `GroupPath` utility allows one to construct *virtual* group hierarchies based on delimited group labels.

`GroupPath` is designed to work in much the same way as python's `pathlib.Path`,
whereby paths are denoted by forward slash characters '/' in group labels.
For example say we have the groups::

    $ verdi group list
    PK    Label                    Type string    User
    ----  -----------------        -------------  --------------
    1     base1/sub_group1         core           user@email.com
    2     base1/sub_group2         core           user@email.com
    3     base2/other/sub_group3   core           user@email.com

We can also access them as from the command-line as::

    $ verdi group path ls -l
    Path         Sub-Groups
    ---------  ------------
    base1                 2
    base2                 1
    $ verdi group path ls base1
    base1/sub_group1
    base1/sub_group2

Or from the python interface::

    In [1]: from aiida.tools.groups import GroupPath
    In [2]: path = GroupPath("base1")
    In [3]: print(list(path.children))
    Out[3]: [GroupPath('base1/sub_group2', cls='<class 'aiida.orm.groups.Group'>'),
             GroupPath('base1/sub_group1', cls='<class 'aiida.orm.groups.Group'>')]

The `GroupPath` can be constructed using indexing or "divisors"::

    In [4]: path = GroupPath()
    In [5]: path["base1"] == path / "base1"
    Out[5]: True

Using the `browse` attribute, you can also construct the paths as preceding attributes.
This is useful in interactive environments, whereby available paths will be shown in the tab-completion::

    In [6]: path.browse.base1.sub_group2()
    Out[6]: GroupPath('base1/sub_group2', cls='<class 'aiida.orm.groups.Group'>')

To check the existence of a path element::

    In [7]: "base1" in path
    Out[7]: True

A group may be "virtual", in which case its label does not directly relate to a group,
or the group can be retrieved with the `get_group()` method::

    In [8]: path.is_virtual
    Out[8]: True
    In [9]: path.get_group() is None
    Out[9]: True
    In [10]: path["base1/sub_group1"].get_group() is None
    Out[10]: True
    In [11]: path["base1/sub_group1"].get_group()
    Out[11]: <Group: "base1/sub_group1" [type core], of user user@email.com>

Groups can be created and destroyed::

    In [12]: path["base1/sub_group1"].delete_group()
    In [13]: path["base1/sub_group1"].is_virtual
    Out[13]: True
    In [14]: path["base1/sub_group1"].get_or_create_group()
    Out[14]: (<Group: "base1/sub_group1" [type core], of user user@email.com>, True)
    In [15]: path["base1/sub_group1"].is_virtual
    Out[15]: False

To traverse paths, use the `children` attribute - for recursive traversal, use `walk`::

    In [16]: for subpath in path.walk(return_virtual=False):
        ...:     print(subpath)
        ...:
    GroupPath('base1/sub_group1', cls='<class 'aiida.orm.groups.Group'>')
    GroupPath('base1/sub_group2', cls='<class 'aiida.orm.groups.Group'>')
    GroupPath('base2/other/sub_group3', cls='<class 'aiida.orm.groups.Group'>')

You can also traverse directly through the nodes of a path,
optionally filtering by node class and any other filters allowed by the `QueryBuilder`::

    In [17]: from aiida.orm import Data
    In [18]: data = Data()
    In [19]: data.set_extra("key", "value")
    In [20]: data.store()
    Out[20]: <Data: uuid: 0adb5224-585d-4fd4-99ae-20a071972ddd (pk: 1)>
    In [21]: path["base1/sub_group1"].get_group().add_nodes(data)
    In [21]: next(path.walk_nodes(node_class=Data, filters={"extras.key": "value"}))
    Out[21]: WalkNodeResult(group_path=GroupPath('base1/sub_group1', cls='<class 'aiida.orm.groups.Group'>'),
    node=<Data: uuid: 0adb5224-585d-4fd4-99ae-20a071972ddd (pk: 1)>)

Finally, you can also specify the `Group` subclasses (discussed above),
in which case only groups of that subclass will be recognised::

    In [22]: from aiida.orm import UpfFamily
    In [23]: path2 = GroupPath(cls=UpfFamily)
    In [24]: path2["base1"].get_or_create_group()
    Out[24]: (<UpfFamily: "base1" [type core.upf], of user user@email.com>, True)
