###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tools for handling Crystallographic Information Files (CIF)"""

from __future__ import annotations

import re
import typing as t
from collections.abc import Sequence
from typing import Literal

import pydantic as pdt
from typing_extensions import Self

from aiida.common.typing import FilePath
from aiida.common.utils import Capturing
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.singlefile import SinglefileData

if t.TYPE_CHECKING:
    from ase import Atoms
    from CifFile import CifFile

    from aiida.orm.implementation import StorageBackend
    from aiida.orm.nodes.data.structure import StructureData


__all__ = ('CifData', 'cif_from_ase', 'has_pycifrw', 'pycifrw_from_cif')

ase_loops = {
    '_atom_site': [
        '_atom_site_label',
        '_atom_site_occupancy',
        '_atom_site_fract_x',
        '_atom_site_fract_y',
        '_atom_site_fract_z',
        '_atom_site_adp_type',
        '_atom_site_thermal_displace_type',
        '_atom_site_B_iso_or_equiv',
        '_atom_site_U_iso_or_equiv',
        '_atom_site_B_equiv_geom_mean',
        '_atom_site_U_equiv_geom_mean',
        '_atom_site_type_symbol',
    ]
}


def has_pycifrw():
    """:return: True if the PyCifRW module can be imported, False otherwise."""
    try:
        import CifFile  # noqa: F401
        from CifFile import CifBlock  # noqa: F401
    except ImportError:
        return False
    return True


def cif_from_ase(
    ase: Atoms | list[Atoms] | tuple[Atoms, ...],
    full_occupancies: bool = False,
    add_fake_biso: bool = False,
) -> list[dict[str, t.Any]]:
    """Construct a CIF datablock from the ASE structure. The code is taken
    from
    https://wiki.fysik.dtu.dk/ase/ase/io/formatoptions.html#ase.io.cif.write_cif,
    as the original ASE code contains a bug in printing the
    Hermann-Mauguin symmetry space group symbol.

    :param ase: ASE "images"
    :return: array of CIF datablocks
    """
    from numpy import arccos, dot, pi
    from numpy.linalg import norm

    if not isinstance(ase, (list, tuple)):
        ase = [ase]

    datablocks = []
    for _, atoms in enumerate(ase):
        datablock = {}

        cell = atoms.cell
        a = norm(cell[0])
        b = norm(cell[1])
        c = norm(cell[2])
        alpha = arccos(dot(cell[1], cell[2]) / (b * c)) * 180.0 / pi
        beta = arccos(dot(cell[0], cell[2]) / (a * c)) * 180.0 / pi
        gamma = arccos(dot(cell[0], cell[1]) / (a * b)) * 180.0 / pi

        datablock['_cell_length_a'] = str(a)
        datablock['_cell_length_b'] = str(b)
        datablock['_cell_length_c'] = str(c)
        datablock['_cell_angle_alpha'] = str(alpha)
        datablock['_cell_angle_beta'] = str(beta)
        datablock['_cell_angle_gamma'] = str(gamma)

        if atoms.pbc.all():
            datablock['_symmetry_space_group_name_H-M'] = 'P 1'
            datablock['_symmetry_int_tables_number'] = str(1)
            datablock['_symmetry_equiv_pos_as_xyz'] = ['x, y, z']

        datablock['_atom_site_label'] = []
        datablock['_atom_site_fract_x'] = []
        datablock['_atom_site_fract_y'] = []
        datablock['_atom_site_fract_z'] = []
        datablock['_atom_site_type_symbol'] = []

        if full_occupancies:
            datablock['_atom_site_occupancy'] = []
        if add_fake_biso:
            datablock['_atom_site_thermal_displace_type'] = []
            datablock['_atom_site_B_iso_or_equiv'] = []

        scaled = atoms.get_scaled_positions()
        no = {}
        for i, atom in enumerate(atoms):
            symbol = atom.symbol
            if symbol in no:
                no[symbol] += 1
            else:
                no[symbol] = 1
            datablock['_atom_site_label'].append(symbol + str(no[symbol]))
            datablock['_atom_site_fract_x'].append(str(scaled[i][0]))
            datablock['_atom_site_fract_y'].append(str(scaled[i][1]))
            datablock['_atom_site_fract_z'].append(str(scaled[i][2]))
            datablock['_atom_site_type_symbol'].append(symbol)

            if full_occupancies:
                datablock['_atom_site_occupancy'].append(str(1.0))
            if add_fake_biso:
                datablock['_atom_site_thermal_displace_type'].append('Biso')
                datablock['_atom_site_B_iso_or_equiv'].append(str(1.0))

        datablocks.append(datablock)
    return datablocks


