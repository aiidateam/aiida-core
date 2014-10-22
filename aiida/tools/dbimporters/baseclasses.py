# -*- coding: utf-8 -*-

class DBImporter(object):
    """
    Base class for database importers.
    """

    def query(self, **kwargs):
        """
        Method to query the database. The method should be able to process the
        following keywords or throw **NotImplementedError** otherwise:

        * id -- database-specific entry identificator
        * element -- element name from periodic table of elements
        * number_of_elements -- number of different elements
        * mineral_name -- name of mineral
        * chemical_name -- chemical name of substance
        * formula -- chemical formula
        * volume -- volume of the unit cell in cubic angstroms
        * spacegroup -- symmetry space group symbol in Hermann-Mauguin notation
        * a, b, c, alpha, beta, gamma -- lattice parameters
        * authors -- authors of the publication
        * journal -- name of the journal
        * title -- title of the publication
        * year -- year of the publication
        """
        raise NotImplementedError( "not implemented in base class" )

    def setup_db(self, **kwargs):
        """
        Sets the database parameters. The method should reconnect to the
        database using updated parameters, if already connected.
        """
        raise NotImplementedError( "not implemented in base class" )

class DBSearchResults(object):
    """
    Base class for database results.
    """

    def __iter__(self):
        """
        Instances of *DBSearchResults can be used as iterators.
        """
        return self

    def fetch_all(self):
        """
        Returns all query results as an array of BaseDBEntry.
        """
        results = []
        for entry in self:
            results.append( entry )
        return results

    def next(self):
        """
        Returns the next result of the query (instance of BaseDBEntry),
        throws **StopIteration** when called after the last result.
        """
        raise NotImplementedError( "not implemented in base class" )

    def at(self, position):
        """
        Returns ``position``-th result (instance of BaseDBEntry) from the
        result array (zero-based).
        """
        raise NotImplementedError( "not implemented in base class" )

class DBEntry(object):
    """
    Represents an entry from the structure database (COD, ICSD, ...).
    """

    @property
    def cif(self):
        """
        Returns raw contents of a CIF file as string.
        """
        raise NotImplementedError( "not implemented in base class" )

    def get_raw_cif(self):
        """
        Returns raw contents of a CIF file as string.
        """
        return self.cif

    def get_ase_structure(self):
        """
        Returns ASE representation of the CIF.
        """
        raise NotImplementedError( "not implemented in base class" )

    def get_cif_node(self):
        """
        Returns CIF node, that can be used in AiiDA workflow.
        """
        raise NotImplementedError( "not implemented in base class" )

    def get_aiida_structure(self):
        """
        Returns AiiDA-compatible structure, representing the crystal
        structure from the CIF file.
        """
        raise NotImplementedError( "not implemented in base class" )

    def get_parsed_cif(self):
        """
        Returns data structure, representing the CIF file. Can be created
        using **PyCIFRW** or any other open-source parser.
        """
        raise NotImplementedError( "not implemented in base class" )
