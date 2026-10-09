###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Persistent input descriptions and reconciliation of interrupted CalcJob uploads."""

from __future__ import annotations

import hashlib
import os
import stat
import typing as t
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from logging import LoggerAdapter
from pathlib import Path, PurePosixPath

from typing_extensions import assert_never

from aiida.common.datastructures import CalcInfo, FileCopyOperation
from aiida.common.exceptions import InvalidOperation, NotExistent
from aiida.common.hashing import chunked_file_hash
from aiida.orm import CalcJobNode, Node, PortableCode, load_node
from aiida.repository.common import FileType
from aiida.transports import Transport
from aiida.transports.transport import has_magic
from aiida.transports.util import run_file_io


def find_data_node(inputs: Mapping[str, t.Any], uuid: str) -> Node | None:
    """Find a source node in nested process inputs, including unstored dry-run inputs."""
    for value in inputs.values():
        if isinstance(value, Mapping):
            result = find_data_node(value, uuid)
            if result is not None:
                return result
        elif isinstance(value, Node) and value.uuid == uuid:
            return value
    return None


def load_source(uuid: str, inputs: Mapping[str, t.Any] | None) -> Node:
    """Resolve a source only for the immediate repository operation."""
    try:
        return load_node(uuid)
    except NotExistent:
        node = find_data_node(inputs, uuid) if inputs else None
        if node is None:
            raise
        return node


@dataclass
class Entry:
    """An expected destination, with a durable source reference rather than staged file contents."""

    kind: t.Literal['directory', 'file', 'symlink']
    source: t.Literal['sandbox', 'repository', 'remote', 'none'] = 'none'
    path: str = ''
    uuid: str = ''
    checksum: str = ''
    target: str = ''
    mode: int | None = None


class Manifest(t.TypedDict):
    """Versioned operational state stored on the CalcJob, separate from scientific input repositories."""

    version: int
    request: dict[str, t.Any]
    entries: dict[str, dict[str, t.Any]]
    verified: list[str]


def relative_path(path: str) -> str:
    """Normalize a destination while rejecting paths outside the calculation directory."""
    normalized = PurePosixPath(os.path.normpath(path or '.'))
    if normalized.is_absolute() or '..' in normalized.parts:
        msg = f'Upload destination must remain inside the work directory: {path}'
        raise ValueError(msg)
    return str(normalized)


def sandbox_entries(folder: Path) -> dict[str, Entry]:
    """Read and hash sandbox files in a worker thread, following the usual upload symlink semantics."""
    entries = {'.': Entry('directory')}
    for root, directories, files in os.walk(folder, followlinks=True):
        resolved = Path(root).resolve()
        relative_root = Path(root).relative_to(folder)
        ancestors = [
            (folder / Path(*relative_root.parts[:depth])).resolve() for depth in range(len(relative_root.parts))
        ]
        if resolved in ancestors:
            msg = f'Cycle while following sandbox symlinks: {root}'
            raise ValueError(msg)
        for name in directories:
            entries[str((Path(root) / name).relative_to(folder))] = Entry('directory')
        for name in files:
            path = Path(root) / name
            relative = str(path.relative_to(folder))
            with path.open('rb') as handle:
                digest = chunked_file_hash(handle, hashlib.sha256)
            entries[relative] = Entry('file', source='sandbox', path=relative, checksum=digest)
    return entries


