###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the identities of a collab: the join code and the roster."""

import pytest

from aiida.tools.collab.config import (
    endpoint_url,
    merge_roster,
    roster_entries,
)
from aiida.tools.collab.protocol import JoinCode

OWN = 'uuid-of-this-profile'


def entry(uuid='uuid-of-alice', url='http://100.64.0.2:9137', name='alice'):
    """Return a roster entry, as it travels on the wire."""
    return {'uuid': uuid, 'url': url, 'name': name}


def held(url='http://100.64.0.2:9137', nickname='alice', **overrides):
    """Return a roster entry, as a completed contact leaves it in the configuration."""
    return {
        'url': url,
        'nickname': nickname,
        'name': nickname,
        'seen': True,
        **overrides,
    }


def test_join_code_round_trip():
    """Test that a join code carries what a newcomer needs — the collab, the issuer, the key and the terms."""
    code = JoinCode(
        collab='uuid-of-the-collab',
        url='http://[fd7a::2]:9137',
        token='the-token',
    )

    assert JoinCode.decode(code.encode()) == code


def test_join_code_rejects_nonsense():
    """Test that a mistyped code fails as a value error, which the CLI turns into an error message."""
    with pytest.raises(ValueError, match='not a valid join code'):
        JoinCode.decode('this is not a code')


def test_merge_adds_an_unknown_peer():
    """Test that a gossiped peer this profile does not know is added under its own announced name, and reported."""
    merged, reports = merge_roster({}, [entry()], OWN)

    assert merged == {'uuid-of-alice': held(seen=False)}
    assert 'alice' in reports[0]


def test_merge_dedups_a_colliding_nickname():
    """Test that a peer whose announced name is taken locally is stored under a name that is not.

    Nicknames address peers on the command line, so two entries may not share one; across the network the same
    member may be called different things on different machines.
    """
    merged, _ = merge_roster(
        {'uuid-of-the-first': held(url='http://one:9137')}, [entry(uuid='uuid-of-the-second')], OWN
    )

    assert merged['uuid-of-the-second']['nickname'] == 'alice-2'
    assert merged['uuid-of-the-first']['nickname'] == 'alice'


def test_merge_skips_a_malformed_entry():
    """Test that an entry that is not what a roster entry is gets skipped, like an incomplete one.

    Anything a peer runs hands these over, and what gets through lands in the configuration of a command that has
    already imported a delta — so a merge that raised would abort that pull, and every later one from that peer.
    """
    merged, reports = merge_roster({}, [entry(uuid=['not-a-uuid']), entry(uuid='ok', name={'not': 'a name'})], OWN)

    assert list(merged) == ['ok']
    assert merged['ok']['nickname'] == 'ok', 'a nameless entry falls back to its UUID'
    assert len(reports) == 1


def test_merge_ignores_the_entry_of_this_profile():
    """Test that the entry every peer gossips back about this profile is never merged as a peer of it."""
    merged, reports = merge_roster({}, [entry(uuid=OWN)], OWN)

    assert merged == {}
    assert reports == []


def test_roster_entries_carry_the_announced_name_not_the_local_nickname():
    """Test that a local rename does not travel: the name a peer relays is the one its owner announced."""
    peers = {'uuid-of-alice': held(url='http://one:9137', nickname='ali', name='alice')}

    gossip = roster_entries(peers, entry(uuid=OWN, name='me'))

    assert gossip[1] == {'uuid': 'uuid-of-alice', 'url': 'http://one:9137', 'name': 'alice'}


def test_endpoint_url_brackets_ipv6():
    """Test that an IPv6 literal is spelled as a URL can carry it; the overlays this runs on hand them out."""
    assert endpoint_url('fd7a::2', 9137) == 'http://[fd7a::2]:9137'
    assert endpoint_url('100.64.0.2', 9137) == 'http://100.64.0.2:9137'