def pycifrw_from_cif(
    datablocks: list[dict[str, t.Any]],
    loops: dict[str, list[str]] | None = None,
    names: list[str] | None = None,
) -> CifFile:
    """Constructs PyCifRW's CifFile from an array of CIF datablocks.

    :param datablocks: an array of CIF datablocks
    :param loops: optional dict of lists of CIF tag loops.
    :param names: optional list of datablock names
    :return: CifFile
    """
    try:
        import CifFile
        from CifFile import CifBlock
    except ImportError as exc:
        raise ImportError(f'{exc!s}. You need to install the PyCifRW package.')

    if loops is None:
        loops = {}

    cif = CifFile.CifFile()
    try:
        cif.set_grammar('1.1')
    except AttributeError:
        # if no grammar can be set, we assume it's 1.1 (widespread standard)
        pass

    if names and len(names) < len(datablocks):
        raise ValueError(
            f'Not enough names supplied for datablocks: {len(names)} (names) < {len(datablocks)} (datablocks)'
        )
    for i, values in enumerate(datablocks):
        name = str(i)
        if names:
            name = names[i]
        datablock = CifBlock()
        cif[name] = datablock
        tags_in_loops = []
        for loopname in loops.keys():
            row_size = None
            tags_seen = []
            for tag in loops[loopname]:
                if tag in values:
                    tag_values = values.pop(tag)
                    if not isinstance(tag_values, list):
                        tag_values = [tag_values]
                    if row_size is None:
                        row_size = len(tag_values)
                    elif row_size != len(tag_values):
                        raise ValueError(
                            f'Number of values for tag `{tag}` is different from the others in the same loop'
                        )
                    if row_size == 0:
                        continue
                    datablock.AddItem(tag, tag_values)
                    tags_seen.append(tag)
                    tags_in_loops.append(tag)
            if row_size is not None and row_size > 0:
                datablock.CreateLoop(datanames=tags_seen)
        for tag in sorted(values.keys()):
            if tag not in tags_in_loops:
                datablock.AddItem(tag, values[tag])
                # create automatically a loop for non-scalar values
                if isinstance(values[tag], (tuple, list)) and tag not in loops.keys():
                    datablock.CreateLoop([tag])
    return cif


def parse_formula(formula: str) -> dict[str, int | float]:
    """Parses the Hill formulae. Does not need spaces as separators.
    Works also for partial occupancies and for chemical groups enclosed in round/square/curly brackets.
    Elements are counted and a dictionary is returned.
    e.g.  'C[NH2]3NO3'  -->  {'C': 1, 'N': 4, 'H': 6, 'O': 3}
    """

    def chemcount_str_to_number(string: str | None) -> int | float:
        """Convert a chemical count string to a number (int or float)."""
        if not string:
            quantity = 1
        else:
            quantity = float(string)
            if quantity.is_integer():
                quantity = int(quantity)
        return quantity

    contents: dict[str, int | float] = {}

    # split blocks with parentheses
    for block in re.split(r'(\([^\)]*\)[^A-Z\(\[\{]*|\[[^\]]*\][^A-Z\(\[\{]*|\{[^\}]*\}[^A-Z\(\[\{]*)', formula):
        if not block:  # block is void
            continue

        # get molecular formula (within parentheses) & count
        group = re.search(r'[\{\[\(](.+)[\}\]\)]([\.\d]*)', block)
        if group is None:  # block does not contain parentheses
            molformula = block
            molcount = 1
        else:
            molformula = group.group(1)
            molcount = chemcount_str_to_number(group.group(2))

        for part in re.findall(r'[A-Z][^A-Z\s]*', molformula.replace(' ', '')):  # split at uppercase letters
            match = re.match(r'(\D+)([\.\d]+)?', part)  # separates element and count

            if match is None:
                continue

            species = match.group(1)
            quantity = chemcount_str_to_number(match.group(2)) * molcount
            contents[species] = contents.get(species, 0) + quantity
    return contents


