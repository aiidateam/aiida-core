# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi, Nicolas Mounet"

from aiida.orm.calculation.inline import optional_inline

@optional_inline
def _get_cif_inline(parameters=None):
    """
    Wraps CIF file in :py:class:`aiida.orm.data.cif.CifData` instance.
    """
    from aiida.common.utils import md5_file
    from aiida.orm.data.cif import CifData
    import tempfile

    cif = parameters.get_dict().pop('cif')
    source = parameters.get_dict().pop('source',{})

    with tempfile.NamedTemporaryFile() as f:
        f.write(cif)
        f.flush()
        if 'source_md5' not in source.keys() or source['source_md5'] is None:
            source['source_md5'] = md5_file(f.name)
        return {'cif': CifData(file=f.name, source=source)}

class DbImporter(object):
    """
    Base class for database importers.
    """

    def query(self, **kwargs):
        """
        Method to query the database.

        :param id: database-specific entry identificator
        :param element: element name from periodic table of elements
        :param number_of_elements: number of different elements
        :param mineral_name: name of mineral
        :param chemical_name: chemical name of substance
        :param formula: chemical formula
        :param volume: volume of the unit cell in cubic angstroms
        :param spacegroup: symmetry space group symbol in Hermann-Mauguin
            notation
        :param spacegroup_hall: symmetry space group symbol in Hall
            notation
        :param a: length of lattice vector in angstroms
        :param b: length of lattice vector in angstroms
        :param c: length of lattice vector in angstroms
        :param alpha: angles between lattice vectors in degrees
        :param beta: angles between lattice vectors in degrees
        :param gamma: angles between lattice vectors in degrees
        :param z: number of the formula units in the unit cell
        :param measurement_temp: temperature in kelvins at which the
            unit-cell parameters were measured
        :param measurement_pressure: pressure in kPa at which the
            unit-cell parameters were measured
        :param diffraction_temp: mean temperature in kelvins at which
            the intensities were measured
        :param diffraction_pressure: mean pressure in kPa at which the
            intensities were measured
        :param authors: authors of the publication
        :param journal: name of the journal
        :param title: title of the publication
        :param year: year of the publication
        :param journal_volume: journal volume of the publication
        :param journal_issue: journal issue of the publication
        :param first_page: first page of the publication
        :param last_page: last page of the publication
        :param doi: digital object identifyer (DOI), refering to the
            publication

        :raises NotImplementedError: if search using given keyword is not
            implemented.
        """
        raise NotImplementedError("not implemented in base class")

    def setup_db(self, **kwargs):
        """
        Sets the database parameters. The method should reconnect to the
        database using updated parameters, if already connected.
        """
        raise NotImplementedError("not implemented in base class")

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.

        :return: list of strings
        """
        raise NotImplementedError("not implemented in base class")

class DbSearchResults(object):
    """
    Base class for database results.

    All classes, inheriting this one and overriding ``at()``, are able to
    benefit from having functions ``__iter__``, ``__len__`` and
    ``__getitem__``.
    """

    class DbSearchResultsIterator(object):
        """
        Iterator for search results
        """

        def __init__(self,results,increment=1):
            self._results = results
            self._position = 0
            self._increment = increment

        def next(self):
            pos = self._position
            if pos >= 0 and pos < len(self._results):
                self._position = self._position + self._increment
                return self._results[pos]
            else:
                raise StopIteration()

    def __iter__(self):
        """
        Instances of
        :py:class:`aiida.tools.dbimporters.baseclasses.DbSearchResults` can
        be used as iterators.
        """
        return self.DbSearchResultsIterator(self)

    def __len__(self):
        return len(self.results)

    def __getitem__(self,key):
        return self.at(key)

    def fetch_all(self):
        """
        Returns all query results as an array of
        :py:class:`aiida.tools.dbimporters.baseclasses.DbEntry`.
        """
        results = []
        for entry in self:
            results.append(entry)
        return results

    def next(self):
        """
        Returns the next result of the query (instance of
        :py:class:`aiida.tools.dbimporters.baseclasses.DbEntry`).

        :raise StopIteration: when the end of result array is reached.
        """
        raise NotImplementedError("not implemented in base class")

    def at(self, position):
        """
        Returns ``position``-th result as
        :py:class:`aiida.tools.dbimporters.baseclasses.DbEntry`.

        :param position: zero-based index of a result.

        :raise IndexError: if ``position`` is out of bounds.
        """
        raise NotImplementedError("not implemented in base class")

class DbEntry(object):
    """
    Represents an entry from the structure database (COD, ICSD, ...).
    """

    def __init__(self,db_source=None,db_url=None,db_id=None,db_version=None,
                 extras={},url=None):
        """
        Sets the basic parameters for the database entry:

        :param db_source: name of the source database
        :param db_url: URL of the source database
        :param db_id: structure identifyer in the database
        :param db_version: version of the database
        :param extras: a dictionary with some extra parameters
            (e.g. database ID number)
        :param url: URL of the structure (should be permanent)
        """
        self.source = {
            'db_source' : db_source,
            'db_url'    : db_url,
            'db_id'     : db_id,
            'db_version': db_version,
            'extras'    : extras,
            'url'       : url,
            'source_md5': None,
        }
        self._cif = None

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,
                               ",".join(["{}={}".format(k,'"{}"'.format(v)
                                         if issubclass(v.__class__,basestring)
                                         else v)
                                        for k,v in self.source.iteritems()]))

    @property
    def cif(self):
        """
        Returns raw contents of a CIF file as string.
        """
        if self._cif is None:
            import urllib2
            self._cif = urllib2.urlopen( self.source['url'] ).read()
        return self._cif

    def get_raw_cif(self):
        """
        Returns raw contents of a CIF file as string.

        :return: contents of a file as string
        """
        return self.cif

    def get_ase_structure(self):
        """
        Returns ASE representation of the CIF.

        .. note:: To be removed, as it is duplicated in
            :py:class:`aiida.orm.data.cif.CifData`.
        """
        import ase.io.cif
        import StringIO
        return ase.io.cif.read_cif( StringIO.StringIO( self.cif ) )

    def get_cif_node(self,store=False):
        """
        Creates a CIF node, that can be used in AiiDA workflow.

        :return: :py:class:`aiida.orm.data.cif.CifData` object
        """
        from aiida.orm.data.parameter import ParameterData
        import baseclasses # This same module
        pd = ParameterData(dict={'cif': self.cif, 'source': self.source})
        ret_dict = _get_cif_inline(parameters=pd,store=store)
        return ret_dict['cif']

    def get_aiida_structure(self):
        """
        Returns AiiDA-compatible structure, representing the crystal
        structure from the CIF file.
        """
        raise NotImplementedError("not implemented in base class")
    def get_parsed_cif(self):
        """
        Returns data structure, representing the CIF file. Can be created
        using PyCIFRW or any other open-source parser.

        :return: list of lists
        """
        raise NotImplementedError("not implemented in base class")
