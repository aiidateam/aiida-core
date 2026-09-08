"""`Data` sub class to represent any data using pickle."""

import sys
from pickle import UnpicklingError

import cloudpickle
from aiida import orm


class PickledData(orm.Data):
    """Data to represent a pickled value using cloudpickle."""

    FILENAME = "value.pkl"  # Class attribute to store the filename

    def __init__(self, value=None, **kwargs):
        """Initialize a `PickledData` node instance.

        :param value: raw Python value to initialize the `PickledData` node from.
        """
        super().__init__(**kwargs)
        self.set_value(value)

    def __str__(self):
        return f"<PickledData: {super().__str__()} : {self.get_value()}>"

    @property
    def value(self):
        """Return the contents of this node.

        :return: The unpickled value.
        """
        return self.get_value()

    @value.setter
    def value(self, value):
        self.set_value(value)

    def get_value(self):
        """Return the contents of this node, unpickling the stored value.

        :return: The unpickled value.
        """
        return self._get_value_from_file()

    def _get_value_from_file(self):
        """Read the pickled value from file and return it."""
        try:
            with self.base.repository.open(self.FILENAME, mode="rb") as f:
                return cloudpickle.loads(f.read())  # Deserialize the value
        except (UnpicklingError, ValueError) as e:
            raise ImportError(
                "Failed to load the pickled value. This may be due to an incompatible pickle protocol. "
                "Please ensure that the correct environment and cloudpickle version are being used."
            ) from e
        except ModuleNotFoundError as e:
            raise ImportError(
                "Failed to load the pickled value. This may be due to a missing module. "
                "Please ensure that the correct environment and cloudpickle version are being used."
            ) from e

    def get_serialized_value(self):
        """Return the serialized value stored in the repository.

        :return: The serialized value.
        """
        with self.base.repository.open(self.FILENAME, mode="rb") as f:
            return f.read()

    def set_value(self, value):
        """Set the contents of this node by pickling the provided value.

        :param value: The Python value to pickle and store.
        """
        # Serialize the value and store it
        serialized_value = cloudpickle.dumps(value)
        self.base.repository.put_object_from_bytes(serialized_value, self.FILENAME)

        # Store relevant metadata
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.base.attributes.set("python_version", python_version)
        self.base.attributes.set("serializer_module", cloudpickle.__name__)
        self.base.attributes.set("serializer_version", cloudpickle.__version__)
        self.base.attributes.set("pickle_protocol", cloudpickle.DEFAULT_PROTOCOL)
