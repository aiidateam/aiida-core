###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA ORM data class storing (numpy) arrays."""

from __future__ import annotations

import typing as t
from collections.abc import Mapping, Sequence

import numpy as np
import pydantic as pdt
from typing_extensions import Self

from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.data import Data

__all__ = ('ArrayData',)

_ArrayLike = Sequence[t.Any] | np.ndarray


class ArrayData(Data):
    """Store a set of arrays on disk (rather than on the database) in an efficient way.

    Arrays are stored using numpy and therefore this class requires numpy to be installed.

    Each array is stored within the Node folder as a different .npy file.

    :note: Before storing, no caching is done: if you perform a
        :py:meth:`.get_array` call, the array will be re-read from disk.
        If instead the ArrayData node has already been stored,
        the array is cached in memory after the first read, and the cached array
        is used thereafter.
        If too much RAM memory is used, you can clear the
        cache with the :py:meth:`.clear_internal_cache` method.
    """

    array_prefix = 'array|'
    default_array_name = 'default'

    _attributes_model_config = pdt.ConfigDict(
        extra='allow',
        json_schema_extra={
            'patternProperties': {
                r'^array\|[A-Za-z0-9_]+$': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'minItems': 1,
                    'description': 'Shape of an array stored in the repository',
                    'readOnly': True,
                }
            }
        },
    )

    _requires_array = True

    @classmethod
    def from_arrays(cls, arrays: _ArrayLike | Mapping[str, _ArrayLike], **kwargs: t.Any) -> Self:
        """Construct a new instance and set one or multiple numpy arrays.

        :param arrays: a single numpy array or sequence, or a mapping of arrays to store.
        """
        node = cls(**kwargs)

        if isinstance(arrays, (Sequence, np.ndarray)):
            arrays = {cls.default_array_name: arrays}

        if not isinstance(arrays, Mapping):
            raise TypeError('`arrays` should be a single sequence or mapping of sequences')

        if any(not isinstance(array, (Sequence, np.ndarray)) for array in arrays.values()):
            raise TypeError('`arrays` should be a single sequence or mapping of sequences')

        for name, array in arrays.items():
            node.set_array(name, np.asarray(array))

        return node

    def initialize(self) -> None:
        super().initialize()
        self._cached_arrays: dict[str, np.ndarray] = {}

    @property
    def arrays(self) -> dict[str, np.ndarray]:
        """Return all arrays stored in the node."""
        return {name: self.get_array(name) for name in self.get_arraynames()}

    def delete_array(self, name: str) -> None:
        """Delete an array from the node. Can only be called before storing.

        :param name: The name of the array to delete from the node.
        """
        filename = f'{name}.npy'

        if filename not in self.base.repository.list_object_names():
            msg = f"Array with name '{name}' not found in node pk={self.pk}"
            raise KeyError(msg)

        self.base.repository.delete_object(filename)

        try:
            self.base.attributes.delete(f'{self.array_prefix}{name}')
        except (KeyError, AttributeError):
            # Should not happen, but do not crash if for some reason the property was not set.
            pass

    def get_arraynames(self) -> list[str]:
        """Return a list of all arrays stored in the node, listing the files."""
        return self._arraynames_from_files()

    def get_shape(self, name: str) -> tuple[int, ...]:
        """Return the shape of an array (read from the value cached in the
        properties for efficiency reasons).

        :param name: The name of the array.
        """
        return tuple(self.base.attributes.get(f'{self.array_prefix}{name}'))

    def get_iterarrays(self) -> t.Iterator[tuple[str, np.ndarray]]:
        """Iterator that returns tuples (name, array) for each array stored in the node."""
        for name in self.get_arraynames():
            yield name, self.get_array(name)

    def get_array(self, name: str | None = None) -> np.ndarray:
        """Return an array stored in the node.

        :param name: The name of the array to return. The name can be omitted in case the node contains only a single
            array, which will be returned in that case. If ``name`` is ``None`` and the node contains multiple arrays or
            no arrays at all a ``ValueError`` is raised.
        :raises ValueError: If ``name`` is ``None`` and the node contains more than one arrays or no arrays at all.
        """
        if name is None:
            names = self.get_arraynames()
            num_arrays = len(names)

            if num_arrays == 0:
                raise ValueError('`name` not specified but the node contains no arrays.')

            if num_arrays > 1:
                raise ValueError('`name` not specified but the node contains multiple arrays.')

            name = names[0]

        def get_array_from_file(name: str) -> np.ndarray:
            """Return the array stored in a .npy file."""
            filename = f'{name}.npy'

            if filename not in self.base.repository.list_object_names():
                msg = f'Array with name `{name}` not found in ArrayData<{self.pk}>'
                raise KeyError(msg)

            # Open a handle in binary read mode as the arrays are written as binary files as well.
            with self.base.repository.open(filename, mode='rb') as handle:
                return np.load(handle, allow_pickle=False)

        # Return with proper caching if the node is stored, otherwise always re-read from disk.
        if not self.is_stored:
            return get_array_from_file(name)

        if name not in self._cached_arrays:
            self._cached_arrays[name] = get_array_from_file(name)

        return self._cached_arrays[name]

    def clear_internal_cache(self) -> None:
        """Clear the internal memory cache where the arrays are stored after being
        read from disk (used in order to reduce at minimum the readings from
        disk).

        This function is useful if you want to keep the node in memory, but you
        do not want to waste memory to cache the arrays in RAM.
        """
        self._cached_arrays = {}

    def set_array(self, name: str, array: np.ndarray) -> None:
        """Store a new numpy array inside the node. Possibly overwrite the array
        if it already existed.

        Internally, it stores a name.npy file in numpy format.

        :param name: The name of the array.
        :param array: The numpy array to store.
        """
        import tempfile

        if not isinstance(array, np.ndarray):
            raise TypeError('ArrayData can only store numpy arrays. Convert the object to an array first')

        self._validate_array_name(name)

        # Write the array to a temporary file, and then add it to the repository of the node.
        with tempfile.NamedTemporaryFile() as handle:
            np.save(handle, array, allow_pickle=False)

            # Flush and rewind the handle, otherwise the command to store it in the repo will write an empty file.
            handle.flush()
            handle.seek(0)

            # Write the numpy array to the repository, keeping the byte representation.
            self.base.repository.put_object_from_filelike(handle, f'{name}.npy')  # type: ignore[arg-type]

        # Store the array name and shape for querying purposes.
        self.base.attributes.set(f'{self.array_prefix}{name}', list(array.shape))

    def attach_file(self, name: str, fileobj: t.BinaryIO) -> None:
        """Attach an array stored in a ``.npy`` file."""
        if not name.lower().endswith('.npy'):
            msg = f'expected .npy file: {name}'
            raise ValueError(msg)

        base = name.removesuffix('.npy')
        array = np.load(fileobj, allow_pickle=False)
        self.set_array(base, array)

    def _arraynames_from_files(self) -> list[str]:
        """Return a list of all arrays stored in the node, listing the files (and
        not relying on the properties).
        """
        return [name[:-4] for name in self.base.repository.list_object_names() if name.endswith('.npy')]

    def _arraynames_from_properties(self) -> list[str]:
        """Return a list of all arrays stored in the node, listing the attributes
        starting with the correct prefix.
        """
        return [
            name[len(self.array_prefix) :] for name in self.base.attributes.keys() if name.startswith(self.array_prefix)
        ]

    def _validate_array_name(self, name: str) -> None:
        """Validate the array name.

        :param name: The name of the array.
        :raises ValueError: if the name is not valid.
        """
        import re

        if not name or re.sub('[0-9a-zA-Z_]', '', name):
            msg = (
                f'The name assigned to the array ({name}) is not valid. '
                'It can only contain digits, letters and underscores'
            )
            raise ValueError(msg)

    def _validate(self) -> None:
        """Validate the consistency of stored array files and metadata."""
        from aiida.common.exceptions import ValidationError

        super()._validate()

        files = self._arraynames_from_files()
        properties = self._arraynames_from_properties()

        if self._requires_array and not files:
            raise ValidationError('ArrayData must contain at least one array')

        if set(files) != set(properties):
            msg = f'Mismatch of files and properties for ArrayData node (pk={self.pk}): {files} vs. {properties}'
            raise ValidationError(msg)

    def _get_array_entries(self) -> dict[str, t.Any]:
        """Return a dictionary with the different array entries.

        The idea is that this dictionary contains the array name as a key and
        the value is the numpy array transformed into a list. This is so that
        it can be transformed into a json object.
        """
        return {name: clean_array(array) for name, array in self.get_iterarrays()}

    def _prepare_json(self, main_file_name: str = '', comments: bool = True) -> tuple[bytes, dict]:
        """Dump the content of the arrays stored in this node into JSON format.

        :param comments: if True, includes comments (if it makes sense for the given format)
        """
        import json

        from aiida import get_file_header

        json_dict = self._get_array_entries()
        json_dict['original_uuid'] = self.uuid

        if comments:
            json_dict['comments'] = get_file_header(comment_char='')

        return json.dumps(json_dict).encode('utf-8'), {}


@to_aiida_type.register(np.ndarray)
def _(value: np.ndarray) -> ArrayData:
    return ArrayData.from_arrays(value)


def clean_array(array: np.ndarray) -> list:
    """Replacing np.nan and np.inf/-np.inf for Nones.

    The function will also sanitize the array removing ``np.nan`` and ``np.inf``
    for ``None`` of this way the resulting JSON is always valid.
    Both ``np.nan`` and ``np.inf``/``-np.inf`` are set to None to be in
    accordance with the
    `ECMA-262 standard <https://www.ecma-international.org/publications-and-standards/standards/ecma-262/>`_.

    :param array: input array to be cleaned
    :return: cleaned list to be serialized
    :rtype: list
    """
    output = np.reshape(
        np.asarray(
            [entry if not np.isnan(entry) and not np.isinf(entry) else None for entry in array.flatten().tolist()]
        ),
        array.shape,
    )

    return output.tolist()
