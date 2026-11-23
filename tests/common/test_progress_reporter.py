###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the progress reporter protocol and implementations."""

from types import TracebackType
import typing as t
import pytest
from tqdm import tqdm
from typing_extensions import Self

from aiida.common.progress_reporter import (
    ProgressReporter,
    ProgressReporterAbstract,
    ProgressReporterNull,
    create_callback,
    get_progress_reporter,
    set_progress_bar_tqdm,
    set_progress_reporter,
)
from aiida.common.warnings import AiidaDeprecationWarning


class PropertyReporter:
    """A custom reporter using read-only properties satisfying ProgressReporter."""

    def __init__(self, *, total: float | int | None = None, desc: str | None = None, **kwargs: t.Any):
        self._total = total
        self._desc = desc
        self._n: float | int = 0
        self.kwargs = kwargs

    @property
    def total(self) -> float | int | None:
        return self._total

    @property
    def desc(self) -> str | None:
        return self._desc

    @property
    def n(self) -> float | int:
        return self._n

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exctype: type[BaseException] | None,
        excinst: BaseException | None,
        exctb: TracebackType | None,
    ) -> bool | None:
        return False

    def set_description_str(self, text: str | None = None, /, refresh: bool = True) -> None:
        self._desc = text

    def update(self, n: float | int = 1) -> bool | None:
        self._n += n
        return None

    def reset(self, total: float | int | None = None) -> None:
        self._n = 0
        if total is not None:
            self._total = total


class PlainAttributeReporter:
    """A reporter with plain attributes (like tqdm) satisfying ProgressReporter."""

    def __init__(self, *, total: float | int | None = None, desc: str | None = None, **kwargs: t.Any):
        self.total: float | int | None = total
        self.desc: str | None = desc
        self.n: float | int = 0
        self.kwargs = kwargs

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exctype: type[BaseException] | None,
        excinst: BaseException | None,
        exctb: TracebackType | None,
    ) -> bool | None:
        return False

    def set_description_str(self, text: str | None = None, /, refresh: bool = True) -> None:
        self.desc = text

    def update(self, n: float | int = 1) -> bool | None:
        self.n += n
        return None

    def reset(self, total: float | int | None = None) -> None:
        self.n = 0
        if total is not None:
            self.total = total


class IncompleteReporter:
    """A reporter missing required protocol methods."""

    def __init__(self, *, total: int | None = None, desc: str | None = None):
        self.total = total
        self.desc = desc
        self.n = 0


def test_progress_reporter_protocol_conformance():
    """Verify that compliant classes and instances satisfy the ProgressReporter protocol."""
    null_reporter = ProgressReporterNull(total=10, desc='Test')
    assert isinstance(null_reporter, ProgressReporter)

    prop_reporter = PropertyReporter(total=10, desc='Test')
    assert isinstance(prop_reporter, ProgressReporter)

    plain_reporter = PlainAttributeReporter(total=10, desc='Test')
    assert isinstance(plain_reporter, ProgressReporter)

    tqdm_reporter = tqdm(total=10, desc='Test')
    try:
        assert isinstance(tqdm_reporter, ProgressReporter)
    finally:
        tqdm_reporter.close()

    incomplete = IncompleteReporter(total=10, desc='Test')
    assert not isinstance(incomplete, ProgressReporter)


def test_progress_reporter_null():
    """Verify the default ProgressReporterNull behavior and context manager contract."""
    reporter = ProgressReporterNull(total=5, desc='Process')
    assert reporter.total == 5
    assert reporter.desc == 'Process'
    assert reporter.n == 0

    with reporter as p:
        assert p is reporter
        p.update()
        assert p.n == 1
        p.update(3)
        assert p.n == 4
        p.set_description_str('Updated Process')
        assert p.desc == 'Updated Process'
        p.set_description_str(desc='Keyword Desc')
        assert p.desc == 'Keyword Desc'
        p.set_description_str(text='Keyword Text')
        assert p.desc == 'Keyword Text'
        p.reset(total=10)
        assert p.n == 0
        assert p.total == 10
        p.reset()
        assert p.n == 0
        assert p.total == 10


def test_progress_reporter_abstract_deprecation(monkeypatch):
    """Verify that using the legacy ProgressReporterAbstract emits an AiidaDeprecationWarning."""
    monkeypatch.setenv('AIIDA_WARN_v3', 'true')

    with pytest.warns(AiidaDeprecationWarning, match=r'`ProgressReporterAbstract` is deprecated'):
        class LegacySubclass(ProgressReporterAbstract):
            pass

    with pytest.warns(AiidaDeprecationWarning, match=r'`ProgressReporterAbstract` is deprecated'):
        instance = ProgressReporterAbstract(total=10, desc='Legacy')

    assert isinstance(instance, ProgressReporter)
    instance.update(2)
    assert instance.n == 2


def test_set_and_get_progress_reporter():
    """Verify set_progress_reporter and get_progress_reporter lifecycle."""
    try:
        set_progress_reporter(PropertyReporter, extra_param='test_val')
        reporter_cls = get_progress_reporter()
        with reporter_cls(total=10, desc='Testing') as p:
            assert isinstance(p, PropertyReporter)
            assert p.kwargs.get('extra_param') == 'test_val'
            assert p.total == 10

        set_progress_reporter(None)
        assert get_progress_reporter() is ProgressReporterNull
    finally:
        set_progress_reporter(None)


def test_set_progress_bar_tqdm():
    """Verify set_progress_bar_tqdm configures a partial tqdm reporter."""
    try:
        set_progress_bar_tqdm(leave=True)
        reporter_cls = get_progress_reporter()
        with reporter_cls(total=5, desc='Tqdm bar') as p:
            assert isinstance(p, ProgressReporter)
            assert isinstance(p, tqdm)
    finally:
        set_progress_reporter(None)


def test_create_callback():
    """Verify create_callback correctly relays 'init' and 'update' actions."""
    reporter = ProgressReporterNull(total=10, desc='Initial')
    callback = create_callback(reporter)

    callback('init', {'total': 25, 'description': 'Phase 2'})
    assert reporter.total == 25
    assert reporter.desc == 'Phase 2'
    assert reporter.n == 0

    callback('update', 7)
    assert reporter.n == 7
