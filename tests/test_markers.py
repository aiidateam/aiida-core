"""Tests markers that have custom in conftest.py"""

import pytest


def test_presto_auto_mark(request):
    """Test that the presto marker is added automatically"""
    own_markers = [marker.name for marker in request.node.own_markers]
    assert len(own_markers) == 1
    assert own_markers[0] == 'presto'


@pytest.mark.sphinx
def test_presto_mark_and_another_mark(request):
    """Test that presto marker is added even if there is an existing marker (except requires_rmq|psql)"""
    own_markers = [marker.name for marker in request.node.own_markers]

    assert len(own_markers) == 2
    assert 'presto' in own_markers
    assert 'sphinx' in own_markers


@pytest.mark.requires_rmq
def test_no_presto_mark_if_rmq(request):
    """Test that presto marker is NOT added if the test is mark with "requires_rmq"""
    own_markers = [marker.name for marker in request.node.own_markers]

    assert len(own_markers) == 1
    assert own_markers[0] == 'requires_rmq'


@pytest.mark.requires_psql
def test_no_presto_mark_if_psql(request):
    """Test that presto marker is NOT added if the test is mark with "requires_psql"""
    own_markers = [marker.name for marker in request.node.own_markers]

    assert len(own_markers) == 1
    assert own_markers[0] == 'requires_psql'


@pytest.mark.nightly
def test_no_presto_mark_if_nightly(request):
    """Test that presto marker is NOT added if the test is mark with "requires_psql"""
    own_markers = [marker.name for marker in request.node.own_markers]

    assert len(own_markers) == 1
    assert own_markers[0] == 'nightly'


@pytest.mark.requires_psql
def test_requires_psql_with_sqlite_impossible(pytestconfig):
    db_backend = pytestconfig.getoption('--db-backend')
    if db_backend.value == 'sqlite':
        pytest.fail('This test should not have been executed with SQLite backend!')


def test_daemon_client_fixture_automarked(request, daemon_client):
    """Test that any test using ``daemon_client`` fixture is
    automatically tagged with 'requires_rmq' mark
    """
    own_markers = [marker.name for marker in request.node.own_markers]

    assert len(own_markers) == 1
    assert own_markers[0] == 'requires_rmq'
