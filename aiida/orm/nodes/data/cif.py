# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-many-locals,too-many-statements
"""Tools for handling Crystallographic Information Files (CIF)"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from aiida.common.utils import Capturing

from .singlefile import SinglefileData

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
    """
    :return: True if the PyCifRW module can be imported, False otherwise.
    """
    # pylint: disable=unused-variable,unused-import
    try:
        import CifFile
        from CifFile import CifBlock
    except ImportError:
        return False
    return True


def cif_from_ase(ase, full_occupancies=False, add_fake_biso=False):
    """
    Construct a CIF datablock from the ASE structure. The code is taken
    from
    https://wiki.fysik.dtu.dk/ase/epydoc/ase.io.cif-pysrc.html#write_cif,
    as the original ASE code contains a bug in printing the
    Hermann-Mauguin symmetry space group symbol.

    :param ase: ASE "images"
    :return: array of CIF datablocks
    """
    from numpy import arccos, pi, dot
    from numpy.linalg import norm

    if not isinstance(ase, (list, tuple)):
        ase = [ase]

    datablocks = []
    for _, atoms in enumerate(ase):
        datablock = dict()

        cell = atoms.cell
        a = norm(cell[0])
        b = norm(cell[1])
        c = norm(cell[2])
        alpha = arccos(dot(cell[1], cell[2]) / (b * c)) * 180. / pi
        beta = arccos(dot(cell[0], cell[2]) / (a * c)) * 180. / pi
        gamma = arccos(dot(cell[0], cell[1]) / (a * b)) * 180. / pi

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


# pylint: disable=too-many-branches
def pycifrw_from_cif(datablocks, loops=None, names=None):
    """
    Constructs PyCifRW's CifFile from an array of CIF datablocks.

    :param datablocks: an array of CIF datablocks
    :param loops: optional dict of lists of CIF tag loops.
    :param names: optional list of datablock names
    :return: CifFile
    """
    try:
        import CifFile
        from CifFile import CifBlock
    except ImportError as exc:
        raise ImportError(str(exc) + '. You need to install the PyCifRW package.')

    if loops is None:
        loops = dict()

    cif = CifFile.CifFile()  # pylint: disable=no-member
    try:
        cif.set_grammar("1.1")
    except AttributeError:
        # if no grammar can be set, we assume it's 1.1 (widespread standard)
        pass

    if names and len(names) < len(datablocks):
        raise ValueError("Not enough names supplied for "
                         "datablocks: {} (names) < "
                         "{} (datablocks)".format(len(names), len(datablocks)))
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
                        raise ValueError("Number of values for tag "
                                         "'{}' is different from "
                                         "the others in the same "
                                         "loop".format(tag))
                    if row_size == 0:
                        continue
                    datablock.AddItem(tag, tag_values)
                    tags_seen.append(tag)
                    tags_in_loops.append(tag)
            if row_size is not None and row_size > 0:
                datablock.CreateLoop(datanames=tags_seen)
        for tag in sorted(values.keys()):
            if not tag in tags_in_loops:
                datablock.AddItem(tag, values[tag])
                # create automatically a loop for non-scalar values
                if isinstance(values[tag], (tuple, list)) and tag not in loops.keys():
                    datablock.CreateLoop([tag])
    return cif


def parse_formula(formula):
    """
    Parses the Hill formulae, written with spaces for separators.
    """
    import re

    contents = {}
    for part in re.split(r'\s+', formula):
        m = re.match(r'(\D+)([\.\d]+)?', part)

        if m is None:
            continue

        specie = m.group(1)
        quantity = m.group(2)
        if quantity is None:
            quantity = 1
        else:
            if re.match(r'^\d+$', quantity):
                quantity = int(quantity)
            else:
                quantity = float(quantity)
        contents[specie] = quantity
    return contents


# pylint: disable=abstract-method,too-many-public-methods
# Note:  Method 'query' is abstract in class 'Node' but is not overridden
class CifData(SinglefileData):
    """
    Wrapper for Crystallographic Interchange File (CIF)

    .. note:: the file (physical) is held as the authoritative source of
        information, so all conversions are done through the physical file:
        when setting ``ase`` or ``values``, a physical CIF file is generated
        first, the values are updated from the physical CIF file.
    """
    # pylint: disable=abstract-method, too-many-public-methods
    _set_incompatibilities = [('ase', 'file'), ('ase', 'values'), ('file', 'values')]
    _scan_types = ('standard', 'flex')
    _parse_policies = ('eager', 'lazy')
    _values = None
    _ase = None

    def __init__(self,
                 ase=None,
                 file=None,
                 values=None,
                 source=None,
                 scan_type='standard',
                 parse_policy='eager',
                 **kwargs):
        # pylint: disable=too-many-arguments, redefined-builtin

        args = {
            'ase': ase,
            'file': file,
            'values': values,
        }

        for left, right in self._set_incompatibilities:
            if args[left] is not None and args[right] is not None:
                raise ValueError('cannot pass {} and {} at the same time'.format(left, right))

        super(CifData, self).__init__(file, **kwargs)
        self.set_scan_type(scan_type)
        self.set_parse_policy(parse_policy)

        if source is not None:
            self.set_source(source)

        if ase is not None:
            self.set_ase(ase)

        if values is not None:
            self.set_values(values)

        if not self.is_stored and file is not None and self.get_attribute('parse_policy') == 'eager':
            self.parse()

    @staticmethod
    def read_cif(fileobj, index=-1, **kwargs):
        """
        A wrapper method that simulates the behavior of the old
        function ase.io.cif.read_cif by using the new generic ase.io.read
        function.
        """
        from ase.io import read

        # the read function returns a list as a cif file might contain multiple
        # structures
        struct_list = read(fileobj, index=':', format='cif', **kwargs)

        if index is None:
            # If index is explicitely set to None, the list is returned as such.
            return struct_list
        # otherwise return the desired structure specified by index.
        # If no index is specified, the last structure is assumed by default
        return struct_list[index]

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all CIF files that match a given MD5 hash.

        .. note:: the hash has to be stored in a ``_md5`` attribute,
            otherwise the CIF file will not be found.
        """
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(cls, filters={'attributes.md5': {'==': md5}})
        return [_ for [_] in qb.all()]

    @classmethod
    def get_or_create(cls, filename, use_first=False, store_cif=True):
        """
        Pass the same parameter of the init; if a file with the same md5
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

        if not os.path.abspath(filename):
            raise ValueError("filename must be an absolute path")
        md5 = md5_file(filename)

        cifs = cls.from_md5(md5)
        if not cifs:
            if store_cif:
                instance = cls(file=filename).store()
                return (instance, True)
            instance = cls(file=filename)
            return (instance, True)

        if len(cifs) > 1:
            if use_first:
                return (cifs[0], False)

            raise ValueError("More than one copy of a CIF file "
                             "with the same MD5 has been found in "
                             "the DB. pks={}".format(",".join([str(i.pk) for i in cifs])))

        return cifs[0], False

    # pylint: disable=attribute-defined-outside-init
    @property
    def ase(self):
        """
        ASE object, representing the CIF.

        .. note:: requires ASE module.
        """
        if self._ase is None:
            self._ase = self.get_ase()
        return self._ase

    def get_ase(self, **kwargs):
        """
        Returns ASE object, representing the CIF. This function differs
        from the property ``ase`` by the possibility to pass the keyworded
        arguments (kwargs) to ase.io.cif.read_cif().

        .. note:: requires ASE module.
        """
        if not kwargs and self._ase:
            return self.ase
        return CifData.read_cif(self.open(), **kwargs)

    def set_ase(self, aseatoms):
        """
        Set the contents of the CifData starting from an ASE atoms object

        :param aseatoms: the ASE atoms object
        """
        import tempfile
        cif = cif_from_ase(aseatoms)
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            with Capturing():
                tmpf.write(pycifrw_from_cif(cif, loops=ase_loops).WriteOut())
            tmpf.flush()
            self.set_file(tmpf.name)

    @ase.setter
    def ase(self, aseatoms):
        self.set_ase(aseatoms)

    @property
    def values(self):
        """
        PyCifRW structure, representing the CIF datablocks.

        .. note:: requires PyCifRW module.
        """
        if self._values is None:
            import CifFile
            from CifFile import CifBlock  # pylint: disable=no-name-in-module

            with self.open() as handle:
                c = CifFile.ReadCif(handle, scantype=self.get_attribute('scan_type'))  # pylint: disable=no-member
            for k, v in c.items():
                c.dictionary[k] = CifBlock(v)
            self._values = c
        return self._values

    def set_values(self, values):
        """
        Set internal representation to `values`.

        Warning: This also writes a new CIF file.

        :param values: PyCifRW CifFile object

        .. note:: requires PyCifRW module.
        """
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            with Capturing():
                tmpf.write(values.WriteOut())
            tmpf.flush()
            self.set_file(tmpf.name)

        self._values = values

    @values.setter
    def values(self, values):
        self.set_values(values)

    def parse(self, scan_type=None):
        """
        Parses CIF file and sets attributes.

        :param scan_type:  See set_scan_type
        """
        if scan_type is not None:
            self.set_scan_type(scan_type)

        # Note: this causes parsing, if not already parsed
        self.set_attribute('formulae', self.get_formulae())
        self.set_attribute('spacegroup_numbers', self.get_spacegroup_numbers())

    # pylint: disable=arguments-differ
    def store(self, *args, **kwargs):
        """
        Store the node.
        """
        if not self.is_stored:
            self.set_attribute('md5', self.generate_md5())

        return super(CifData, self).store(*args, **kwargs)

    def set_file(self, file):
        """
        Set the file.

        If the source is set and the MD5 checksum of new file
        is different from the source, the source has to be deleted.
        """
        # pylint: disable=redefined-builtin
        super(CifData, self).set_file(file)
        md5sum = self.generate_md5()
        if isinstance(self.source, dict) and \
                self.source.get('source_md5', None) is not None and \
                self.source['source_md5'] != md5sum:
            self.source = {}
        self.set_attribute('md5', md5sum)

        self._values = None
        self._ase = None
        self.set_attribute('formulae', None)
        self.set_attribute('spacegroup_numbers', None)

    def set_scan_type(self, scan_type):
        """
        Set the scan_type for PyCifRW.

        The 'flex' scan_type of PyCifRW is faster for large CIF files but
        does not yet support the CIF2 format as of 02/2018.
        See the CifFile.ReadCif function

        :param scan_type: Either 'standard' or 'flex' (see _scan_types)
        """
        if scan_type in self._scan_types:
            self.set_attribute('scan_type', scan_type)
        else:
            raise ValueError("Got unknown scan_type {}".format(scan_type))

    def set_parse_policy(self, parse_policy):
        """
        Set the parse policy.

        :param parse_policy: Either 'eager' (parse CIF file on set_file)
            or 'lazy' (defer parsing until needed)
        """
        if parse_policy in self._parse_policies:
            self.set_attribute('parse_policy', parse_policy)
        else:
            raise ValueError("Got unknown parse_policy {}".format(parse_policy))

    def get_formulae(self, mode='sum'):
        """
        Return chemical formulae specified in CIF file.

        Note: This does not compute the formula, it only reads it from the
        appropriate tag. Use refine_inline to compute formulae.
        """
        # note: If formulae are not None, they could be returned
        # directly (but the function is very cheap anyhow).
        formula_tag = "_chemical_formula_{}".format(mode)
        formulae = []
        for datablock in self.values.keys():
            formula = None
            if formula_tag in self.values[datablock].keys():
                formula = self.values[datablock][formula_tag]
            formulae.append(formula)

        return formulae

    def get_spacegroup_numbers(self):
        """
        Get the spacegroup international number.
        """
        # note: If spacegroup_numbers are not None, they could be returned
        # directly (but the function is very cheap anyhow).
        spg_tags = ["_space_group.it_number", "_space_group_it_number", "_symmetry_int_tables_number"]
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

    @property
    def has_partial_occupancies(self):
        """
        Return if the cif data contains partial occupancies

        A partial occupancy is defined as site with an occupancy that differs from unity, within a precision of 1E-6

        .. note: occupancies that cannot be parsed into a float are ignored

        :return: True if there are partial occupancies, False otherwise
        """
        import re

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
    def has_attached_hydrogens(self):
        """
        Check if there are hydrogens without coordinates, specified as attached
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
    def has_undefined_atomic_sites(self):
        """
        Return whether the cif data contains any undefined atomic sites.

        An undefined atomic site is defined as a site where at least one of the fractional coordinates specified in the
        `_atom_site_fract_*` tags, cannot be successfully interpreted as a float. If the cif data contains any site that
        matches this description, or it does not contain any atomic site tags at all, the cif data is said to have
        undefined atomic sites.

        :return: boolean, True if no atomic sites are defined or if any of the defined sites contain undefined positions
            and False otherwise
        """
        import re

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
    def has_atomic_sites(self):
        """
        Returns whether there are any atomic sites defined in the cif data. That
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

        return not all([coord == '?' for coord in coords])

    @property
    def has_unknown_species(self):
        """
        Returns whether the cif contains atomic species that are not recognized by AiiDA.

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
            if any([specie not in known_species for specie in species]):
                return True

        return False

    def generate_md5(self):
        """
        Computes and returns MD5 hash of the CIF file.
        """
        from aiida.common.files import md5_from_filelike

        # Open in binary mode which is required for generating the md5 checksum
        with self.open(mode='rb') as handle:
            return md5_from_filelike(handle)

    def _get_aiida_structure(self, converter='pymatgen', store=False, **kwargs):
        """
        Creates :py:class:`aiida.orm.nodes.data.structure.StructureData`.

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
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn(  # pylint: disable=no-member
            'This method has been deprecated and will be renamed to get_structure() in AiiDA v1.0', DeprecationWarning)
        return self.get_structure(converter=converter, store=store, **kwargs)

    def get_structure(self, converter='pymatgen', store=False, **kwargs):
        """
        Creates :py:class:`aiida.orm.nodes.data.structure.StructureData`.

        .. versionadded:: 1.0
           Renamed from _get_aiida_structure

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

        parameters = Dict(dict=kwargs)

        try:
            convert_function = getattr(cif_tools, '_get_aiida_structure_{}_inline'.format(converter))
        except AttributeError:
            raise ValueError("No such converter '{}' available".format(converter))

        result = convert_function(cif=self, parameters=parameters, metadata={'store_provenance': store})

        return result['structure']

    # pylint: disable=unused-argument
    def _prepare_cif(self, main_file_name=""):
        """
        Return CIF string of CifData object.

        If parsed values are present, a CIF string is created
        and written to file.
        If no parsed values are present, the CIF string is read
        from file.
        """
        if self._values and not self.is_stored:
            # Note: this overwrites the CIF file!
            self.set_values(self._values)

        with self.open() as handle:
            return handle.read().encode('utf-8'), {}

    def _get_object_ase(self):
        """
        Converts CifData to ase.Atoms

        :return: an ase.Atoms object
        """
        return self.ase

    def _get_object_pycifrw(self):
        """
        Converts CifData to PyCIFRW.CifFile

        :return: a PyCIFRW.CifFile object
        """
        return self.values

    def _validate(self):
        """
        Validates MD5 hash of CIF file.
        """
        from aiida.common.exceptions import ValidationError

        super(CifData, self)._validate()

        try:
            attr_md5 = self.get_attribute('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")
        md5 = self.generate_md5()
        if attr_md5 != md5:
            raise ValidationError("Attribute 'md5' says '{}' but '{}' was parsed instead.".format(attr_md5, md5))
