


def delete_nodes(pks, follow_calls=False, follow_returns=False, dry_run=False, force=False, verbosity=0):
    """
    :note: The script will also delete
    all children calculations generated from the specified nodes.

    :param pks: a list of the PKs of the nodes to delete
    :param bool follow_calls: Follow calls
    :param bool follow_returns: Follow returns
    :param bool dry_run: Do not delete, a dry run, with statistics printed according to verbosity levels.
    :param bool force: Do not ask for confirmation to delete nodes.
    :param int verbosity:
        The verbosity levels, 0 prints nothing, 1 prints just sums and total, 2 prints individual nodes.
    """

    from aiida.orm.querybuilder import QueryBuilder
    from aiida.common.links import LinkType
    from aiida.orm.node import Node
    from aiida.orm import load_node
    from aiida.backends.utils import delete_nodes_and_connections

    # The following code is just for the querying of downwards provenance.
    # Ideally, there should be a module to interface with, but this is the solution
    # for now.
    # By only dealing with ids, and keeping track of what has been already
    # visited in the query, there's good performance
    link_types_to_follow = [LinkType.CREATE.value, LinkType.INPUT.value]
    if follow_calls:
        link_types_to_follow.append(LinkType.CALL.value)
    if follow_returns:
        link_types_to_follow.append(LinkType.RETURN.value)
    edge_filters={'type':{'in':link_types_to_follow}}

    operational_set = set().union(set(pks)) # Copy the set!
    pks_set_to_delete = set().union(set(pks))
    while operational_set:
        # new_pks_set are the the pks of all nodes that are connected to the operational node set with the edges specified.
        new_pks_set = set([i for i, in QueryBuilder().append(
                Node, filters={'id':{'in':operational_set}}).append(
                Node,project='id', edge_filters=edge_filters).iterall()])
        # The operational set is only those pks that haven't been yet put into the pks_set_to_delete.
        operational_set = new_pks_set.difference(pks_set_to_delete)

        # I add these pks in the pks_set_to_delete with a union
        pks_set_to_delete = pks_set_to_delete.union(new_pks_set)

    if verbosity > 0:
        if dry_run:
            print "I would have deleted", " ".join(map(str, sorted(pks_set_to_delete)))
        else:
            print "I will delete {} nodes".format(len(pks_set_to_delete))
        if verbosity > 1:
            qb = QueryBuilder().append(Node, filters={'id':{'in':pks_set_to_delete}}, project=('uuid', 'id', 'type', 'label'))
            for uuid, pk, type_string, label in qb.iterall():
                try:
                    short_type_string = type_string.split('.')[-2]
                except IndexError:
                    short_type_string = type_string
                print "   {} {} {} {}".format(uuid, pk, short_type_string, label)

    if dry_run:
        if verbosity > 0:
            print "This was a dry run, exiting without deleting anything"
        return

    # Asking for user confirmation here
    if not(force) and raw_input("Continue?").lower() != 'y':
        return

    # Recover the list of folders to delete before actually deleting
    # the nodes.  I will delete the folders only later, so that if
    # there is a problem during the deletion of the nodes in
    # the DB, I don't delete the folders

    folders = [load_node(_).folder for _ in pks_set_to_delete]

    delete_nodes_and_connections(pks_set_to_delete)
    # If we are here, we managed to delete the entries from the DB.
    # I can now delete the folders
    for f in folders:
        f.erase()

