###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for Path types"""

import click
import pytest

from aiida.cmdline.params.types.path import PathOrUrl, check_timeout_seconds


def test_default_timeout():
    """Test the default timeout_seconds value is correct"""
    from aiida.cmdline.params.types.path import URL_TIMEOUT_SECONDS

    import_path = PathOrUrl()

    assert import_path.timeout_seconds == URL_TIMEOUT_SECONDS


def test_timeout_checks():
    """Test that timeout check handles different values.

    * valid
    * none
    * wrong type
    * outside range
    """
    valid_values = [42, '42']

    for value in valid_values:
        assert check_timeout_seconds(value) == int(value)

    for invalid in [None, 'test']:
        with pytest.raises(TypeError):
            check_timeout_seconds(invalid)

    for invalid in [-5, 65]:
        with pytest.raises(ValueError):
            check_timeout_seconds(invalid)


def test_fail_non_existing_path():
    """Test the parameter for a non-existing path when ``exists=True``."""
    with pytest.raises(
        click.BadParameter, match=r'.*does not correspond to a file and also could not be reached as a URL.'
    ):
        PathOrUrl(exists=True).convert('non-existent.txt', None, None)


def test_fail_non_readable_path(tmp_path):
    """Test that if the path exists but cannot be read, the parameter does not try to treat it as a URL."""
    filepath = tmp_path / 'some_file'
    filepath.touch()
    filepath.chmod(0o333)  # Make it writable and executable only, so it is not readable

    with pytest.raises(click.BadParameter, match=r'.*exists but could not be read.'):
        PathOrUrl(exists=True).convert(str(filepath), None, None)


def test_fail_unreachable_url():
    """Test the parameter in case of a valid URL that cannot be reached."""
    # TODO: Mock the request to make this faster
    with pytest.raises(click.BadParameter, match=r'.* could not be reached.'):
        PathOrUrl(exists=True).convert('http://domain/some/path', None, None)


def test_fail_timeout(monkeypatch):
    """Test the parameter in case of a valid URL that times out."""
    import socket
    from urllib import request

    def raise_timeout(*args, **kwargs):
        raise socket.timeout

    monkeypatch.setattr(request, 'urlopen', raise_timeout)

    with pytest.raises(click.BadParameter, match=r'.* could not be reached within .* seconds.'):
        PathOrUrl(exists=True).convert('http://domain/some/pat', None, None)
