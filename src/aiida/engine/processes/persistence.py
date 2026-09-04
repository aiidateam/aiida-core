###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from Plumpy.                         #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The Plumpy license is reproduced in open_source_licenses.txt.         #
###########################################################################
"""Persistence support for process state."""

import abc
import asyncio
import collections
import copy
import errno
import fnmatch
import inspect
import os
import pickle
import stat
import uuid
import warnings
from collections.abc import Callable, Generator, Hashable, Iterable, MutableMapping
from types import MethodType
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union

import yaml

from aiida.common import loaders
from aiida.common.lang import call_with_super_check, super_check, type_check
from aiida.engine.processes import events
from aiida.engine.processes.exceptions import PersistenceError
from aiida.engine.processes.generic import futures

__all__: tuple[str, ...] = ()

PersistedCheckpoint = collections.namedtuple('PersistedCheckpoint', ['pid', 'tag'])
SAVED_STATE_TYPE = MutableMapping[str, Any]
PID_TYPE = Hashable

if TYPE_CHECKING:
    from aiida.engine.processes.generic.process import Process


def uuid_representer(dumper, data):
    return dumper.represent_scalar('!uuid', str(data))


def uuid_constructor(loader, node):
    value = loader.construct_scalar(node)
    return uuid.UUID(value)


yaml.add_representer(uuid.UUID, uuid_representer)
yaml.add_constructor('!uuid', uuid_constructor)


class Bundle(dict):
    def __init__(self, savable: 'Savable', save_context: Optional['LoadSaveContext'] = None, dereference: bool = False):
        """
        Create a bundle from a savable.  Optionally keep information about the
        class loader that can be used to load the classes in the bundle.

        :param savable: The savable object to bundle
        :param save_context: The optional save context to use
        :param dereference: Remove refrences from the data, by deep copying

        """
        super().__init__()
        if dereference:
            self.update(copy.deepcopy(savable.save(save_context)))
        else:
            self.update(savable.save(save_context))

    def unbundle(self, load_context: Optional['LoadSaveContext'] = None) -> 'Savable':
        """
        This method loads the class of the object and calls its recreate_from
        method passing the positional and keyword arguments.

        :param load_context: The optional load context
        :return: An instance of the Savable

        """
        return Savable.load(self, load_context)


BUNDLE_TAG = '!aiida:bundle'


def _bundle_representer(dumper: yaml.Dumper, node: Any) -> Any:
    return dumper.represent_mapping(BUNDLE_TAG, node)


def _bundle_constructor(loader: yaml.Loader, data: Any) -> Generator[Bundle, None, None]:
    result = Bundle.__new__(Bundle)
    yield result
    mapping = loader.construct_mapping(data)
    result.update(mapping)


yaml.add_representer(Bundle, _bundle_representer)
yaml.add_constructor(BUNDLE_TAG, _bundle_constructor)  # type: ignore[arg-type]


