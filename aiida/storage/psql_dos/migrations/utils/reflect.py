# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility for performing schema migrations, via reflection of the current database."""
from __future__ import annotations

import alembic
from sqlalchemy import inspect


class ReflectMigrations:
    """Perform schema migrations, via reflection of the current database.

    In django, it is not possible to explicitly specify constraints/indexes and their names,
    instead they are implicitly created by internal "auto-generation" code
    (as opposed to sqlalchemy, where one can explicitly specify the names).
    For a specific django version, this auto-generation code is deterministic,
    however, over time it has changed.
    So is not possible to know declaratively exactly what constraints/indexes are present on a users database,
    withtout knowing the exact django version that created it (and run migrations).
    Therefore, we need to reflect the database's schema, to determine what is present on the database,
    to know what to drop.
    """

    def __init__(self, op: alembic.op) -> None:
        self.op = op  # pylint: disable=invalid-name
        # note, we only want to instatiate the inspector once, since it caches reflection calls to the database
        self.inspector = inspect(op.get_bind())

    def reset_cache(self) -> None:
        """Reset the inspector cache."""
        self.inspector = inspect(self.op.get_bind())

    def drop_all_unique_constraints(self, table_name: str) -> None:
        """Drop all unique constraints set for this table."""
        for constraint in self.inspector.get_unique_constraints(table_name):
            self.op.drop_constraint(constraint['name'], table_name, type_='unique')

    def drop_unique_constraints(self, table_name: str, column_names: list[str]) -> None:
        """Drop all unique constraints set for this column name group."""
        column_set = set(column_names)
        for constraint in self.inspector.get_unique_constraints(table_name):
            if set(constraint['column_names']) == column_set:
                self.op.drop_constraint(constraint['name'], table_name, type_='unique')

    def drop_all_indexes(self, table_name: str, unique: bool = False) -> None:
        """Drop all non-unique indexes set for this table."""
        for index in self.inspector.get_indexes(table_name):
            if index['unique'] is unique:
                self.op.drop_index(index['name'], table_name)

    def drop_indexes(self, table_name: str, column: str | list[str], unique: bool = False) -> None:
        """Drop all indexes set for this column name group."""
        if isinstance(column, str):
            column = [column]
        column_set = set(column)
        for index in self.inspector.get_indexes(table_name):
            if (index['unique'] is unique) and (set(index['column_names']) == column_set):
                self.op.drop_index(index['name'], table_name)

    def drop_all_foreign_keys(self, table_name: str) -> None:
        """Drop all foreign keys set for this table."""
        for constraint in self.inspector.get_foreign_keys(table_name):
            self.op.drop_constraint(constraint['name'], table_name, type_='foreignkey')

    def drop_foreign_keys(self, table_name: str, columns: list[str], ref_tbl: str, ref_columns: list[str]) -> None:
        """Drop all foreign keys set for this column name group and referring column set."""
        column_set = set(columns)
        ref_column_set = set(ref_columns)
        for constraint in self.inspector.get_foreign_keys(table_name):
            if constraint['referred_table'] != ref_tbl:
                continue
            if set(constraint['referred_columns']) != ref_column_set:
                continue
            if set(constraint['constrained_columns']) == column_set:
                self.op.drop_constraint(constraint['name'], table_name, type_='foreignkey')

    def replace_index(self, label: str, table_name: str, column: str, unique: bool = False) -> None:
        """Create index, dropping any existing index with the same table+columns."""
        self.drop_indexes(table_name, column, unique)
        self.op.create_index(label, table_name, column, unique=unique)

    def replace_unique_constraint(self, label: str, table_name: str, columns: list[str]) -> None:
        """Create unique constraint, dropping any existing unique constraint with the same table+columns."""
        self.drop_unique_constraints(table_name, columns)
        self.op.create_unique_constraint(label, table_name, columns)

    def replace_foreign_key(
        self, label: str, table_name: str, columns: list[str], ref_tbl: str, ref_columns: list[str], **kwargs
    ) -> None:
        """Create foreign key, dropping any existing foreign key with the same constraints."""
        self.drop_foreign_keys(table_name, columns, ref_tbl, ref_columns)
        self.op.create_foreign_key(label, table_name, ref_tbl, columns, ref_columns, **kwargs)
