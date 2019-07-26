# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Utility functions specific to the SqlAlchemy backend."""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function


def flag_modified(instance, key):
    """Wrapper around `sqlalchemy.orm.attributes.flag_modified` to correctly dereference utils.ModelWrapper

    Since SqlAlchemy 1.2.12 (and maybe earlier but not in 1.0.19) the flag_modified function will check that the
    key is actually present in the instance or it will except. If we pass a model instance, wrapped in the ModelWrapper
    the call will raise an InvalidRequestError. In this function that wraps the flag_modified of SqlAlchemy, we
    derefence the model instance if the passed instance is actually wrapped in the ModelWrapper.
    """
    from sqlalchemy.orm.attributes import flag_modified as flag_modified_sqla
    from aiida.orm.implementation.sqlalchemy.utils import ModelWrapper

    if isinstance(instance, ModelWrapper):
        instance = instance._model  # pylint: disable=protected-access

    flag_modified_sqla(instance, key)


def delete_nodes_and_connections_sqla(pks_to_delete):  # pylint: disable=invalid-name
    """
    Delete all nodes corresponding to pks in the input.
    :param pks_to_delete: A list, tuple or set of pks that should be deleted.
    """
    # pylint: disable=no-value-for-parameter
    from aiida.backends.sqlalchemy.models.node import DbNode, DbLink
    from aiida.backends.sqlalchemy.models.group import table_groups_nodes
    from aiida.manage.manager import get_manager

    backend = get_manager().get_backend()

    with backend.transaction() as session:
        # I am first making a statement to delete the membership of these nodes to groups.
        # Since table_groups_nodes is a sqlalchemy.schema.Table, I am using expression language to compile
        # a stmt to be executed by the session. It works, but it's not nice that two different ways are used!
        # Can this be changed?
        stmt = table_groups_nodes.delete().where(table_groups_nodes.c.dbnode_id.in_(list(pks_to_delete)))
        session.execute(stmt)
        # First delete links, then the Nodes, since we are not cascading deletions.
        # Here I delete the links coming out of the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.input_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Here I delete the links pointing to the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.output_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Now I am deleting the nodes
        session.query(DbNode).filter(DbNode.id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
