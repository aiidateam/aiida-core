# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.data.singlefile import SinglefileData
from aiida.orm.calculation.inline import optional_inline


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

symmetry_tags = [
    '_symmetry_equiv_pos_site_id',
    '_symmetry_equiv_pos_as_xyz',

    '_symmetry_Int_Tables_number',
    '_symmetry_space_group_name_H-M',
    '_symmetry_space_group_name_Hall',

    '_space_group_symop_id',
    '_space_group_symop_operation_xyz',
    '_space_group_symop_sg_id',

    '_space_group_id',
    '_space_group_IT_number',
    '_space_group_name_H-M_alt',
    '_space_group_name_Hall',
]


def has_pycifrw():
    """
    :return: True if the PyCifRW module can be imported, False otherwise.
    """
    try:
        import CifFile
    except ImportError:
        return False
    return True


def symop_string_from_symop_matrix_tr(matrix, tr=(0, 0, 0), eps=0):
    """
    Construct a CIF representation of symmetry operator plus translation.
    See International Tables for Crystallography Vol. A. (2002) for
    definition.

    :param matrix: 3x3 matrix, representing the symmetry operator
    :param tr: translation vector of length 3 (default 0)
    :param eps: epsilon parameter for fuzzy comparison x == 0
    :return: CIF representation of symmetry operator
    """
    import re
    axes = ["x", "y", "z"]
    parts = ["", "", ""]
    for i in range(0, 3):
        for j in range(0, 3):
            sign = None
            if matrix[i][j] > eps:
                sign = "+"
            elif matrix[i][j] < -eps:
                sign = "-"
            if sign:
                parts[i] = format("{}{}{}".format(parts[i], sign, axes[j]))
        if tr[i] < -eps or tr[i] > eps:
            sign = "+"
            if tr[i] < -eps:
                sign = "-"
            parts[i] = format("{}{}{}".format(parts[i], sign, abs(tr[i])))
        parts[i] = re.sub('^\+', '', parts[i])
    return ",".join(parts)


@optional_inline
def _get_aiida_structure_ase_inline(cif=None, parameters=None):
    """
    Creates :py:class:`aiida.orm.data.structure.StructureData` using ASE.

    .. note:: unable to correctly import structures of alloys.
    .. note:: requires ASE module.
    """
    from aiida.orm.data.structure import StructureData

    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    return {'structure': StructureData(ase=cif.get_ase(**kwargs))}


@optional_inline
def _get_aiida_structure_pymatgen_inline(cif=None, parameters=None):
    """
    Creates :py:class:`aiida.orm.data.structure.StructureData` using
    pymatgen.

    .. note:: requires pymatgen module.
    """
    from pymatgen.io.cif import CifParser
    from aiida.orm.data.structure import StructureData

    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    kwargs['primitive'] = kwargs.pop('primitive_cell', False)
    parser = CifParser(cif.get_file_abs_path())
    try:
        struct = parser.get_structures(**kwargs)[0]
        return {'structure': StructureData(pymatgen_structure=struct)}
    except IndexError:
        raise ValueError("pymatgen failed to provide a structure from the cif file")


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
    for i, atoms in enumerate(ase):
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


def pycifrw_from_cif(datablocks, loops=dict(), names=None):
    """
    Constructs PyCifRW's CifFile from an array of CIF datablocks.

    :param datablocks: an array of CIF datablocks
    :param loops: optional list of lists of CIF tag loops.
    :param names: optional list of datablock names
    :return: CifFile
    """
    import CifFile

    cif = CifFile.CifFile()
    if names and len(names) < len(datablocks):
        raise ValueError("Not enough names supplied for "
                         "datablocks: {} (names) < "
                         "{} (datablocks)".format(len(names),
                                                  len(datablocks)))
    for i, values in enumerate(datablocks):
        name = str(i)
        if names:
            name = names[i]
        cif.NewBlock(name)
        datablock = cif[name]
        for loopname in loops.keys():
            loopdata = ([[]], [[]])
            row_size = None
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
                    loopdata[0][0].append(tag)
                    loopdata[1][0].append(tag_values)
            if row_size is not None and row_size > 0:
                datablock.AddCifItem(loopdata)
        for tag in sorted(values.keys()):
            datablock[tag] = values[tag]
    return cif


