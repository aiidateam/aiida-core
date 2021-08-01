# -*- coding: utf-8 -*-
"""Data plugin to represent an electronic band structure."""
from typing import Optional

from numpy.typing import ArrayLike

from aiida.common.lang import type_check
from ..kpoints import KpointsData
from .bands import BandsData

__all__ = ('ElectronicBandsData',)


class ElectronicBandsData(BandsData):
    """Data plugin to represent an electronic band structure.

    It subclasses the ``BandsData`` plugin and adds the ``fermi_level`` attribute.
    """

    KEY_FERMI_LEVEL = 'fermi_level'

    def __init__(self, kpoints: KpointsData, bands: ArrayLike, fermi_level: Optional[float] = None, **kwargs):
        """Construct a new instance.

        The arguments ``kpoints``, ``bands`` and ``fermi_level`` can be set through the constructor but have to be
        provided as positional arguments.

        .. note:: Since we are currently still supporting Python 3.7, we cannot yet use the ``/`` positional argument
            which was added to Python 3.8. Once support for Python 3.7 is dropped we can enforce the correct usage of
            the arguments through that operator.

        """
        super().__init__(**kwargs)

        self.set_kpointsdata(kpoints)
        self.set_bands(bands)

        if fermi_level is not None:
            self.fermi_level = fermi_level

    @property
    def fermi_level(self) -> Optional[float]:
        """Return the fermi level or ``None`` if one is not defined."""
        return self.get_attribute(self.KEY_FERMI_LEVEL, None)

    @fermi_level.setter
    def fermi_level(self, value: float):
        """Set the fermi level."""
        type_check(value, float)
        self.set_attribute(self.KEY_FERMI_LEVEL, value)
