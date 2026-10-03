###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for utilities that extend the Python language."""

import pytest

from aiida.common.lang import call_with_super_check, super_check


class Root:
    @super_check
    def method(self) -> None:
        pass

    def invoke(self) -> None:
        call_with_super_check(self.method)


class CallsSuper(Root):
    def method(self) -> None:
        super().method()


class DoesNotCallSuper(Root):
    def method(self) -> None:
        pass


def test_super_check() -> None:
    CallsSuper().invoke()


def test_super_check_missing_super() -> None:
    with pytest.raises(AssertionError, match='Did you forget to call the super'):
        DoesNotCallSuper().invoke()


def test_super_check_without_checked_call() -> None:
    with pytest.raises(AssertionError, match='was not called through call_with_super_check'):
        CallsSuper().method()
