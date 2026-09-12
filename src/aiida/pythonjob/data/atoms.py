import numpy as np
from aiida.orm import Data
from ase import Atoms
from ase.db.row import atoms2dict

__all__ = ("AtomsData",)


class AtomsData(Data):
    """Data to represent a ASE Atoms."""

    _cached_atoms = None

    def __init__(self, value=None, **kwargs):
        """Initialise a `AtomsData` node instance.

        :param value: ASE Atoms instance to initialise the `AtomsData` node from
        """
        atoms = value or Atoms()
        super().__init__(**kwargs)
        data, keys = self.atoms2dict(atoms)
        self.base.attributes.set_many(data)
        self.base.attributes.set("keys", keys)

    @classmethod
    def atoms2dict(cls, atoms):
        """Convert ASE Atoms to a dictionary."""
        # we remove the calculator as it may not be JSON serializable
        atoms.calc = None
        data = atoms2dict(atoms)
        data.pop("unique_id")
        keys = list(data.keys())
        formula = atoms.get_chemical_formula()
        data = cls._convert_numpy_to_native(data)
        data["formula"] = formula
        data["symbols"] = atoms.get_chemical_symbols()
        return data, keys

    @classmethod
    def _convert_numpy_to_native(cls, data):
        """Convert numpy types to Python native types for JSON compatibility."""
        for key, value in data.items():
            if isinstance(value, np.bool_):
                data[key] = bool(value)
            elif isinstance(value, np.ndarray):
                data[key] = value.tolist()
            elif isinstance(value, np.generic):
                data[key] = value.item()
        return data

    @property
    def value(self):
        keys = self.base.attributes.get("keys")
        data = self.base.attributes.get_many(keys)
        data = dict(zip(keys, data))
        return Atoms(**data)
