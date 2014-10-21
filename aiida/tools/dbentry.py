# -*- coding: utf-8 -*-

class DBEntry(object):
    """
    Represents the entry from the structure database (COD, ICSD, ...).
    """

    def __init__(self, url, **kwargs):
        """
        Creates an instance of DBEntry, related to the supplied URL.
        Downloads corresponding CIF file.
        """
        import urllib2
        self.url       = url
        self.source_db = None
        self.db_id     = None
        self._cif      = None
        if 'source_db' in kwargs.keys():
            self.source_db = kwargs['source_db']
        if 'db_id' in kwargs.keys():
            self.db_id = kwargs['db_id']

    @property
    def cif(self):
        if self._cif is None:
            import urllib2
            self._cif = urllib2.urlopen( self.url ).read()
        return self._cif

    def get_raw_cif(self):
        """
        Returns raw contents of a CIF file as string.
        """
        return self.cif

    def get_ase_structure(self):
        """
        Returns ASE representation of the CIF.
        """
        import ase.io.cif
        import StringIO
        return ase.io.cif.read_cif( StringIO.StringIO( self.cif ) )

    def get_cif_node(self):
        """
        Returns CIF node, that can be used in AiiDA workflow.
        """
        raise NotImplementedError()

    def get_aiida_structure(self):
        """
        Returns AiiDA-compatible structure, representing the crystal
        structure from the CIF file.
        """
        raise NotImplementedError()

    def get_parsed_cif(self):
        """
        Returns data structure, representing the CIF file. Can be created
        using **PyCIFRW** or any other open-source parser.
        """
        raise NotImplementedError()