class Plan:
    """Resolve copy ordering against the expected tree, never against leftovers from an earlier attempt."""

    def __init__(self, transport: Transport) -> None:
        self.transport = transport
        self.entries: dict[str, Entry] = {'.': Entry('directory')}

    def directory(self, destination: str) -> None:
        destination = relative_path(destination)
        if destination in self.entries:
            if self.entries[destination].kind != 'directory':
                msg = f'Upload directory conflicts with a file or symlink: {destination}'
                raise NotADirectoryError(msg)
            return
        self.directory(str(PurePosixPath(destination).parent))
        self.entries[destination] = Entry('directory')

    def add(self, destination: str, entry: Entry) -> None:
        destination = relative_path(destination)
        if entry.kind == 'directory':
            self.directory(destination)
            return
        previous = self.entries.get(destination)
        if previous is not None and previous.kind == 'directory':
            raise IsADirectoryError(destination)
        if previous is not None and previous.kind == 'symlink':
            msg = f'An upload would overwrite a previously requested symlink: {destination}'
            raise InvalidOperation(msg)
        self.directory(str(PurePosixPath(destination).parent))
        if previous is not None and entry.mode is None:
            entry.mode = previous.mode
        self.entries[destination] = entry

    def repository(self, uuid: str, source: str, destination: str, inputs: Mapping[str, t.Any] | None = None) -> None:
        node = load_source(uuid, inputs)
        repository = node.base.repository
        source = source or '.'
        destination = relative_path(destination)
        if repository.get_object(source).file_type == FileType.FILE:
            self.add(destination, Entry('file', source='repository', path=source, uuid=uuid))
            return
        self.directory(destination)
        for root, directories, files in repository.walk(source):
            relative = PurePosixPath(root).relative_to(source)
            for name in directories:
                self.directory(str(PurePosixPath(destination) / relative / name))
            for name in files:
                self.add(
                    str(PurePosixPath(destination) / relative / name),
                    Entry('file', source='repository', path=str(PurePosixPath(root) / name), uuid=uuid),
                )

    async def remote_tree(self, source: str, destination: str, *, preserve_link: bool = False) -> None:
        attributes = await self.transport.get_attribute_async(source)
        mode = attributes['st_mode']
        if stat.S_ISLNK(mode) and preserve_link:
            self.add(destination, Entry('symlink', target=await self.transport.readlink_async(source)))
        elif await self.transport.isdir_async(source):
            self.directory(destination)
            for name in sorted(await self.transport.listdir_async(source)):
                await self.remote_tree(
                    str(PurePosixPath(source) / name), str(PurePosixPath(destination) / name), preserve_link=True
                )
        elif await self.transport.isfile_async(source):
            self.add(
                destination,
                Entry('file', source='remote', path=source, mode=stat.S_IMODE(mode) if stat.S_ISREG(mode) else None),
            )
        else:
            msg = f'Cannot upload non-regular remote source: {source}'
            raise OSError(msg)

    async def remote_copy(self, source: str, destination: str) -> None:
        destination = relative_path(destination)
        sources = await self.transport.glob_async(source) if has_magic(source) else [source]
        if not sources:
            raise FileNotFoundError(source)
        if len(sources) > 1 and self.entries.get(destination, Entry('file')).kind != 'directory':
            msg = "Can't copy more than one file in the same destination file"
            raise OSError(msg)
        for path in sources:
            target = destination
            if self.entries.get(target, Entry('file')).kind == 'directory':
                target = str(PurePosixPath(target) / PurePosixPath(path).name)
            if str(PurePosixPath(target).parent) not in self.entries:
                # Remote copy has historically ignored a missing destination parent.
                raise FileNotFoundError(target)
            await self.remote_tree(path, target)


async def source_checksum(
    entry: Entry, folder: Path, transport: Transport, inputs: Mapping[str, t.Any] | None = None
) -> str:
    """Read a source in place without making a staging copy."""
    if entry.source == 'remote':
        return await transport.get_file_checksum_async(entry.path)
    if entry.source == 'repository':
        with load_source(entry.uuid, inputs).base.repository.open(entry.path, 'rb') as handle:
            return await run_file_io(chunked_file_hash, handle, hashlib.sha256)
    with (folder / entry.path).open('rb') as handle:
        return await run_file_io(chunked_file_hash, handle, hashlib.sha256)


async def prepare_manifest(
    node: CalcJobNode,
    transport: Transport,
    calc_info: CalcInfo,
    folder: Path,
    workdir: Path,
    logger: LoggerAdapter,
    inputs: Mapping[str, t.Any] | None = None,
) -> Manifest:
    """Persist the final expected inputs before transferring any bytes.

    A retry uses the original remote tree and checksums. A remote source is only needed again when its destination
    needs repair. Regenerated sandbox inputs must still match, including files stored solely for provenance.
    """
    sandbox = await run_file_io(sandbox_entries, folder)
    computer = node.computer
    assert computer is not None
    codes_info = calc_info.codes_info or []
    order = calc_info.file_copy_operation_order or [
        FileCopyOperation.SANDBOX,
        FileCopyOperation.LOCAL,
        FileCopyOperation.REMOTE,
    ]
    request = {
        'computer': computer.uuid,
        'workdir': str(workdir),
        'codes': [info.code_uuid for info in codes_info],
        'sandbox': {path: asdict(entry) for path, entry in sandbox.items()},
        'local': [list(item) for item in calc_info.local_copy_list or []],
        'remote': [list(item) for item in calc_info.remote_copy_list or []],
        'symlinks': [list(item) for item in calc_info.remote_symlink_list or []],
        'order': [operation.value for operation in order],
    }
    previous = node.base.attributes.get(node.UPLOAD_MANIFEST_KEY, None)
    if previous is not None:
        if previous['version'] != 1 or previous['request'] != request:
            msg = 'Upload inputs or destination changed since the first attempt; refusing to mix different inputs.'
            raise InvalidOperation(msg)
        return previous

    plan = Plan(transport)
    for info in codes_info:
        code = load_node(info.code_uuid)
        if isinstance(code, PortableCode):
            plan.repository(code.uuid, '.', '.')
            plan.entries[relative_path(str(code.filepath_executable))].mode = 0o755
    for operation in order:
        if operation == FileCopyOperation.SANDBOX:
            for path, entry in sandbox.items():
                plan.add(path, entry)
        elif operation == FileCopyOperation.LOCAL:
            for uuid, source, destination in calc_info.local_copy_list or []:
                try:
                    plan.repository(uuid, source, destination, inputs)
                except NotExistent:
                    logger.warning(f'failed to load Node<{uuid}> specified in the `local_copy_list`')
        elif operation == FileCopyOperation.REMOTE:
            for computer_uuid, source, destination in calc_info.remote_copy_list or []:
                if computer_uuid != computer.uuid:
                    msg = 'Remote copy between two different machines is not implemented yet'
                    raise NotImplementedError(msg)
                try:
                    await plan.remote_copy(source, destination)
                except FileNotFoundError:
                    logger.warning(f'Unable to copy remote resource from {source} to {destination}; ignoring.')
            for computer_uuid, source, destination in calc_info.remote_symlink_list or []:
                if computer_uuid != computer.uuid:
                    msg = 'It is not possible to create a symlink between two different machines'
                    raise OSError(msg)
                sources = await transport.glob_async(source) if has_magic(source) else [source]
                for path in sources:
                    target = (
                        str(PurePosixPath(destination) / PurePosixPath(path).name) if has_magic(source) else destination
                    )
                    plan.add(target, Entry('symlink', target=path))
        else:
            assert_never(operation)

    for entry in plan.entries.values():
        if entry.kind == 'file' and not entry.checksum:
            entry.checksum = await source_checksum(entry, folder, transport, inputs)
    manifest: Manifest = {
        'version': 1,
        'request': request,
        'entries': {path: asdict(entry) for path, entry in plan.entries.items()},
        'verified': [],
    }
    node.base.attributes.set(node.UPLOAD_MANIFEST_KEY, manifest)
    return manifest


