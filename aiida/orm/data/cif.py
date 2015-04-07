# -*- coding: utf-8 -*-
from aiida.orm.data.singlefile import SinglefileData
from aiida.orm.calculation.inline import optional_inline

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi, Nicolas Mounet"

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
    try:
        import CifFile
    except ImportError:
        return False
    return True

def encode_textfield_base64(content,foldwidth=76):
    """
    Encodes the contents for CIF textfield in Base64.

    :param content: a string with contents
    :param foldwidth: maximum width of line (default is 76)
    :return: encoded string
    """
    import base64
    content = base64.standard_b64encode(content)
    content = "\n".join(list(content[i:i+foldwidth]
                             for i in range(0,len(content),foldwidth)))
    return content

def decode_textfield_base64(content):
    """
    Decodes the contents for CIF textfield from Base64.

    :param content: a string with contents
    :return: decoded string
    """
    import base64
    return base64.standard_b64decode(content)

def encode_textfield_quoted_printable(content):
    """
    Encodes the contents for CIF textfield in quoted-printable encoding.

    :param content: a string with contents
    :return: encoded string
    """
    import re
    import quopri
    content = quopri.encodestring(content)
    def match2qp(m):
        prefix  = ''
        postfix = ''
        if 'prefix' in m.groupdict().keys():
            prefix = m.group('prefix')
        if 'postfix' in m.groupdict().keys():
            postfix = m.group('postfix')
        h = hex(ord(m.group('chr')))[2:].upper()
        if len(h) == 1:
            h = "0{}".format(h)
        return "{}={}{}".format(prefix,h,postfix)
    content = re.sub('^(?P<chr>;)',match2qp,content)
    content = re.sub('(?P<chr>\t)',match2qp,content)
    content = re.sub('(?P<prefix>\n)(?P<chr>;)',match2qp,content)
    content = re.sub('^(?P<chr>[\.\?])$',match2qp,content)
    return content

def decode_textfield_quoted_printable(content):
    """
    Decodes the contents for CIF textfield from quoted-printable encoding.

    :param content: a string with contents
    :return: decoded string
    """
    import quopri
    return quopri.decodestring(content)

def encode_textfield_ncr(content):
    """
    Encodes the contents for CIF textfield in Numeric Character Reference.

    :param content: a string with contents
    :return: encoded string
    """
    import re
    def match2ncr(m):
        prefix = ''
        postfix = ''
        if 'prefix' in m.groupdict().keys():
            prefix = m.group('prefix')
        if 'postfix' in m.groupdict().keys():
            postfix = m.group('postfix')
        return prefix + '&#' + str(ord(m.group('chr'))) + ';' + postfix
    content = re.sub('(?P<chr>[&\t])',match2ncr,content)
    content = re.sub('(?P<chr>[^\x09\x0A\x0D\x20-\x7E])',match2ncr,content)
    content = re.sub('^(?P<chr>;)',match2ncr,content)
    content = re.sub('(?P<prefix>\n)(?P<chr>;)',match2ncr,content)
    content = re.sub('^(?P<chr>[\.\?])$',match2ncr,content)
    return content

def decode_textfield_ncr(content):
    """
    Decodes the contents for CIF textfield from Numeric Character Reference.

    :param content: a string with contents
    :return: decoded string
    """
    import re
    def match2str(m):
        return chr(int(m.group(1)))
    return re.sub('&#(\d+);',match2str,content)

def encode_textfield_gzip_base64(content,**kwargs):
    """
    Gzips the given string and encodes it in Base64.

    :param content: a string with contents
    :return: encoded string
    """
    from aiida.common.utils import gzip_string
    return encode_textfield_base64(gzip_string(content),**kwargs)

def decode_textfield_gzip_base64(content):
    """
    Decodes the contents for CIF textfield from Base64 and decompresses
    them with gzip.

    :param content: a string with contents
    :return: decoded string
    """
    from aiida.common.utils import gunzip_string
    return gunzip_string(decode_textfield_base64(content))

@optional_inline
def _get_aiida_structure_ase_inline(cif=None,parameters=None):
    """
    Creates :py:class:`aiida.orm.data.structure.StructureData` using ASE.

    :note: requires ASE module.
    """
    from aiida.orm.data.structure import StructureData
    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    return {'structure': StructureData(ase=cif.get_ase(**kwargs))}

def cif_from_ase(ase,full_occupancies=False,add_fake_biso=False):
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
        alpha = arccos(dot(cell[1], cell[2])/(b*c))*180./pi
        beta = arccos(dot(cell[0], cell[2])/(a*c))*180./pi
        gamma = arccos(dot(cell[0], cell[1])/(a*b))*180./pi

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

def pycifrw_from_cif(datablocks,loops=dict()):
    """
    Constructs PyCifRW's CifFile from an array of CIF datablocks.

    :param datablocks: an array of CIF datablocks
    :param loops: optional list of lists of CIF tag loops.
    :return: CifFile
    """
    import CifFile
    cif = CifFile.CifFile()
    nr = 0
    for values in datablocks:
        name = str(nr)
        nr = nr + 1
        cif.NewBlock(name)
        datablock = cif[name]
        for loopname in loops.keys():
            loopdata = ([[]],[[]])
            row_size = None
            for tag in loops[loopname]:
                if tag in values:
                    tag_values = values.pop(tag)
                    if not isinstance(tag_values,list):
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

