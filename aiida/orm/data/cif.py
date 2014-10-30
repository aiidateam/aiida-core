# -*- coding: utf-8 -*-
from aiida.orm.data.singlefile import SinglefileData

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

def has_pycifrw():
    """
    :return: True if the PyCifRW module can be imported, False otherwise.
    """
    try:
        import CifFile
    except ImportError:
        return False
    return True

class CifData(SinglefileData): 
    """
    Wrapper for Crystallographic Interchange File (CIF)
    """

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all CIF files that match a given MD5 hash.
        
        Note that the hash has to be stored in a _md5 attribute, otherwise
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

    def _get_aiida_structure(self, converter='ase'):
        try:
            getattr(self, '_get_aiida_structure_{}'.format(converter))
        except AttributeError:
            raise ValueError("No such converter '{}' available".format(converter))

    def _get_aiida_structure_ase(self):
        from aiida.orm.data.structure import StructureData
        import ase.io.cif
        return StructureData(ase=ase.io.cif.read_cif(self.get_file_abs_path()))

    @property
    def values(self):
        """
        Returns parsed CIF file.
        """
        if self._values is None:
            import CifFile
            self._values = CifFile.ReadCif( self.get_file_abs_path() )
        return self._values

    def __init__(self, **kwargs):
        """
        Initialises an instance of CifData.
        """
        super(CifData,self).__init__(**kwargs)
        self._values = None

    def store(self):
        """
        Store the node.
        """
        self._set_attr('md5', self.generate_md5())
        return super(CifData, self).store()

    def set_file(self, filename):
        """
        Set the file.
        """
        super(CifData,self).set_file(filename)
        self._set_attr('md5', self.generate_md5())
        self._values = None

    def generate_md5(self):
        """
        Generate MD5 hash of the file's contents on-the-fly.
        """
        import aiida.common.utils
        abspath = self.get_file_abs_path()
        if not abspath:
            raise ValidationError("No valid CIF was passed!")

        return aiida.common.utils.md5_file(abspath)
        
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
