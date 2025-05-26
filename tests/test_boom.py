import pytest


@pytest.mark.nightly
@pytest.mark.requires_rmq
def test_boom():
    assert False, 'BOOM!'


def test_boom_boom():
    assert False, 'BIGGER BOOM!'
