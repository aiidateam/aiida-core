# -*- coding: utf-8 -*-

import urllib2

class DBEntry(object):
    """
    Represents the entry from the structure database (COD, ICSD, ...).
    """

    url = ""
    source_db = "" # Identification of the source database
    db_id = ""     # Structure identifyer

    cif = "" # Contents of raw CIF file

    def __init__(self, url, **kwargs):
        self.url = url
        if 'source_db' in kwargs.keys():
            self.source_db = kwargs['source_db']
        if 'db_id' in kwargs.keys():
            self.db_id = kwargs['db_id']
        cif = urllib2.urlopen( self.url ).read()

    def get_raw_cif(self):
        """
        Returns raw contents of a CIF file as string.
        """
        return self.cif

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
