###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin to model an atomic orbital."""

from __future__ import annotations

import copy
import typing as t

import pydantic as pdt

from aiida.common.exceptions import ValidationError
from aiida.orm import qb_fields
from aiida.orm.decorators import attribute
from aiida.orm.models.modeling import ModelAdapter
from aiida.orm.nodes.data.data import Data
from aiida.plugins import OrbitalFactory

__all__ = ('OrbitalData',)


@t.runtime_checkable
class Orbital(t.Protocol):
    def get_orbital_dict(self) -> dict[str, t.Any]: ...


def _orbital_to_dict(orbital: Orbital) -> dict[str, t.Any]:
    """Convert an orbital to its raw dictionary representation."""
    orbital_dict = copy.deepcopy(orbital.get_orbital_dict())

    if '_orbital_type' not in orbital_dict:
        msg = f'No _orbital_type found in: {orbital_dict}'
        raise ValueError(msg)

    return orbital_dict


def _orbital_from_dict(orbital_dict: dict[str, t.Any]) -> Orbital:
    """Construct an orbital from its raw dictionary representation."""
    orbital_dict = copy.deepcopy(orbital_dict)

    try:
        orbital_type = orbital_dict.pop('_orbital_type')
    except KeyError:
        msg = f'No _orbital_type found in: {orbital_dict}'
        raise ValidationError(msg)

    orbital_cls = OrbitalFactory(orbital_type)
    return orbital_cls(**orbital_dict)


class OrbitalsAdapter(ModelAdapter[list[Orbital], list[dict[str, t.Any]], qb_fields.QbArrayField]):
    """Adapt orbitals between the ORM and model representations."""

    @classmethod
    def to_model(cls, value: list[Orbital], *, context: t.Any = None) -> list[dict[str, t.Any]]:
        return [_orbital_to_dict(orbital) for orbital in value]

    @classmethod
    def to_orm(cls, value: list[dict[str, t.Any]], *, context: t.Any = None) -> list[Orbital]:
        return [_orbital_from_dict(orbital_dict) for orbital_dict in value]


class OrbitalData(Data):
    """Used for storing collections of orbitals, as well as
    providing methods for accessing them internally.
    """

    @attribute(
        model_adapter=OrbitalsAdapter(),
        model_field_info=pdt.fields.FieldInfo(default_factory=list),
    )
    def orbitals(self) -> list[Orbital]:
        """The orbitals."""
        orbital_dicts = copy.deepcopy(self.base.attributes.get('orbitals', []))
        return [_orbital_from_dict(orbital_dict) for orbital_dict in orbital_dicts]

    @orbitals.setter
    def orbitals(self, value: list[Orbital | dict[str, t.Any]]) -> None:
        self.base.attributes.set(
            'orbitals',
            [_orbital_to_dict(orbital) if isinstance(orbital, Orbital) else orbital for orbital in value],
        )

    def clear_orbitals(self) -> None:
        """Remove all orbitals that were added to the class
        Cannot work if OrbitalData has been already stored
        """
        self.base.attributes.set('orbitals', [])

    def get_orbitals(self, **kwargs: t.Any) -> list[Orbital]:
        """Returns all orbitals by default. If a site is provided, returns
        all orbitals cooresponding to the location of that site, additional
        arguments may be provided, which act as filters on the retrieved
        orbitals.

        :param site: if provided, returns all orbitals with position of site
        :kwargs: attributes than can filter the set of returned orbitals
        :return list_of_outputs: a list of orbitals
        """
        orbital_dicts = copy.deepcopy(self.base.attributes.get('orbitals', []))

        orbital_dicts = [
            orbital_dict
            for orbital_dict in orbital_dicts
            if all(key in orbital_dict and orbital_dict[key] == value for key, value in kwargs.items())
        ]

        return [_orbital_from_dict(orbital_dict) for orbital_dict in orbital_dicts]

    def set_orbitals(self, orbitals):
        """Sets the orbitals into the database. Uses the orbital's inherent
        set_orbital_dict method to generate a orbital dict string.

        :param orbitals: an orbital or list of orbitals to be set
        """
        if not isinstance(orbitals, list):
            orbitals = [orbitals]

        self.orbitals = orbitals


##########################################################################
#     Here are some ideas for potential future convenience methods
#########################################################################
#     def set_projection_on_site(self, orbital, site, tag=None):
#         """
#         Sets a orbital on a site
#         We prepare the description dictionary, using information `parsed`
#         from the site.
#         """
#         diffusivity = from_site_guess_diffusivity(site) # or 1.
#         position = site.position
#         description = {'somedictionary of the above':''}
#         self.set_projection(orbital=orbital, description=description)

#     def delete_projections_by_attribute(self, selection_attributes):
#         """
#         Deletes all projections whose internal attributes correspond to the
#         selection_attributes
#         """
#         raise NotImplementedError
#
#     def modify_projections(self, key_attributes_to_select_projections, attributes_to_be_modified):
#         """
#         Modifies the projections, as selected by the key_attributes.
#         Overwrites attributes inside these projections, to values stored
#         in attributes_to_be_modified
#         """
#
#    def set_realhydrogenorbitals_from_structure(self, structure, pseudo_family=None):
#        raise NotImplementedError
