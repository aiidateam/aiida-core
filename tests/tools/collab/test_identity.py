###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the identities of a collab: the join code, the roster and the version stamp of an address."""

import pytest

from aiida import get_profile
from aiida.tools.collab.config import (
    OPTION_ANNOUNCED,
    OPTION_BIND,
    OPTION_PORT,
    OPTION_STAMP,
    endpoint_url,
    merge_roster,
    roster_entries,
    self_entry,
)
from aiida.tools.collab.protocol import JoinCode

OWN = 'uuid-of-this-profile'


def entry(uuid='uuid-of-alice', url='http://100.64.0.2:9137', name='alice', stamp=1):
    """Return a gossiped entry, as it travels on the wire."""
    return {'uuid': uuid, 'url': url, 'name': name, 'stamp': stamp}


def held(url='http://100.64.0.2:9137', nickname='alice', **overrides):
    """Return a roster entry, as a completed contact leaves it in the configuration."""
    return {
        'url': url,
        'nickname': nickname,
        'name': nickname,
        'stamp': 1,
        'seen': True,
        **overrides,
    }


def test_join_code_round_trip():
    """Test that a join code carries what a newcomer needs — the collab, the issuer, the key and the terms."""
    code = JoinCode(
        collab='uuid-of-the-collab',
        url='http://[fd7a::2]:9137',
        token='the-token',
        policy={'extras_mode': 'sync', 'groups_mode': 'grow'},
    )

    assert JoinCode.decode(code.encode()) == code


def test_join_code_rejects_nonsense():
    """Test that a mistyped code fails as a value error, which the CLI turns into an error message."""
    with pytest.raises(ValueError, match='not a valid join code'):
        JoinCode.decode('this is not a code')


@pytest.mark.parametrize('policy', [None, {'groups_mode': 'grow'}, {'extras_mode': 'evil', 'groups_mode': 'grow'}])
def test_join_code_rejects_a_policy_it_cannot_honour(policy):
    """Test that a code is refused unless it names a policy this version has, and refused at the boundary.

    A newcomer must not join on terms it was not shown, and a mode nobody offers has to fail here rather than
    where the policy is written — which is after the profile exists, and would leave a half-made one behind.
    """
    import base64
    import json

    payload = {'collab': 'uuid-of-the-collab', 'url': 'http://peer:9137', 'token': 'the-token'}
    code = base64.urlsafe_b64encode(
        json.dumps(payload if policy is None else {**payload, 'policy': policy}).encode('utf-8')
    ).decode('ascii')

    with pytest.raises(ValueError, match='not a valid join code'):
        JoinCode.decode(code.rstrip('='))


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


def test_merge_updates_on_a_higher_stamp_and_discards_a_stale_one():
    """Test the flip-flop: the newer address survives the older one being gossiped back at it.

    Only the owner of an entry raises its stamp, which is what makes "whose information is newer" decidable
    locally — without it two peers would overwrite each other with their own truths forever.
    """
    moved = entry(url='http://100.64.0.9:9137', stamp=2)
    fresh, reports = merge_roster({}, [moved], OWN)

    # A peer that still holds the old address gossips it: the stamp is lower, so it changes nothing here.
    kept, stale_reports = merge_roster(fresh, [entry(stamp=1)], OWN)

    assert kept['uuid-of-alice']['url'] == 'http://100.64.0.9:9137'
    assert stale_reports == []

    # And the other way round, the fresher entry does replace the address the stale peer holds.
    adopted, moved_reports = merge_roster({'uuid-of-alice': held(nickname='ali', name='alice')}, [moved], OWN)

    assert adopted['uuid-of-alice']['url'] == 'http://100.64.0.9:9137'
    assert adopted['uuid-of-alice']['nickname'] == 'ali', 'a local rename survives what its owner announces'
    assert adopted['uuid-of-alice']['seen'] is False, 'the new address is unproven until the peer answers at it'
    assert 'moved' in moved_reports[0]
    assert reports and 'alice' in reports[0]


def test_merge_discards_an_equal_stamp():
    """Test that only a raised stamp supersedes what is held, which is what makes a manual correction stick.

    A peer that has not moved keeps announcing its own URL at the same stamp. If that counted as newer, the
    address a `verdi collab peer set --url` corrected would be undone at the very next contact — and that
    correction is the one write nothing else ever re-applies, since it deliberately never travels.
    """
    corrected = held(url='http://100.64.0.9:9137', seen=False)

    merged, reports = merge_roster({'uuid-of-alice': corrected}, [entry()], OWN)

    assert merged['uuid-of-alice'] == corrected
    assert reports == []


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
    peers = {'uuid-of-alice': held(url='http://one:9137', nickname='ali', name='alice', stamp=3)}

    gossip = roster_entries(peers, entry(uuid=OWN, name='me'))

    assert gossip[1] == {'uuid': 'uuid-of-alice', 'url': 'http://one:9137', 'name': 'alice', 'stamp': 3}


def test_self_entry_stamps_a_changed_address(config_with_profile):
    """Test that the stamp rises exactly when the endpoint URL changed, and not on every announcement."""
    profile = get_profile()
    scope = profile.name
    config = config_with_profile

    config.set_option(OPTION_BIND, '127.0.0.1', scope=scope)
    config.set_option(OPTION_PORT, 9137, scope=scope)
    config.set_option(OPTION_STAMP, 1, scope=scope)
    config.set_option(OPTION_ANNOUNCED, endpoint_url('127.0.0.1', 9137), scope=scope)

    assert self_entry(config, profile, bump=True)['stamp'] == 1

    config.set_option(OPTION_PORT, 9200, scope=scope)
    announcement = self_entry(config, profile, bump=True)

    assert announcement == {
        'uuid': profile.uuid,
        'url': 'http://127.0.0.1:9200',
        'name': profile.name,
        'stamp': 2,
    }
    assert config.get_option(OPTION_ANNOUNCED, scope=scope) == 'http://127.0.0.1:9200'


def test_endpoint_url_brackets_ipv6():
    """Test that an IPv6 literal is spelled as a URL can carry it; the overlays this runs on hand them out."""
    assert endpoint_url('fd7a::2', 9137) == 'http://[fd7a::2]:9137'
    assert endpoint_url('100.64.0.2', 9137) == 'http://100.64.0.2:9137'
