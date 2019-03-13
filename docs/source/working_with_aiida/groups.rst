Groups
------

Groups provide an additional level of data organization based on some common
property(ies) shared between them. As by default AiiDA manages only casual
relationships between calculations and data objecs -- it is often desired to
organize them in Groups.

Nodes of any types may be organized in Groups. Unlike Nodes, Groups can be
modified at any time. Here we profide the list of typical operations that may
be performed with Groups:

.. note:: Any deletion operation like delition of a Group or nodes from a Group
  will not delete the nodes themselfs. They will remain in you AiiDA database.


1. **Create a new Group.**
    From command line interface::

      > verdi group create test_group

    From python interface::
      
      In [1]: group = Group(label="test_group")

      In [2]: group.store()
      Out[2]: <Group: "test_group" [type user], of user xxx@xx.com>



2. **List available Groups.**
      > verdi group list

    .. note:: By default ``verdi group list`` only shows groups of type *user*.
      In case you want to show groups of other type use ``-t/--type`` options. If
      you want to show groups of all types, use ``-a/--all-types`` option.

    From python interface::

      In [1]: query = QueryBuilder()

      In [2]: query.append(Group, filters={'type_string':'user'})
      Out[2]: <aiida.orm.querybuilder.QueryBuilder at 0x7f20db413ef0>

      In [3]: query.all()
      Out[3]: 
      [[<Group: "another_group" [type user], of user ya@epfl.ch>],
       [<Group: "old_group" [type user], of user ya@epfl.ch>],
       [<Group: "new_group" [type user], of user ya@epfl.ch>]]


3. **Add nodes to a Group.**
    From command line interface::

      > verdi group addnodes -G test_group 1

    Here we are adding Node with pk number 1 to the group we just created

    From python interface::

      In [3]: from aiida.orm import Dict

      In [4]: p = Dict().store()

      In [5]: p
      Out[5]: <Dict: uuid: 09b3d52a-d0c4-4e3c-823c-6157f84af920 (pk: 2)>

      In [6]: group.add_nodes(p)

4. **Show information about a Group.**
    From command line interface::

      > verdi group show test_group


5. **Remove nodes from a Group.**

    From command line interface::

      > verdi group removenodes -G test_group 1


6. **Rename Group.**
    From command line interface::
    
      > verdi group rename test_group old_group

    From python interface::
      
      In [1]: group = Group.get(label='test_group')

      In [2]: group.label = "another_group"

7. **Delete Group.**
    From command line interface::
    
      > verdi group delete old_group

8. **Copy one group into anohter.**
    This operation will copy the content of source group into the destination
    group. Moreover, if the destination group does not exist it will be created
    automatically.

    From command line interface::
    
      > verdi group copy source_group destination_group

    From python interface::
      
      In [1]: src_group = Group.objects.get(label='source_group')

      In [2]: dest_group = Group.get_or_create(label='destination_group')[0]

      In [3]: dest_group.add_nodes(src_group.nodes)

    

