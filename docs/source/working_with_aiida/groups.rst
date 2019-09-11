Groups
------

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

1. **Create a new Group.**
    From the command line interface::

      verdi group create test_group

    From the python interface::

      In [1]: group = Group(label="test_group")

      In [2]: group.store()
      Out[2]: <Group: "test_group" [type user], of user xxx@xx.com>



2. **List available Groups.**

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


3. **Add nodes to a Group.**
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

4. **Show information about a Group.**
    From the command line interface::

      verdi group show test_group
      -----------------  ----------------
      Group label        test_group
      Group type_string  user
      Group description  <no description>
      -----------------  ----------------
      # Nodes:
        PK  Type    Created
      ----  ------  ---------------
         1  Code    26D:21h:45m ago



5. **Remove nodes from a Group.**

    From the command line interface::

      verdi group remove-nodes -G test_group 1
      Do you really want to remove 1 nodes from Group<test_group>? [y/N]: y

    From the python interface::

      In [1]: group = Group.get(label='test_group')

      In [2]: group.clear()

6. **Rename Group.**
    From the command line interface::

      verdi group relabel test_group old_group
      Success: Label changed to old_group

    From the python interface::

      In [1]: group = Group.get(label='old_group')

      In [2]: group.label = "another_group"

7. **Delete Group.**
    From the command line interface::

      verdi group delete another_group
      Are you sure to delete Group<another_group>? [y/N]: y
      Success: Group<another_group> deleted.



8. **Copy one group into another.**
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



