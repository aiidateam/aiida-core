# -*- coding: utf-8 -*-

class BaseDBImporter(object):
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

class BaseDBSearchResults(object):
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
        Returns all query results as an array of DBEntry.
        """
        results = []
        for entry in self:
            results.append( entry )
        return results

    def next(self):
        """
        Returns the next result of the query (instance of DBEntry), throws
        **StopIteration** when called after the last result.
        """
        raise NotImplementedError( "not implemented in base class" )

    def at(self, position):
        """
        Returns ``position``-th result (instance of DBEntry) from the
        result array (zero-based).
        """
        raise NotImplementedError( "not implemented in base class" )
