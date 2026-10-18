from __future__ import annotations

import dataclasses
import os
import pathlib
import typing as t
from collections.abc import Callable, Mapping

__all__ = (
    'RepoFiles',
    'RepoSource',
    'RepoSourceCliInput',
    'iter_repo_sources',
    'repo_source',
)

if t.TYPE_CHECKING:
    from aiida.orm.cli import CliAdapter, CliFieldInfo
    from aiida.orm.nodes.node import Node

RepoFiles = dict[str, Callable[[], t.BinaryIO | None]]

_NodeT = t.TypeVar('_NodeT', bound='Node')
_ValueT = t.TypeVar('_ValueT')


@dataclasses.dataclass(frozen=True)
class RepoSourceCliInput:
    """One CLI representation of a repository source."""

    name: str
    adapter: CliAdapter[t.Any, t.Any] | None = None
    annotation: t.Any = None
    mapper: (
        Callable[
            [t.Any, Mapping[str, t.Any]],
            Mapping[str, Callable[[], t.BinaryIO | None]],
        ]
        | None
    ) = None
    cli_field_info: CliFieldInfo | None = None
    multiple: bool = False
    nargs: int | None = None
    required: bool = False

    def __post_init__(self) -> None:
        if self.adapter is None and self.annotation is None:
            raise ValueError('a repository source CLI input requires an adapter or a Click type')

    def to_files(self, value: t.Any, *, context: Mapping[str, t.Any] | None = None) -> RepoFiles:
        """Convert one CLI value to repository files."""
        if self.adapter is not None:
            value = self.adapter.to_model(value)

        if self.mapper is not None:
            value = self.mapper(value, context if context is not None else {})

        if not isinstance(value, Mapping):
            msg = f'CLI input `{self.name}` must map to a mapping of repository paths to file openers'
            raise TypeError(msg)

        return dict(value)


@dataclasses.dataclass(frozen=True)
class _RepoSourceConfig:
    cli_inputs: tuple[RepoSourceCliInput, ...]
    min_files: int
    max_files: int | None
    validator: Callable[[Mapping[str, Callable[[], t.BinaryIO | None]]], None] | None
    interactive_collector: Callable[[], Mapping[str, t.Any]] | None


class RepoSource(t.Generic[_NodeT, _ValueT]):
    """Descriptor for a value backed by a Node repository."""

    def __init__(
        self,
        fget: Callable[[_NodeT], _ValueT],
        *,
        cli_inputs: tuple[RepoSourceCliInput, ...],
        min_files: int,
        max_files: int | None,
        validator: Callable[[Mapping[str, Callable[[], t.BinaryIO | None]]], None] | None,
        interactive_collector: Callable[[], Mapping[str, t.Any]] | None,
    ) -> None:
        self.fget = fget
        self.__doc__ = getattr(fget, '__doc__', None)
        self._name: str | None = None
        self._owner: type[_NodeT] | None = None
        self._config = _RepoSourceConfig(
            cli_inputs=cli_inputs,
            min_files=min_files,
            max_files=max_files,
            validator=validator,
            interactive_collector=interactive_collector,
        )

    def __set_name__(self, owner: type[_NodeT], name: str) -> None:
        self._name = name
        self._owner = owner

    @t.overload
    def __get__(self, instance: None, owner: type[_NodeT]) -> RepoSource[_NodeT, _ValueT]: ...

    @t.overload
    def __get__(self, instance: _NodeT, owner: type[_NodeT] | None = None) -> _ValueT: ...

    def __get__(
        self,
        instance: _NodeT | None,
        owner: type[_NodeT] | None = None,
    ) -> RepoSource[_NodeT, _ValueT] | _ValueT:
        if instance is None:
            return self

        return self.fget(instance)

    def __set__(self, instance: _NodeT, value: _ValueT) -> t.NoReturn:
        if self._name is None or self._owner is None:
            raise RuntimeError('repository source has not been assigned to a class')

        msg = f'{self._owner.__name__}.{self._name} is read-only'
        raise AttributeError(msg)

    @property
    def name(self) -> str:
        """Return the declared source name."""
        if self._name is None:
            raise RuntimeError('repository source has not been assigned to a class')

        return self._name

    @property
    def cli_inputs(self) -> tuple[RepoSourceCliInput, ...]:
        """Return the CLI input forms for this source."""
        return self._config.cli_inputs

    @property
    def interactive_collector(self) -> Callable[[], Mapping[str, t.Any]] | None:
        """Return the interactive collector for this source, if any."""
        return self._config.interactive_collector

    def validate_files(self, files: Mapping[str, Callable[[], t.BinaryIO | None]]) -> None:
        """Validate repository files against this source's constraints."""
        file_paths = list(files)

        if len(file_paths) < self._config.min_files:
            msg = f'{self.name} requires at least {self._config.min_files} repository file(s)'
            raise ValueError(msg)

        if self._config.max_files is not None and len(file_paths) > self._config.max_files:
            msg = f'{self.name} accepts at most {self._config.max_files} repository file(s)'
            raise ValueError(msg)

        if self._config.validator is not None:
            self._config.validator(files)