@optional_inline
def refine_inline(node):
    """
    Refine (reduce) the cell of :py:class:`aiida.orm.data.cif.CifData`,
    find and remove symmetrically equivalent atoms.

    :param node: a :py:class:`aiida.orm.data.cif.CifData` instance.
    :return: dict with :py:class:`aiida.orm.data.cif.CifData`

    .. note:: can be used as inline calculation.
    """
    from aiida.orm.data.structure import StructureData, ase_refine_cell

    if len(node.values.keys()) > 1:
        raise ValueError("CifData seems to contain more than one data "
                         "block -- multiblock CIF files are not "
                         "supported yet")

    name = node.values.keys()[0]

    original_atoms = node.get_ase(index=None)
    if len(original_atoms) > 1:
        raise ValueError("CifData seems to contain more than one crystal "
                         "structure -- such refinement is not supported "
                         "yet")

    original_atoms = original_atoms[0]

    refined_atoms, symmetry = ase_refine_cell(original_atoms)

    cif = CifData(ase=refined_atoms)
    cif.values.dictionary[name] = cif.values.dictionary.pop(str(0))

    # Remove all existing symmetry tags before overwriting:
    for tag in symmetry_tags:
        cif.values[name].RemoveCifItem(tag)

    cif.values[name]['_symmetry_space_group_name_H-M'] = symmetry['hm']
    cif.values[name]['_symmetry_space_group_name_Hall'] = symmetry['hall']
    cif.values[name]['_symmetry_Int_Tables_number'] = symmetry['tables']
    cif.values[name]['_symmetry_equiv_pos_as_xyz'] = \
        [symop_string_from_symop_matrix_tr(symmetry['rotations'][i],
                                           symmetry['translations'][i])
         for i in range(0, len(symmetry['rotations']))]

    # Summary formula has to be calculated from non-reduced set of atoms.
    cif.values[name]['_chemical_formula_sum'] = \
        StructureData(ase=original_atoms).get_formula(mode='hill',
                                                      separator=' ')

    # If the number of reduced atoms multiplies the number of non-reduced
    # atoms, the new Z value can be calculated.
    if '_cell_formula_units_Z' in node.values[name].keys():
        old_Z = node.values[name]['_cell_formula_units_Z']
        if len(original_atoms) % len(refined_atoms):
            new_Z = old_Z * len(original_atoms) / len(refined_atoms)
            cif.values[name]['_cell_formula_units_Z'] = new_Z

    return {'cif': cif}


def parse_formula(formula):
    """
    Parses the Hill formulae, written with spaces for separators.
    """
    import re

    contents = {}
    for part in re.split('\s+', formula):
        m = re.match('(\D+)([\.\d]+)?', part)
        specie = m.group(1)
        quantity = m.group(2)
        if quantity is None:
            quantity = 1
        else:
            if re.match('^\d+$', quantity):
                quantity = int(quantity)
            else:
                quantity = float(quantity)
        contents[specie] = quantity
    return contents