class Persister(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def save_checkpoint(self, process: 'Process', tag: str | None = None) -> None:
        """
        Persist a Process instance

        :param process: :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow distinguishing
            multiple checkpoints for the same process
        :raises: :class:`aiida.engine.processes.exceptions.PersistenceError` Raised if saving the checkpoint fails
        """

    @abc.abstractmethod
    def load_checkpoint(self, pid: PID_TYPE, tag: str | None = None) -> Bundle:
        """
        Load a process from a persisted checkpoint by its process id

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving
            a specific sub checkpoint for the corresponding process
        :return: a bundle with the process state

        :raises: :class:`aiida.engine.processes.exceptions.PersistenceError` Raised if loading the checkpoint fails
        """

    @abc.abstractmethod
    def get_checkpoints(self) -> list[PersistedCheckpoint]:
        """
        Return a list of all the current persisted process checkpoints
        with each element containing the process id and optional checkpoint tag

        :return: list of PersistedCheckpoint
        """

    @abc.abstractmethod
    def get_process_checkpoints(self, pid: PID_TYPE) -> list[PersistedCheckpoint]:
        """
        Return a list of all the current persisted process checkpoints for the
        specified process with each element containing the process id and
        optional checkpoint tag

        :param pid: the process pid
        :return: list of PersistedCheckpoint tuples
        """

    @abc.abstractmethod
    def delete_checkpoint(self, pid: PID_TYPE, tag: str | None = None) -> None:
        """
        Delete a persisted process checkpoint. No error will be raised if
        the checkpoint does not exist

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving
            a specific sub checkpoint for the corresponding process
        """

    @abc.abstractmethod
    def delete_process_checkpoints(self, pid: PID_TYPE) -> None:
        """
        Delete all persisted checkpoints related to the given process id

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        """


PersistedPickle = collections.namedtuple('PersistedPickle', ['checkpoint', 'bundle'])
_PICKLE_SUFFIX = 'pickle'


class PicklePersister(Persister):
    """Persist process states as pickles in a trusted, private directory."""

    def __init__(self, pickle_directory: str):
        """
        Instantiate a PicklePersister object that will persist processes by
        writing their bundles to a pickle in a directory specified by the
        argument 'pickle_directory'

        :param pickle_directory: the full path to the directory where pickles will be written
        """
        super().__init__()

        PicklePersister.ensure_pickle_directory(pickle_directory)

        self._pickle_directory = pickle_directory

    @staticmethod
    def ensure_pickle_directory(dirpath: str) -> None:
        """Ensure that the pickle directory exists with owner-only permissions.

        If the directory already exists with more permissive permissions, they
        are changed to ``rwx------`` and a warning is raised.
        """
        try:
            os.makedirs(dirpath, mode=stat.S_IRWXU)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                msg = f'failed to create the pickle directory at {dirpath}'
                raise ValueError(msg) from exception

            if stat.S_IMODE(os.stat(dirpath).st_mode) != stat.S_IRWXU:
                msg = f'Changing permissions of the pickle directory {dirpath} to rwx------.'
                warnings.warn(msg, UserWarning, stacklevel=2)
                try:
                    os.chmod(dirpath, stat.S_IRWXU)
                except OSError as exception:
                    msg = f'failed to change permissions of the pickle directory at {dirpath}'
                    raise ValueError(msg) from exception

    @staticmethod
    def load_pickle(filepath: str) -> 'PersistedPickle':
        """
        Load a pickle from disk

        :param filepath: absolute filepath to the pickle
        :returns: the loaded pickle

        """
        with open(filepath, 'r+b') as handle:
            persisted_pickle = pickle.load(handle)

        return persisted_pickle

    @staticmethod
    def pickle_filename(pid: PID_TYPE, tag: str | None = None) -> str:
        """
        Returns the relative filepath of the pickle for the given process id
        and optional checkpoint tag
        """
        if tag is not None:
            filename = f'{pid}.{tag}.{_PICKLE_SUFFIX}'
        else:
            filename = f'{pid}.{_PICKLE_SUFFIX}'

        return filename

    def _pickle_filepath(self, pid: PID_TYPE, tag: str | None = None) -> str:
        """
        Returns the full filepath of the pickle for the given process id
        and optional checkpoint tag
        """
        return os.path.join(self._pickle_directory, PicklePersister.pickle_filename(pid, tag))

    def save_checkpoint(self, process: 'Process', tag: str | None = None) -> None:
        """
        Persist a process to a pickle on disk

        :param process: :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow distinguishing
            multiple checkpoints for the same process
        """
        bundle = Bundle(process)
        checkpoint = PersistedCheckpoint(process.pid, tag)
        persisted_pickle = PersistedPickle(checkpoint, bundle)

        with open(self._pickle_filepath(process.pid, tag), 'w+b') as handle:
            pickle.dump(persisted_pickle, handle)

    def load_checkpoint(self, pid: PID_TYPE, tag: str | None = None) -> Bundle:
        """
        Load a process from a persisted checkpoint by its process id

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving
            a specific sub checkpoint for the corresponding process
        :return: a bundle with the process state

        """
        filepath = self._pickle_filepath(pid, tag)
        checkpoint = PicklePersister.load_pickle(filepath)

        return checkpoint.bundle

    def get_checkpoints(self) -> list[PersistedCheckpoint]:
        """
        Return a list of all the current persisted process checkpoints
        with each element containing the process id and optional checkpoint tag

        :return: list of PersistedCheckpoint
        """
        checkpoints = []
        file_pattern = f'*.{_PICKLE_SUFFIX}'

        for _, _, files in os.walk(self._pickle_directory):
            for filename in fnmatch.filter(files, file_pattern):
                filepath = os.path.join(self._pickle_directory, filename)
                persisted_pickle = PicklePersister.load_pickle(filepath)
                checkpoints.append(persisted_pickle.checkpoint)

        return checkpoints

    def get_process_checkpoints(self, pid: PID_TYPE) -> list[PersistedCheckpoint]:
        """
        Return a list of all the current persisted process checkpoints for the
        specified process with each element containing the process id and
        optional checkpoint tag

        :param pid: the process pid
        :return: list of PersistedCheckpoint
        """
        return [c for c in self.get_checkpoints() if c.pid == pid]

    def delete_checkpoint(self, pid: PID_TYPE, tag: str | None = None) -> None:
        """
        Delete a persisted process checkpoint. No error will be raised if
        the checkpoint does not exist

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving
            a specific sub checkpoint for the corresponding process
        """
        pickle_filepath = self._pickle_filepath(pid, tag)

        try:
            os.remove(pickle_filepath)
        except OSError:
            pass

    def delete_process_checkpoints(self, pid: PID_TYPE) -> None:
        """
        Delete all persisted checkpoints related to the given process id

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        """
        for checkpoint in self.get_process_checkpoints(pid):
            self.delete_checkpoint(checkpoint.pid, checkpoint.tag)


class InMemoryPersister(Persister):
    """Mainly to be used in testing/debugging"""

    def __init__(self, loader: loaders.ObjectLoader | None = None) -> None:
        super().__init__()
        self._checkpoints: dict[PID_TYPE, dict[str | None, Bundle]] = {}
        self._save_context = LoadSaveContext(loader=loader)

    def save_checkpoint(self, process: 'Process', tag: str | None = None) -> None:
        self._checkpoints.setdefault(process.pid, {})[tag] = Bundle(process, self._save_context, dereference=True)

    def load_checkpoint(self, pid: PID_TYPE, tag: str | None = None) -> Bundle:
        return self._checkpoints[pid][tag]

    def get_checkpoints(self) -> list[PersistedCheckpoint]:
        cps = []
        for pid in self._checkpoints:
            cps.extend(self.get_process_checkpoints(pid))
        return cps

    def get_process_checkpoints(self, pid: PID_TYPE) -> list[PersistedCheckpoint]:
        cps = []
        try:
            for tag, _ in self._checkpoints[pid].items():
                cps.append(PersistedCheckpoint(pid, tag))
        except KeyError:
            pass
        return cps

    def delete_checkpoint(self, pid: PID_TYPE, tag: str | None = None) -> None:
        try:
            del self._checkpoints[pid][tag]
        except KeyError:
            pass

    def delete_process_checkpoints(self, pid: PID_TYPE) -> None:
        if pid in self._checkpoints:
            del self._checkpoints[pid]


SavableClsType = TypeVar('SavableClsType', bound='type[Savable]')


def auto_persist(*members: str) -> Callable[[SavableClsType], SavableClsType]:
    def wrapped(savable: SavableClsType) -> SavableClsType:
        if savable._auto_persist is None:
            savable._auto_persist = set()
        else:
            savable._auto_persist = set(savable._auto_persist)
        savable.auto_persist(*members)
        return savable

    return wrapped


def _ensure_object_loader(context: Optional['LoadSaveContext'], saved_state: SAVED_STATE_TYPE) -> 'LoadSaveContext':
    """
    Given a LoadSaveContext this method will ensure that it has a valid class loader
    using the following priorities:
    1) The one that is already in the context
    2) One that is found in the saved state
    3) The default global class loader from loaders.get_object_loader()
    :param context:
    :param saved_state:
    :return:
    """
    if context is None:
        context = LoadSaveContext()

    assert isinstance(context, LoadSaveContext)

    if context.loader is not None:
        return context

    # 2) Try getting from saved_state
    default_loader = loaders.get_object_loader()
    try:
        loader_identifier = Savable.get_custom_meta(saved_state, META__OBJECT_LOADER)
    except ValueError:
        # 3) Fall back to default
        loader = default_loader
    else:
        loader = default_loader.load_object(loader_identifier)

    return context.copyextend(loader=loader)


class LoadSaveContext:
    def __init__(self, loader: loaders.ObjectLoader | None = None, **kwargs: Any) -> None:
        self._values = dict(**kwargs)
        self.loader = loader

    def __getattr__(self, item: str) -> Any:
        try:
            return self._values[item]
        except KeyError:
            raise AttributeError(f"item '{item}' not found")

    def __iter__(self) -> Iterable[Any]:
        return self._value.__iter__()

    def __contains__(self, item: Any) -> bool:
        return self._values.__contains__(item)

    def copyextend(self, **kwargs: Any) -> 'LoadSaveContext':
        """Add additional information to the context by making a copy with the new values"""
        extended = self._values.copy()
        extended.update(kwargs)
        loader = extended.pop('loader', self.loader)
        return LoadSaveContext(loader=loader, **extended)


META: str = '!!meta'
META__CLASS_NAME: str = 'class_name'
META__OBJECT_LOADER: str = 'object_loader'
META__USER: str = 'user'
META__TYPES: str = 'types'
META__TYPE__METHOD: str = 'm'
META__TYPE__SAVABLE: str = 'S'


class Savable:
    CLASS_NAME: str = 'class_name'

    _auto_persist: set[str] | None = None
    _persist_configured = False

    @staticmethod
    def load(saved_state: SAVED_STATE_TYPE, load_context: LoadSaveContext | None = None) -> 'Savable':
        """
        Load a `Savable` from a saved instance state.  The load context is a way of passing
        runtime data to the object being loaded.

        :param saved_state: The saved state
        :param load_context: Additional runtime state that can be passed into when loading.
            The type and content (if any) is completely user defined
        :return: The loaded Savable instance

        """
        load_context = _ensure_object_loader(load_context, saved_state)
        assert load_context.loader is not None  # required for type checking
        try:
            class_name = Savable._get_class_name(saved_state)
            load_cls = load_context.loader.load_object(class_name)
        except KeyError:
            raise ValueError('Class name not found in saved state')
        else:
            return load_cls.recreate_from(saved_state, load_context)

    @classmethod
    def auto_persist(cls, *members: str) -> None:
        if cls._auto_persist is None:
            cls._auto_persist = set()
        cls._auto_persist.update(members)

    @classmethod
    def persist(cls) -> None:
        pass

    @classmethod
    def recreate_from(cls, saved_state: SAVED_STATE_TYPE, load_context: LoadSaveContext | None = None) -> 'Savable':
        """
        Recreate a :class:`Savable` from a saved state using an optional load context.

        :param saved_state: The saved state
        :param load_context: An optional load context

        :return: The recreated instance

        """
        load_context = _ensure_object_loader(load_context, saved_state)
        obj = cls.__new__(cls)
        call_with_super_check(obj.load_instance_state, saved_state, load_context)
        return obj

    @super_check
    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: LoadSaveContext) -> None:
        self._ensure_persist_configured()
        if self._auto_persist is not None:
            self.load_members(self._auto_persist, saved_state, load_context)

    @super_check
    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: LoadSaveContext) -> None:
        self._ensure_persist_configured()
        if self._auto_persist is not None:
            self.save_members(self._auto_persist, out_state)

    def save(self, save_context: LoadSaveContext | None = None) -> SAVED_STATE_TYPE:
        out_state: SAVED_STATE_TYPE = {}

        if save_context is None:
            save_context = LoadSaveContext()

        type_check(save_context, LoadSaveContext)

        default_loader = loaders.get_object_loader()
        # If the user has specified a class loader, then save it in the saved state
        if save_context.loader is not None:
            loader_class = default_loader.identify_object(save_context.loader.__class__)
            Savable.set_custom_meta(out_state, META__OBJECT_LOADER, loader_class)
            loader = save_context.loader
        else:
            loader = default_loader

        Savable._set_class_name(out_state, loader.identify_object(self.__class__))
        call_with_super_check(self.save_instance_state, out_state, save_context)
        return out_state

    def save_members(self, members: Iterable[str], out_state: SAVED_STATE_TYPE) -> None:
        for member in members:
            value = getattr(self, member)
            if inspect.ismethod(value):
                if value.__self__ is not self:
                    raise TypeError('Cannot persist methods of other classes')
                Savable._set_meta_type(out_state, member, META__TYPE__METHOD)
                value = value.__name__
            elif isinstance(value, Savable):
                Savable._set_meta_type(out_state, member, META__TYPE__SAVABLE)
                value = value.save()
            else:
                value = copy.deepcopy(value)
            out_state[member] = value

    def load_members(
        self, members: Iterable[str], saved_state: SAVED_STATE_TYPE, load_context: LoadSaveContext | None = None
    ) -> None:
        for member in members:
            setattr(self, member, self._get_value(saved_state, member, load_context))

    def _ensure_persist_configured(self) -> None:
        if not self._persist_configured:
            self.persist()
            self._persist_configured = True

    # region Metadata getter/setters

    @staticmethod
    def set_custom_meta(out_state: SAVED_STATE_TYPE, name: str, value: Any) -> None:
        user_dict = Savable._get_create_meta(out_state).setdefault(META__USER, {})
        user_dict[name] = value

    @staticmethod
    def get_custom_meta(saved_state: SAVED_STATE_TYPE, name: str) -> Any:
        try:
            return saved_state[META][META__USER][name]
        except KeyError:
            raise ValueError(f"Unknown meta key '{name}'")

    @staticmethod
    def _get_create_meta(out_state: SAVED_STATE_TYPE) -> dict[str, Any]:
        return out_state.setdefault(META, {})

    @staticmethod
    def _set_class_name(out_state: SAVED_STATE_TYPE, name: str) -> None:
        Savable._get_create_meta(out_state)[META__CLASS_NAME] = name

    @staticmethod
    def _get_class_name(saved_state: SAVED_STATE_TYPE) -> str:
        return Savable._get_create_meta(saved_state)[META__CLASS_NAME]

    @staticmethod
    def _set_meta_type(out_state: SAVED_STATE_TYPE, name: str, type_spec: Any) -> None:
        type_dict = Savable._get_create_meta(out_state).setdefault(META__TYPES, {})
        type_dict[name] = type_spec

    @staticmethod
    def _get_meta_type(saved_state: SAVED_STATE_TYPE, name: str) -> Any:
        try:
            return saved_state[META][META__TYPES][name]
        except KeyError:
            pass

    # endregion

    def _get_value(
        self, saved_state: SAVED_STATE_TYPE, name: str, load_context: LoadSaveContext | None
    ) -> Union[MethodType, 'Savable']:
        value = saved_state[name]

        typ = Savable._get_meta_type(saved_state, name)
        if typ == META__TYPE__METHOD:
            value = getattr(self, value)
        elif typ == META__TYPE__SAVABLE:
            value = Savable.load(value, load_context)

        return value