async def reconcile(
    node: CalcJobNode,
    transport: Transport,
    manifest: Manifest,
    folder: Path,
    workdir: Path,
    inputs: Mapping[str, t.Any] | None = None,
) -> None:
    """Verify expected paths and repair only missing or incorrect inputs, without backup copies."""
    verified = []
    try:
        for relative, data in sorted(
            manifest['entries'].items(), key=lambda item: (len(PurePosixPath(item[0]).parts), item[0])
        ):
            entry = Entry(**data)
            destination = workdir / relative_path(relative)
            try:
                mode = (await transport.get_attribute_async(destination))['st_mode']
            except FileNotFoundError:
                mode = None
            if entry.kind == 'directory':
                if mode is not None and not stat.S_ISDIR(mode):
                    if relative == '.' or not stat.S_ISLNK(mode):
                        raise NotADirectoryError(str(destination))
                    await transport.remove_async(destination)
                    mode = None
                if mode is None:
                    await transport.mkdir_async(destination)
            else:
                if mode is not None and stat.S_ISDIR(mode):
                    raise IsADirectoryError(str(destination))
                correct = False
                if entry.kind == 'symlink' and mode is not None and stat.S_ISLNK(mode):
                    correct = await transport.readlink_async(destination) == entry.target
                elif entry.kind == 'file' and mode is not None and stat.S_ISREG(mode):
                    correct = await transport.get_file_checksum_async(destination) == entry.checksum
                    if entry.mode is not None and stat.S_IMODE(mode) != entry.mode:
                        # Replacing also breaks a possible hard link before chmod can affect another calculation.
                        correct = False
                if not correct:
                    if (
                        entry.kind == 'file'
                        and await source_checksum(entry, folder, transport, inputs) != entry.checksum
                    ):
                        msg = f'Upload source changed since the first attempt: {entry.path}'
                        raise InvalidOperation(msg)
                    # Unlink before replacing: never truncate through a symlink or hard link to a source file.
                    if mode is not None:
                        await transport.remove_async(destination)
                    if entry.kind == 'symlink':
                        await transport.symlink_literal_async(entry.target, destination)
                        if await transport.readlink_async(destination) != entry.target:
                            msg = f'Upload symlink verification failed: {destination}'
                            raise OSError(msg)
                    elif entry.source == 'remote':
                        await transport.copyfile_literal_async(entry.path, destination)
                    elif entry.source == 'repository':
                        with load_source(entry.uuid, inputs).base.repository.open(entry.path, 'rb') as handle:
                            await transport.putfilelike_async(handle, destination)
                    else:
                        await transport.putfile_async(folder / entry.path, destination)
                    if entry.kind == 'file' and await transport.get_file_checksum_async(destination) != entry.checksum:
                        msg = f'Upload checksum verification failed: {destination}'
                        raise OSError(msg)
                if entry.mode is not None and (mode is None or stat.S_IMODE(mode) != entry.mode or not correct):
                    await transport.chmod_async(destination, entry.mode)
            verified.append(relative)
    finally:
        # These are progress hints only: even previously verified destinations are checked on the next attempt.
        manifest['verified'] = verified
        node.base.attributes.set(node.UPLOAD_MANIFEST_KEY, manifest)