class CifData(SinglefileData):
    """
    Wrapper for Crystallographic Interchange File (CIF)

    .. note:: the file (physical) is held as the authoritative source of
        information, so all conversions are done through the physical file:
        when setting ``ase`` or ``values``, a physical CIF file is generated
        first, the values are updated from the physical CIF file.
    """
    _set_incompatibilities = [("ase", "file"), ("ase", "values"),
                              ("file", "values")]

    @staticmethod
    def read_cif(fileobj, index=-1, **kwargs):
        """
        A wrapper method that simulates the behavior of the old
        function ase.io.cif.read_cif by using the new generic ase.io.read
        function.
        """
        from ase.io import read

        #the read function returns a list as a cif file might contain multiple
        # structures
        struct_list = read(fileobj, index=':', format='cif', **kwargs)

        if index is None:
            # If index is explicitely set to None, the list is returned as such.
            return struct_list
        else:
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
        import aiida.common.utils
        import os
        from aiida.common.exceptions import ParsingError

        if not os.path.abspath(filename):
            raise ValueError("filename must be an absolute path")
        md5 = aiida.common.utils.md5_file(filename)

        cifs = cls.from_md5(md5)
        if len(cifs) == 0:
            if store_cif:
                instance = cls(file=filename).store()
                return (instance, True)
            else:
                instance = cls(file=filename)
                return (instance, True)
        else:
            if len(cifs) > 1:
                if use_first:
                    return (cifs[0], False)
                else:
                    raise ValueError(
                        "More than one copy of a CIF file "
                        "with the same MD5 has been found in "
                        "the DB. pks={}".format(
                            ",".join([str(i.pk) for i in cifs])))
            else:
                return cifs[0], False

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
        else:
            return CifData.read_cif(
                self._get_folder_pathsubfolder.open(self.filename), **kwargs)

    def set_ase(self, aseatoms):
        import tempfile
        cif = cif_from_ase(aseatoms)
        with tempfile.NamedTemporaryFile() as f:
            f.write(pycifrw_from_cif(cif, loops=ase_loops).WriteOut())
            f.flush()
            self.set_file(f.name)

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
            try:
                import CifFile
            except ImportError as e:
                raise ImportError(str(e) + '. You need to install the PyCifRW package.')
            self._values = CifFile.ReadCif(self.get_file_abs_path())
        return self._values

    def set_values(self, values):
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(values.WriteOut())
            f.flush()
            self.set_file(f.name)

    @values.setter
    def values(self, values):
        self.set_values(values)

    def __init__(self, **kwargs):
        """
        Initialises an instance of CifData.
        """
        super(CifData, self).__init__(**kwargs)
        self._values = None
        self._ase = None

    def store(self, *args, **kwargs):
        """
        Store the node.
        """
        self._set_attr('md5', self.generate_md5())
        return super(CifData, self).store(*args, **kwargs)

    def set_file(self, filename):
        """
        Set the file. If the source is set and the MD5 checksum of new file
        is different from the source, the source has to be deleted.
        """
        super(CifData, self).set_file(filename)
        md5sum = self.generate_md5()
        if isinstance(self.source, dict) and \
                        self.source.get('source_md5', None) is not None and \
                        self.source['source_md5'] != md5sum:
            self.source = {}
        self._set_attr('md5', md5sum)
        self._values = None
        self._ase = None
        self._set_attr('formulae', self.get_formulae())
        self._set_attr('spacegroup_numbers', self.get_spacegroup_numbers())

    def get_formulae(self, mode='sum'):
        """
        Get the formula.
        """
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
        spg_tags = ["_space_group.it_number", "_space_group_it_number",
                    "_symmetry_int_tables_number"]
        spacegroup_numbers = []
        for datablock in self.values.keys():
            spacegroup_number = None
            correct_tags = [tag for tag in spg_tags
                            if tag in self.values[datablock].keys()]
            if correct_tags:
                try:
                    spacegroup_number = int(self.values[datablock][correct_tags[0]])
                except ValueError:
                    pass
            spacegroup_numbers.append(spacegroup_number)
        return spacegroup_numbers

    def has_partial_occupancies(self):
        """
        Check if there are float values in the atom occupancies.
        :return: True if there are partial occupancies, False
        otherwise.
        """
        # precision
        epsilon = 1e-6
        tag = "_atom_site_occupancy"
        partial_occupancies = False
        for datablock in self.values.keys():
            if tag in self.values[datablock].keys():
                for site in self.values[datablock][tag]:
                    # find the float number in the string
                    bracket = site.find('(')
                    if bracket == -1:
                        # no bracket found
                        if abs(float(site) - 1) > epsilon:
                            partial_occupancies = True
                    else:
                        # bracket, cut string
                        if abs(float(site[0:bracket]) - 1) > epsilon:
                            partial_occupancies = True

        return partial_occupancies

    def has_attached_hydrogens(self):
        """
        Check if there are hydrogens without coordinates, specified
        as attached to the atoms of the structure.
        :return: True if there are attached hydrogens, False otherwise.
        """
        tag = '_atom_site_attached_hydrogens'
        for datablock in self.values.keys():
            if tag in self.values[datablock].keys():
                for value in self.values[datablock][tag]:
                    if value != '.' and value != '?' and value != '0':
                        return True
        return False

    def generate_md5(self):
        """
        Generate MD5 hash of the file's contents on-the-fly.
        """
        import aiida.common.utils
        from aiida.common.exceptions import ValidationError

        abspath = self.get_file_abs_path()
        if not abspath:
            raise ValidationError("No valid CIF was passed!")

        return aiida.common.utils.md5_file(abspath)

    def _get_aiida_structure(self, converter='ase', store=False, **kwargs):
        """
        Creates :py:class:`aiida.orm.data.structure.StructureData`.

        :param converter: specify the converter. Default 'ase'.
        :param store: if True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :param primitive_cell: if True, primitive cell is returned,
            conventional cell if False. Default False.
        :return: :py:class:`aiida.orm.data.structure.StructureData` node.
        """
        from aiida.orm.data.parameter import ParameterData
        import cif  # This same module

        param = ParameterData(dict=kwargs)
        try:
            conv_f = getattr(cif, '_get_aiida_structure_{}_inline'.format(converter))
        except AttributeError:
            raise ValueError("No such converter '{}' available".format(converter))
        ret_dict = conv_f(cif=self, parameters=param, store=store)
        return ret_dict['structure']

    def _prepare_cif(self, main_file_name=""):
        """
        Write the given CIF file to a string of format CIF.
        """
        # If values have been changed and node is not stored,
        # the file is updated.
        if self._values and not self.is_stored:
            self.values = self._values
        with self._get_folder_pathsubfolder.open(self.filename) as f:
            return f.read(), {}

    def _prepare_tcod(self, main_file_name="", **kwargs):
        """
        Write the given CIF to a string of format TCOD CIF.
        """
        from aiida.tools.dbexporters.tcod import export_cif
        return export_cif(self, **kwargs).encode('utf-8'), {}

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
        Validate the structure.
        """
        from aiida.common.exceptions import ValidationError

        super(CifData, self)._validate()

        try:
            attr_md5 = self.get_attr('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")
        md5 = self.generate_md5()
        if attr_md5 != md5:
            raise ValidationError("Attribute 'md5' says '{}' but '{}' was "
                                  "parsed instead.".format(attr_md5, md5))