@auto_persist('_state', '_result')
class SavableFuture(futures.Future, Savable):
    """
    A savable future.

    .. note: This does not save any assigned done callbacks.
    """

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        if self.done() and not self.cancelled() and self.exception() is not None:
            out_state['exception'] = self.exception()

    @classmethod
    def recreate_from(cls, saved_state: SAVED_STATE_TYPE, load_context: LoadSaveContext | None = None) -> 'Savable':
        """
        Recreate a :class:`Savable` from a saved state using an optional load context.

        :param saved_state: The saved state
        :param load_context: An optional load context

        :return: The recreated instance

        """
        load_context = _ensure_object_loader(load_context, saved_state)

        try:
            loop = load_context.loop
        except AttributeError:
            loop = events.get_or_create_event_loop()

        state = saved_state['_state']

        if state == asyncio.futures._PENDING:  # type: ignore[attr-defined]
            obj = cls(loop=loop)
        elif state == asyncio.futures._FINISHED:  # type: ignore[attr-defined]
            obj = cls(loop=loop)
            result = saved_state['_result']

            try:
                exception = saved_state['exception']
                obj.set_exception(exception)
            except KeyError:
                obj.set_result(result)
        elif state == asyncio.futures._CANCELLED:  # type: ignore[attr-defined]
            obj = cls(loop=loop)
            obj.cancel()
        else:
            msg = f'Unsupported future state: {state}'
            raise PersistenceError(msg)

        return obj

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        if self._callbacks:
            # typing says asyncio.Future._callbacks needs to be called, but in the python 3.7 code it is a simple list
            for callback in self._callbacks:
                self.remove_done_callback(callback)  # type: ignore[arg-type]