def repo_source(
    *,
    cli_inputs: tuple[RepoSourceCliInput, ...] = (),
    min_files: int = 0,
    max_files: int | None = None,
    validator: Callable[[Mapping[str, Callable[[], t.BinaryIO | None]]], None] | None = None,
    interactive_collector: Callable[[], Mapping[str, t.Any]] | None = None,
) -> Callable[[Callable[[_NodeT], _ValueT]], RepoSource[_NodeT, _ValueT]]:
    """Declare a repository-backed Node value and its CLI input forms."""
    if min_files < 0:
        raise ValueError('min_files must be non-negative')

    if max_files is not None and max_files < min_files:
        raise ValueError('max_files must be greater than or equal to min_files')

    names = [cli_input.name for cli_input in cli_inputs]
    if len(names) != len(set(names)):
        raise ValueError('repository source CLI input names must be unique')

    def decorator(fget: Callable[[_NodeT], _ValueT]) -> RepoSource[_NodeT, _ValueT]:
        return RepoSource(
            fget,
            cli_inputs=cli_inputs,
            min_files=min_files,
            max_files=max_files,
            validator=validator,
            interactive_collector=interactive_collector,
        )

    return decorator


def iter_repo_sources(entity: type) -> dict[str, RepoSource[t.Any, t.Any]]:
    """Return all effective repository sources on an entity hierarchy."""
    result: dict[str, RepoSource[t.Any, t.Any]] = {}

    for base in reversed(entity.__mro__):
        for name, value in vars(base).items():
            if isinstance(value, RepoSource):
                result[name] = value
            elif name in result:
                del result[name]

    return result


def file_to_repo_files(
    filepath: pathlib.Path,
    _context: Mapping[str, t.Any],
    *,
    destination: str | None = None,
) -> RepoFiles:
    """Map one local file to a repository file with the same basename."""
    if not filepath.is_file():
        msg = f'`{filepath}` is not a file'
        raise ValueError(msg)

    return {destination or filepath.name: _open_binary_file(filepath)}


def directory_to_repo_files(directory: pathlib.Path, _context: Mapping[str, t.Any]) -> RepoFiles:
    """Map a local directory tree to repository paths relative to its root."""
    if not directory.is_dir():
        msg = f'`{directory}` is not a directory'
        raise ValueError(msg)

    files: RepoFiles = {}

    for root, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        filenames.sort()
        root_path = pathlib.Path(root)

        if root_path != directory and not dirnames and not filenames:
            relative = root_path.relative_to(directory).as_posix()
            files[relative] = _empty_directory

        for filename in filenames:
            filepath = root_path / filename
            relative = filepath.relative_to(directory).as_posix()
            files[relative] = _open_binary_file(filepath)

    return files


def _open_binary_file(filepath: pathlib.Path) -> Callable[[], t.BinaryIO]:
    """Return an opener for a local file."""

    def opener() -> t.BinaryIO:
        return filepath.open('rb')

    return opener


def _empty_directory() -> None:
    """Mark a repository path as an empty directory."""
    return None
