# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



def delete_nodes(pks, follow_calls=False, follow_returns=False, 
        dry_run=False, force=False, disable_checks=False, verbosity=0):
    """
    Delete nodes by a list of pks

    :note: The script will also delete all children calculations generated from the specified nodes.

    :param pks: a list of the PKs of the nodes to delete
    :param bool follow_calls: Follow calls
    :param bool follow_returns:
        Follow returns. This is a very dangerous option, since anything returned by a workflow might have
        been used as input in many other calculations. Use with care, and never combine with force.
    :param bool dry_run: Do not delete, a dry run, with statistics printed according to verbosity levels.
    :param bool force: Do not ask for confirmation to delete nodes.
    :param bool disable_checks:
        If True, will not check whether calculations are losing created data or called instances.
        If checks are disabled, also logging is disabled.
    :param bool force: Do not ask for confirmation to delete nodes.
    :param int verbosity:
        The verbosity levels, 0 prints nothing, 1 prints just sums and total, 2 prints individual nodes.
    """

    from aiida.orm.querybuilder import QueryBuilder
    from aiida.common.links import LinkType
    from aiida.orm.node import Node
    from aiida.orm.calculation import Calculation
    from aiida.orm.data import Data
    from aiida.orm import load_node
    from aiida.backends.utils import delete_nodes_and_connections
    from aiida.backends.utils import get_automatic_user
    user_email = get_automatic_user().email


    if not pks:
        # If I was passed an empty list, I don't to anything
        # I prefer checking explicitly, an empty set might be problematic for the queries done below.
        if verbosity:
            print "Nothing to delete"
        return

    # The following code is just for the querying of downwards provenance.
    # Ideally, there should be a module to interface with, but this is the solution for now.
    # By only dealing with ids, and keeping track of what has been already
    # visited in the query, there's good performance and no infinite loops.
    link_types_to_follow = [LinkType.CREATE.value, LinkType.INPUT.value]
    if follow_calls:
        link_types_to_follow.append(LinkType.CALL.value)
    if follow_returns:
        link_types_to_follow.append(LinkType.RETURN.value)

    edge_filters={'type':{'in':link_types_to_follow}}

    # Operational set always includes the recently (in the last iteration added) nodes.
    operational_set = set().union(set(pks)) # Union to copy the set!
    pks_set_to_delete = set().union(set(pks))
    while operational_set:
        # new_pks_set are the the pks of all nodes that are connected to the operational node set
        # with the links specified.
        new_pks_set = set([i for i, in QueryBuilder().append(
                Node, filters={'id':{'in':operational_set}}).append(
                Node,project='id', edge_filters=edge_filters).iterall()])
        # The operational set is only those pks that haven't been yet put into the pks_set_to_delete.
        operational_set = new_pks_set.difference(pks_set_to_delete)

        # I add these pks in the pks_set_to_delete with a union
        pks_set_to_delete = pks_set_to_delete.union(new_pks_set)

    if verbosity > 0:
        print "I {} delete {} node{}".format(
                'would' if dry_run else 'will',
                 len(pks_set_to_delete),
                 's' if len(pks_set_to_delete)> 1 else '')
        if verbosity > 1:
            qb = QueryBuilder().append(Node, filters={'id':{'in':pks_set_to_delete}}, project=('uuid', 'id', 'type', 'label'))
            print "The nodes I {} delete:".format('would' if dry_run else 'will')
            for uuid, pk, type_string, label in qb.iterall():
                try:
                    short_type_string = type_string.split('.')[-2]
                except IndexError:
                    short_type_string = type_string
                print "   {} {} {} {}".format(uuid, pk, short_type_string, label)


    # Here I am checking whether I am deleting
    ## A data instance without also deleting the creator, which brakes relationship between a calculation and its data
    ## A calculation instance that was called, without also deleting the caller.

    if not disable_checks:
        called_qb = QueryBuilder()
        called_qb.append(Calculation, filters={'id': {'!in': pks_set_to_delete}}, project='id')
        called_qb.append(Calculation, project='type', edge_project='label',
                filters={'id': {'in': pks_set_to_delete}},
                edge_filters={'type': {'==': LinkType.CALL.value}})
        caller_to_called2delete = called_qb.all()

        if verbosity > 0 and caller_to_called2delete:
            calculation_pks_losing_called = set(zip(*caller_to_called2delete)[0])
            print "\n{} calculation{} {} lose at least one called instance".format(
                    len(calculation_pks_losing_called),
                    's' if len(calculation_pks_losing_called) > 1 else '',
                    'would' if dry_run else 'will')
            if verbosity > 1:
                print "These are the calculations that {} lose a called instance:".format('would' if dry_run else 'will')
                for calc_losing_called_pk in calculation_pks_losing_called:
                    print '  ', load_node(calc_losing_called_pk)

        created_qb = QueryBuilder()
        created_qb.append(Calculation, filters={'id':{'!in': pks_set_to_delete}}, project='id')
        created_qb.append(Data, project='type', edge_project='label',
                filters={'id':{'in': pks_set_to_delete}},
                edge_filters={'type':{'==':LinkType.CREATE.value}})

        creator_to_created2delete = created_qb.all()
        if verbosity > 0 and creator_to_created2delete:
            calculation_pks_losing_created = set(zip(*creator_to_created2delete)[0])
            print "\n{} calculation{} {} lose at least one created data-instance".format(
                    len(calculation_pks_losing_created),
                    's' if len(calculation_pks_losing_created) > 1 else '',
                    'would' if dry_run else 'will')
            if verbosity > 1:
                print "These are the calculations that {} lose a created data-instance:".format('would' if dry_run else 'will')
                for calc_losing_created_pk in calculation_pks_losing_created:
                    print '  ', load_node(calc_losing_created_pk)

    if dry_run:
        if verbosity > 0:
            print "\nThis was a dry run, exiting without deleting anything"
        return



    # Asking for user confirmation here
    if force:
        pass
    else:
        print "YOU ARE ABOUT TO DELETE {} NODES! THIS CANNOT BE UNDONE!".format(len(pks_set_to_delete))
        if raw_input("Shall I continue? [Y/N] ").lower() != 'y':
            print "Exiting without deleting"
            return

    # Recover the list of folders to delete before actually deleting
    # the nodes.  I will delete the folders only later, so that if
    # there is a problem during the deletion of the nodes in
    # the DB, I don't delete the folders
    folders = [load_node(_).folder for _ in pks_set_to_delete]


    delete_nodes_and_connections(pks_set_to_delete)

    if not disable_checks:
        # I pass now to the log the information for calculations losing created data or called instances
        for calc_pk, calc_type_string, link_label in caller_to_called2delete:
            calc = load_node(calc_pk)
            calc.logger.warning("User {} deleted "
                "an instance of type {} "
                "called with the label {} "
                "by this calculation".format(
                    user_email, calc_type_string, link_label))

        for calc_pk, data_type_string, link_label  in creator_to_created2delete:
            calc = load_node(calc_pk)
            calc.logger.warning("User {} deleted "
                "an instance of type {} "
                "created with the label {} "
                "by this calculation".format(
                    user_email, data_type_string, link_label))

    # If we are here, we managed to delete the entries from the DB.
    # I can now delete the folders
    for f in folders:
        f.erase()

