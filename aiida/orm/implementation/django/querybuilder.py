# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django query builder implementation"""
from aiida.backends.djsite.db import models
from aiida.orm.implementation.sqlalchemy.querybuilder import SqlaQueryBuilder


class DjangoQueryBuilder(SqlaQueryBuilder):
    """Django query builder

    With the Django backend, we actually still use SQLAlchemy, since Django does not support complex queries.
    We use aldjemy to generate SQLAlchemy models by introspecting the Django models.
    """

    def set_field_mappings(self):
        pass

    @property
    def Node(self):
        return models.DbNode.sa  # pylint: disable=no-member

    @property
    def Link(self):
        return models.DbLink.sa  # pylint: disable=no-member

    @property
    def Computer(self):
        return models.DbComputer.sa  # pylint: disable=no-member

    @property
    def User(self):
        return models.DbUser.sa  # pylint: disable=no-member

    @property
    def Group(self):
        return models.DbGroup.sa  # pylint: disable=no-member

    @property
    def AuthInfo(self):
        return models.DbAuthInfo.sa  # pylint: disable=no-member

    @property
    def Comment(self):
        return models.DbComment.sa  # pylint: disable=no-member

    @property
    def Log(self):
        return models.DbLog.sa  # pylint: disable=no-member

    @property
    def table_groups_nodes(self):
        return models.DbGroup.sa.table.metadata.tables['db_dbgroup_dbnodes']  # pylint: disable=no-member

    def modify_expansions(self, alias, expansions):
        """
        For django, there are no additional expansions for now, so
        I am returning an empty list
        """
        return expansions

    @staticmethod
    def get_table_name(aliased_class):
        """Returns the table name given an Aliased class based on Aldjemy"""
        return aliased_class._aliased_insp._target.table.name  # pylint: disable=protected-access

    def get_column_names(self, alias):
        """
        Given the backend specific alias, return the column names that correspond to the aliased table.
        """
        # pylint: disable=protected-access
        return [
            str(c).replace(f'{alias._aliased_insp.class_.table.name}.', '')
            for c in alias._aliased_insp.class_.table._columns._all_columns
        ]