class CifData(SinglefileData):
    """
    Wrapper for Crystallographic Interchange File (CIF)

    :note: the file (physical) is held as the authoritative source of
        information, so all conversions are done through the physical file:
        when setting ``ase`` or ``values``, a physical CIF file is generated
        first, the values are updated from the physical CIF file.
    """

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all CIF files that match a given MD5 hash.
        
        :note: the hash has to be stored in a ``_md5`` attribute, otherwise
            the CIF file will not be found.
        """
        queryset = cls.query(dbattributes__key='md5', dbattributes__tval=md5)
        return list(queryset)

    @classmethod
    def get_or_create(cls,filename,use_first = False,store_cif=True):
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
            raise ValueError( "filename must be an absolute path" )
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
                    raise ValueError( "More than one copy of a CIF file "
                                      "with the same MD5 has been found in "
                                      "the DB. pks={}".format(
                                      ",".join([str(i.pk) for i in cifs])))
            else:        
                return (cifs[0], False)

    def _get_aiida_structure(self,converter='ase',store=False,**kwargs):
        """
        Creates :py:class:`aiida.orm.data.structure.StructureData`.

        :param converter: specify the converter. Default 'ase'.
        :param store: If True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :return: :py:class:`aiida.orm.data.structure.StructureData` node.
        """
        from aiida.orm.data.parameter import ParameterData
        import cif # This same module

        param = ParameterData(dict=kwargs)
        try:
            conv_f = getattr(cif,'_get_aiida_structure_{}_inline'.format(converter))
            ret_dict = conv_f(cif=self,parameters=param,store=store)
            return ret_dict['structure']
        except AttributeError:
            raise ValueError("No such converter '{}' available".format(converter))

    @property
    def ase(self):
        """
        ASE object, representing the CIF.

        :note: requires ASE module.
        """
        if self._ase is None:
            self._ase = self.get_ase()
        return self._ase

    def get_ase(self, **kwargs):
        """
        Returns ASE object, representing the CIF. This function differs
        from the property ``ase`` by the possibility to pass the keyworded
        arguments (kwargs) to ase.io.cif.read_cif().

        :note: requires ASE module.
        """
        if not kwargs and self._ase:
            return self.ase
        else:
            from ase.io.cif import read_cif
            return read_cif(self.get_file_abs_path(),**kwargs)

    def set_ase(self,aseatoms):
        cif = cif_from_ase(aseatoms)
        self.values = pycifrw_from_cif(cif,loops=ase_loops)

    @ase.setter
    def ase(self,aseatoms):
        self.set_ase(aseatoms)

    @property
    def values(self):
        """
        PyCifRW structure, representing the CIF datablocks.

        :note: requires PyCifRW module.
        """
        if self._values is None:
            import CifFile
            self._values = CifFile.ReadCif( self.get_file_abs_path() )
        return self._values

    def set_values(self,values):
        import CifFile
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(values.WriteOut())
            f.flush()
            self.set_file(f.name)

    @values.setter
    def values(self,values):
        self.set_values(values)

    def __init__(self, **kwargs):
        """
        Initialises an instance of CifData.
        """
        self._db_source_attrs = ['db_source',
                                 'db_url',
                                 'db_id',
                                 'db_version',
                                 'extras',
                                 'url',
                                 'source_md5']
        super(CifData,self).__init__(**kwargs)
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
        super(CifData,self).set_file(filename)
        md5sum = self.generate_md5()
        if self.get_attr('source_md5','') and self.get_attr('source_md5') != md5sum:
            for key in self._db_source_attrs:
                try:
                    self._del_attr(key)
                except AttributeError:
                    pass
        self._set_attr('md5', md5sum)
        self._values = None
        self._ase = None
        self._set_attr('formulae', self.get_formulae())

    @property
    def source(self):
        """
        A dictionary representing the source of a CIF.
        """
        source_dict = {}
        for k in self._db_source_attrs:
            source_dict[k] = self.get_attr(k, "")
        return source_dict

    @source.setter
    def source(self, source):
        """
        Set the file source descriptions.
        :raises ValueError: if unknown data source attribute is found in
            supplied dictionary.
        """
        unknown_keys = []
        for k in source.keys():
            if k in self._db_source_attrs:
                self._set_attr(k,source[k])
            else:
                unknown_keys.append(k)
        if unknown_keys:
            raise ValueError("Unknown data source attribute(s) " +
                             ", ".join(unknown_keys) +
                             ": only " + ", ".join(self._db_source_attrs) +
                             " are supported")

    def set_source(self, source):
        """
        Set the file source descriptions.
        """
        self.source = source

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

    def _prepare_cif(self):
        """
        Write the given CIF file to a string of format CIF.
        """
        if self._values: # if values have been changed
            self.values = self._values
        with open(self.get_file_abs_path()) as f:
            return f.read()
        
    def _validate(self):
        """
        Validate the structure.
        """
        from aiida.common.exceptions import ValidationError
        super(CifData,self)._validate()

        try:
            attr_md5 = self.get_attr('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")
        md5 = self.generate_md5()
        if attr_md5 != md5:
            raise ValidationError("Attribute 'md5' says '{}' but '{}' was "
                                  "parsed instead.".format(
                    attr_md5, md5))