class CifData(SinglefileData):
    """Wrapper for Crystallographic Interchange File (CIF)

    .. note:: the file (physical) is held as the authoritative source of
        information, so all conversions are done through the physical file:
        when setting ``ase`` or ``values``, a physical CIF file is generated
        first, the values are updated from the physical CIF file.
    """

    _SCAN_TYPES = ('standard', 'flex')
    _SCAN_TYPE_DEFAULT = 'standard'
    _PARSE_POLICIES = ('eager', 'lazy')
    _PARSE_POLICY_DEFAULT = 'eager'

    @classmethod
    def from_path(
        cls,
        filepath: FilePath,
        filename: FilePath | None = None,
        scan_type: Literal['standard', 'flex'] = _SCAN_TYPE_DEFAULT,
        parse_policy: Literal['eager', 'lazy'] = _PARSE_POLICY_DEFAULT,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance and set the contents to that of the file.

        :param filepath: an absolute filepath for the CIF.
        :param filename: specify filename to use (defaults to name of provided file).
        :param scan_type: scan type string for parsing with PyCIFRW ('standard' or 'flex'). See CifFile.ReadCif
        :param parse_policy: 'eager' (parse CIF file on set_file) or 'lazy' (defer parsing until needed)
        """
        instance = cls(**kwargs)
        instance.scan_type = scan_type
        instance.parse_policy = parse_policy
        instance.set_file(filepath, filename=filename)

        if parse_policy == 'eager':
            instance.parse()

        return instance

    @classmethod
    def from_ase(
        cls,
        ase: Atoms | list[Atoms] | tuple[Atoms, ...],
        scan_type: Literal['standard', 'flex'] = _SCAN_TYPE_DEFAULT,
        parse_policy: Literal['eager', 'lazy'] = _PARSE_POLICY_DEFAULT,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance from an ASE Atoms object."""
        instance = cls(**kwargs)
        instance.scan_type = scan_type
        instance.parse_policy = parse_policy
        instance.set_ase(ase)
        return instance

    @classmethod
    def from_values(
        cls,
        values: CifFile,
        scan_type: Literal['standard', 'flex'] = _SCAN_TYPE_DEFAULT,
        parse_policy: Literal['eager', 'lazy'] = _PARSE_POLICY_DEFAULT,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance from a PyCifRW CifFile object."""
        instance = cls(**kwargs)
        instance.scan_type = scan_type
        instance.parse_policy = parse_policy
        instance.set_values(values)
        return instance

    @classmethod
    def from_md5(cls, md5: str, backend: StorageBackend | None = None) -> list[Self]:
        """Return a list of all CIF files that match a given MD5 hash.

        .. note:: the hash has to be stored in the ``md5`` attribute,
            otherwise the CIF file will not be found.
        """
        from aiida.orm.querybuilder import QueryBuilder

        builder = QueryBuilder(backend=backend)
        builder.append(cls, filters={'attributes.md5': {'==': md5}})
        return builder.all(flat=True)

    @attribute(readonly=True)
    def formulae(self) -> list[str | None] | None:
        """The formulae contained in the CIF file."""
        return self.base.attributes.get('formulae', None)

    @attribute(readonly=True)
    def spacegroup_numbers(self) -> list[int | None] | None:
        """The space group numbers of the structures."""
        return self.base.attributes.get('spacegroup_numbers', None)

    @attribute(
        readonly=True,
        required_once_stored=True,
    )
    def md5(self) -> str | None:
        """The MD5 checksum of the file contents."""
        return self.base.attributes.get('md5', None)

    @attribute(model_field_info=pdt.fields.FieldInfo(default=_SCAN_TYPE_DEFAULT))
    def scan_type(self) -> Literal['standard', 'flex']:
        """The scan type for parsing with PyCifRW."""
        return self.base.attributes.get('scan_type', self._SCAN_TYPE_DEFAULT)

    @scan_type.setter
    def scan_type(self, value: Literal['standard', 'flex']) -> None:
        if value not in self._SCAN_TYPES:
            raise ValueError(f'Got unknown scan_type {value}')
        self.base.attributes.set('scan_type', value)

    @attribute(model_field_info=pdt.fields.FieldInfo(default=_PARSE_POLICY_DEFAULT))
    def parse_policy(self) -> Literal['eager', 'lazy']:
        """The parse policy for parsing with PyCifRW."""
        return self.base.attributes.get('parse_policy', self._PARSE_POLICY_DEFAULT)

    @parse_policy.setter
    def parse_policy(self, value: Literal['eager', 'lazy']) -> None:
        if value not in self._PARSE_POLICIES:
            raise ValueError(f'Got unknown parse_policy {value}')
        self.base.attributes.set('parse_policy', value)

    @property
    def ase(self) -> Atoms:
        """ASE object, representing the CIF.

        .. note:: requires ASE module.
        """
        if self._ase is None:
            self._ase = self.get_ase()
        return self._ase

    @ase.setter
    def ase(self, aseatoms: Atoms) -> None:
        self.set_ase(aseatoms)

    @property
    def values(self) -> CifFile:
        """PyCifRW structure, representing the CIF datablocks.

        .. note:: requires PyCifRW module.
        """
        if self._values is None:
            import CifFile
            from CifFile import CifBlock

            with self.open() as handle:
                c = CifFile.ReadCif(handle, scantype=self.scan_type)
            for k, v in c.items():
                c.dictionary[k] = CifBlock(v)
            self._values = c
        return self._values

    @values.setter
    def values(self, values: CifFile) -> None:
        self.set_values(values)

    @property
    def has_partial_occupancies(self) -> bool:
        """Return if the cif data contains partial occupancies

        A partial occupancy is defined as site with an occupancy that differs from unity, within a precision of 1E-6

        .. note: occupancies that cannot be parsed into a float are ignored

        :return: True if there are partial occupancies, False otherwise
        """
        tag = '_atom_site_occupancy'

        epsilon = 1e-6
        partial_occupancies = False

        for datablock in self.values.keys():
            if tag in self.values[datablock].keys():
                for position in self.values[datablock][tag]:
                    try:
                        # First remove any parentheses to support value like 1.134(56) and then cast to float
                        occupancy = float(re.sub(r'[\(\)]', '', position))
                    except ValueError:
                        pass
                    else:
                        if abs(occupancy - 1) > epsilon:
                            return True

        return partial_occupancies

    @property
    def has_attached_hydrogens(self) -> bool:
        """Check if there are hydrogens without coordinates, specified as attached
        to the atoms of the structure.

        :returns: True if there are attached hydrogens, False otherwise.
        """
        tag = '_atom_site_attached_hydrogens'
        for datablock in self.values.keys():
            if tag in self.values[datablock].keys():
                for value in self.values[datablock][tag]:
                    if value not in ['.', '?', '0']:
                        return True

        return False

    @property
    def has_undefined_atomic_sites(self) -> bool:
        """Return whether the cif data contains any undefined atomic sites.

        An undefined atomic site is defined as a site where at least one of the fractional coordinates specified in the
        `_atom_site_fract_*` tags, cannot be successfully interpreted as a float. If the cif data contains any site that
        matches this description, or it does not contain any atomic site tags at all, the cif data is said to have
        undefined atomic sites.

        :return: boolean, True if no atomic sites are defined or if any of the defined sites contain undefined positions
            and False otherwise
        """
        tag_x = '_atom_site_fract_x'
        tag_y = '_atom_site_fract_y'
        tag_z = '_atom_site_fract_z'

        # Some CifData files do not even contain a single `_atom_site_fract_*` tag
        has_tags = False

        for datablock in self.values.keys():
            for tag in [tag_x, tag_y, tag_z]:
                if tag in self.values[datablock].keys():
                    for position in self.values[datablock][tag]:
                        # The CifData contains at least one `_atom_site_fract_*` tag
                        has_tags = True

                        try:
                            # First remove any parentheses to support value like 1.134(56) and then cast to float
                            float(re.sub(r'[\(\)]', '', position))
                        except ValueError:
                            # Position cannot be converted to a float value, so we have undefined atomic sites
                            return True

        # At this point the file either has no tags at all, or it does and all coordinates were valid floats
        return not has_tags

    @property
    def has_atomic_sites(self) -> bool:
        """Returns whether there are any atomic sites defined in the cif data. That
        is to say, it will check all the values for the `_atom_site_fract_*` tags
        and if they are all equal to `?` that means there are no relevant atomic
        sites defined and the function will return False. In all other cases the
        function will return True

        :returns: False when at least one atomic site fractional coordinate is not
            equal to `?` and True otherwise
        """
        tag_x = '_atom_site_fract_x'
        tag_y = '_atom_site_fract_y'
        tag_z = '_atom_site_fract_z'
        coords = []
        for datablock in self.values.keys():
            for tag in [tag_x, tag_y, tag_z]:
                if tag in self.values[datablock].keys():
                    coords.extend(self.values[datablock][tag])

        return not all(coord == '?' for coord in coords)

    @property
    def has_unknown_species(self) -> bool | None:
        """Returns whether the cif contains atomic species that are not recognized by AiiDA.

        The known species are taken from the elements dictionary in `aiida.common.constants`, with the exception of
        the "unknown" placeholder element with symbol 'X', as this could not be used to construct a real structure.
        If any of the formula of the cif data contain species that are not in that elements dictionary, the function
        will return True and False in all other cases. If there is no formulae to be found, it will return None

        :returns: True when there are unknown species in any of the formulae, False if not, None if no formula found
        """
        from aiida.common.constants import elements

        # Get all the elements known by AiiDA, excluding the "unknown" element with symbol 'X'
        known_species = [element['symbol'] for element in elements.values() if element['symbol'] != 'X']

        for formula in self.get_formulae():
            if formula is None:
                return None

            species = parse_formula(formula).keys()
            if any(specie not in known_species for specie in species):
                return True

        return False

    @classmethod
    def get_or_create(
        cls,
        filename: str,
        use_first: bool = False,
        store_cif: bool = True,
    ) -> tuple[Self, bool]:
        """Pass the same parameter of the init; if a file with the same md5
        is found, that CifData is returned.

        :param filename: an absolute filename on disk
        :param use_first: if False (default), raise an exception if more than \
                one CIF file is found.\
                If it is True, instead, use the first available CIF file.
        :param bool store_cif: If false, the CifData objects are not stored in
                the database. default=True.
        :return (cif, created): where cif is the CifData object, and create is either\
            True if the object was created, or False if the object was retrieved\
            from the DB.
        """
        import os

        from aiida.common.files import md5_file

        if not os.path.isabs(filename):
            raise ValueError('filename must be an absolute path')
        md5 = md5_file(filename)

        cifs = cls.from_md5(md5)
        if not cifs:
            instance = cls.from_path(filename)
            if store_cif:
                instance.store()
            return instance, True

        if len(cifs) > 1:
            if use_first:
                return cifs[0], False

            raise ValueError(
                'More than one copy of a CIF file with the same MD5 has been found in the DB. pks={}'.format(
                    ','.join([str(i.pk) for i in cifs])
                )
            )

        return cifs[0], False

    @t.overload
    @staticmethod
    def read_cif(fileobj: str | t.IO[t.Any], index: None, **kwargs: t.Any) -> list[Atoms]: ...

    @t.overload
    @staticmethod
    def read_cif(fileobj: str | t.IO[t.Any], index: int = -1, **kwargs: t.Any) -> Atoms: ...

    @staticmethod
    def read_cif(
        fileobj: str | t.IO[t.Any],
        index: int | None = -1,
        **kwargs: t.Any,
    ) -> Atoms | list[Atoms]:
        """A wrapper method that simulates the behavior of the old
        function ase.io.cif.read_cif by using the new generic ase.io.read
        function.

        Somewhere from 3.12 to 3.17 the tag concept was bundled with each Atom object. When
        reading a CIF file, this is incremented and signifies the atomic species, even though
        the CIF file do not have specific tags embedded. On reading CIF files we thus force the
        ASE tag to zero for all Atom elements.

        """
        from ase.io import read

        # The read function returns a list as a cif file might contain multiple
        # structures.
        struct_list = read(fileobj, index=':', format='cif', **kwargs)

        if index is None:
            # If index is explicitly set to None, the list is returned as such.
            for atoms_entry in struct_list:
                atoms_entry.set_tags(0)
            return struct_list

        # Otherwise return the desired structure specified by index, if no index is specified,
        # the last structure is assumed by default.
        struct_list[index].set_tags(0)
        return struct_list[index]

    def get_ase(self, **kwargs: t.Any) -> Atoms:
        """Returns ASE object, representing the CIF. This function differs
        from the property ``ase`` by the possibility to pass the keyworded
        arguments (kwargs) to ase.io.cif.read_cif().

        .. note:: requires ASE module.
        """
        if not kwargs and self._ase:
            return self.ase
        with self.open() as handle:
            return CifData.read_cif(handle, **kwargs)

    def set_ase(self, aseatoms: Atoms) -> None:
        """Set the contents of the CifData starting from an ASE atoms object

        :param aseatoms: the ASE atoms object
        """
        import tempfile

        cif = cif_from_ase(aseatoms)
        with tempfile.NamedTemporaryFile(mode='w+') as temp:
            with Capturing():
                temp.write(pycifrw_from_cif(cif, loops=ase_loops).WriteOut())
            temp.flush()
            self.set_file(temp.name)

    def set_values(self, values: CifFile) -> None:
        """Set internal representation to `values`.

        Warning: This also writes a new CIF file.

        :param values: PyCifRW CifFile object

        .. note:: requires PyCifRW module.
        """
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w+') as temp:
            with Capturing():
                temp.write(values.WriteOut())
            temp.flush()
            temp.seek(0)
            self.set_file(temp)

        self._values = values

    def parse(self, scan_type: Literal['standard', 'flex'] | None = None) -> None:
        """Parses CIF file and sets attributes.

        :param scan_type:  See set_scan_type
        """
        if scan_type is not None:
            self.set_scan_type(scan_type)

        # Note: this causes parsing, if not already parsed
        self.base.attributes.set('formulae', self.get_formulae())
        self.base.attributes.set('spacegroup_numbers', self.get_spacegroup_numbers())

    def store(self, *args: t.Any, **kwargs: t.Any) -> Self:
        """Store the node."""
        if not self.is_stored:
            # We need to first run validation on the parent `SinglefileData` to ensure the `filename` is set,
            # in case the file was added after the node was created (but clearly not yet stored)
            super()._validate()
            self.base.attributes.set('md5', self.generate_md5())

        return super().store(*args, **kwargs)

    def set_file(self, file: FilePath | t.BinaryIO, filename: FilePath | None = None) -> None:
        """Set the file.

        If the source is set and the MD5 checksum of new file
        is different from the source, the source has to be deleted.

        :param file: filepath or filelike object of the CIF file to store.
            Hint: Pass io.BytesIO(b"my string") to construct the file directly from a string.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        super().set_file(file, filename=filename)
        md5sum = self.generate_md5()

        if (
            isinstance(self.source, dict)
            and self.source.get('source_md5', None) is not None
            and self.source['source_md5'] != md5sum
        ):
            self.source = {}

        self.base.attributes.set('md5', md5sum)

        self._values = None
        self._ase = None
        self.base.attributes.set('formulae', None)
        self.base.attributes.set('spacegroup_numbers', None)

    def get_formulae(
        self,
        mode: str = 'sum',
        custom_tags: str | Sequence[str] | None = None,
    ) -> list[str | None]:
        """Return chemical formulae specified in CIF file.

        Note: This does not compute the formula, it only reads it from the
        appropriate tag. Use refine_inline to compute formulae.
        """
        # note: If formulae are not None, they could be returned
        # directly (but the function is very cheap anyhow).
        formula_tags = [f'_chemical_formula_{mode}']
        if custom_tags:
            if isinstance(custom_tags, str):
                custom_tags = [custom_tags]
            formula_tags.extend(custom_tags)

        formulae = []
        for datablock in self.values.keys():
            formula = None
            for formula_tag in formula_tags:
                if formula_tag in self.values[datablock].keys():
                    formula = self.values[datablock][formula_tag]
                    break
            formulae.append(formula)

        return formulae

    def get_spacegroup_numbers(self) -> list[int | None]:
        """Get the spacegroup international number."""
        # note: If spacegroup_numbers are not None, they could be returned
        # directly (but the function is very cheap anyhow).
        spg_tags = ['_space_group.it_number', '_space_group_it_number', '_symmetry_int_tables_number']
        spacegroup_numbers = []
        for datablock in self.values.keys():
            spacegroup_number = None
            correct_tags = [tag for tag in spg_tags if tag in self.values[datablock].keys()]
            if correct_tags:
                try:
                    spacegroup_number = int(self.values[datablock][correct_tags[0]])
                except ValueError:
                    pass
            spacegroup_numbers.append(spacegroup_number)

        return spacegroup_numbers

    def generate_md5(self) -> str:
        """Computes and returns MD5 hash of the CIF file."""
        from aiida.common.files import md5_from_filelike

        # Open in binary mode which is required for generating the md5 checksum
        with self.open(mode='rb') as handle:
            return md5_from_filelike(handle)

    def get_structure(
        self,
        converter: str = 'pymatgen',
        store: bool = False,
        **kwargs: t.Any,
    ) -> StructureData:
        """Creates :py:class:`aiida.orm.nodes.data.structure.StructureData`.

        :param converter: specify the converter. Default 'pymatgen'.
        :param store: if True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :param primitive_cell: if True, primitive cell is returned,
            conventional cell if False. Default False.
        :param occupancy_tolerance: If total occupancy of a site is between 1 and occupancy_tolerance,
            the occupancies will be scaled down to 1. (pymatgen only)
        :param site_tolerance: This tolerance is used to determine if two sites are sitting in the same position,
            in which case they will be combined to a single disordered site. Defaults to 1e-4. (pymatgen only)
        :return: :py:class:`aiida.orm.nodes.data.structure.StructureData` node.
        """
        from aiida.orm import Dict
        from aiida.tools.data import cif as cif_tools

        parameters = Dict(**kwargs)

        try:
            convert_function = getattr(cif_tools, f'_get_aiida_structure_{converter}_inline')
        except AttributeError:
            raise ValueError(f"No such converter '{converter}' available")

        result = convert_function(
            cif=self,
            parameters=parameters,
            metadata={'store_provenance': store},
        )

        return result['structure']

    def initialize(self) -> None:
        super().initialize()
        self._values: CifFile | None = None
        self._ase: Atoms | None = None

    def _prepare_cif(self, **kwargs: t.Any) -> tuple[bytes, dict[str, t.Any]]:
        """Return CIF string of CifData object.

        If parsed values are present, a CIF string is created and written to file. If no parsed values are present, the
        CIF string is read from file.
        """
        with self.open(mode='rb') as handle:
            return handle.read(), {}

    def _get_object_ase(self) -> Atoms:
        """Converts CifData to ase.Atoms

        :return: an ase.Atoms object
        """
        return self.ase

    def _get_object_pycifrw(self) -> CifFile:
        """Converts CifData to PyCIFRW.CifFile

        :return: a PyCIFRW.CifFile object
        """
        return self.values

    def _validate(self) -> None:
        """Validates MD5 hash of CIF file."""
        from aiida.common.exceptions import ValidationError

        super()._validate()

        if self.md5 is None:
            raise ValidationError("attribute 'md5' not set.")

        md5 = self.generate_md5()
        if self.md5 != md5:
            raise ValidationError(f"Attribute 'md5' says '{self.md5}' but '{md5}' was parsed instead.")

    # TODO the following methods are handled above via property operations - consider removing

    def set_scan_type(self, scan_type: Literal['standard', 'flex']) -> None:
        """Set the scan_type for PyCifRW.

        The 'flex' scan_type of PyCifRW is faster for large CIF files but
        does not yet support the CIF2 format as of 02/2018.
        See the CifFile.ReadCif function

        :param scan_type: Either 'standard' or 'flex' (see _scan_types)
        """
        self.scan_type = scan_type

    def set_parse_policy(self, parse_policy: Literal['eager', 'lazy']) -> None:
        """Set the parse policy.

        :param parse_policy: Either 'eager' (parse CIF file on set_file)
            or 'lazy' (defer parsing until needed)
        """
        self.parse_policy = parse_policy
