# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Bring schema inline with psql_dos main_0001

Revision ID: main_0001
Revises:
Create Date: 2021-02-02

"""
revision = 'main_0001'
down_revision = 'main_0000b'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of main_0001.')
