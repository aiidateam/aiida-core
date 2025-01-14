###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.array.bands` module."""

import uuid
from argparse import Namespace

import pytest

from aiida.common.exceptions import NotExistent
from aiida.orm import BandsData, Group, User
from aiida.orm.nodes.data.array.bands import get_bands_and_parents_structure


@pytest.fixture
def alternate_user():
    """Return an alternate ``User`` instance that is not the current default user."""
    email = 'alternate@localhost'
    try:
        return User.collection.get(email=email)
    except NotExistent:
        return User(email='alternate@localhost').store()


class TestGetBandsAndParentsStructure:
    """Tests for the :meth:`~aiida.orm.nodes.data.array.bands.get_bands_and_parents_structure` function."""

    @staticmethod
    def _get_default_ns():
        """Returns a simple template Namespace"""
        args = Namespace()
        args.element = None
        args.element_only = None
        args.formulamode = None
        args.past_days = None
        args.group_name = None
        args.group_pk = None
        args.all_users = False
        return args

    @pytest.mark.parametrize('all_users, expected', ((True, [True, True]), (False, [True, False])))
    def test_all_users(self, alternate_user, all_users, expected):
        """Test the behavior for the ``all_users`` argument."""
        bands_default_user = BandsData().store()
        bands_alternate_user = BandsData(user=alternate_user).store()
        bands = [bands_default_user, bands_alternate_user]

        args = self._get_default_ns()
        args.all_users = all_users

        entries = get_bands_and_parents_structure(args)
        node_pks = [int(e[0]) for e in entries]
        assert [node.pk in node_pks for node in bands] == expected

    @pytest.mark.parametrize('argument, attribute', (('group_name', 'label'), ('group_pk', 'pk')))
    def test_identifier(self, argument, attribute):
        """Test the behavior for the ``group_name`` and ``group_pk`` arguments."""
        bands_data_grouped = BandsData().store()
        _ = BandsData().store()
        bands_group = Group(uuid.uuid4().hex).store()
        bands_group.add_nodes(bands_data_grouped)

        args = self._get_default_ns()
        setattr(args, argument, [getattr(bands_group, attribute)])

        entries = get_bands_and_parents_structure(args)
        assert [int(e[0]) for e in entries] == [bands_data_grouped.pk]
