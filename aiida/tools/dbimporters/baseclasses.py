# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six


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

    def __init__(self, results):
        self._results = results
        self._entries = {}

    class DbSearchResultsIterator(object):
        """
        Iterator for search results
        """

        def __init__(self, results, increment=1):
            self._results = results
            self._position = 0
            self._increment = increment

        def __next__(self):
            pos = self._position
            if pos >= 0 and pos < len(self._results):
                self._position = self._position + self._increment
                return self._results[pos]
            else:
                raise StopIteration()

        def next(self):
            """
            The iterator method expected by python 2.x,
            implemented as python 3.x style method.
            """
            return self.__next__()

    def __iter__(self):
        """
        Instances of
        :py:class:`aiida.tools.dbimporters.baseclasses.DbSearchResults` can
        be used as iterators.
        """
        return self.DbSearchResultsIterator(self)

    def __len__(self):
        return len(self._results)

    def __getitem__(self, key):
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
        if position < 0 | position >= len(self._results):
            raise IndexError("index out of bounds")
        if position not in self._entries:
            source_dict = self._get_source_dict(self._results[position])
            url = self._get_url(self._results[position])
            self._entries[position] = self._return_class(url, **source_dict)
        return self._entries[position]

    def _get_source_dict(self, result_dict):
        """
        Returns a dictionary, which is passed as kwargs to the created
        DbEntry instance, describing the source of the entry.

        :param result_dict: dictionary, describing an entry in the results.
        """
        raise NotImplementedError("not implemented in base class")

    def _get_url(self, result_dict):
        """
        Returns an URL of an entry CIF file.

        :param result_dict: dictionary, describing an entry in the results.
        """
        raise NotImplementedError("not implemented in base class")


class DbEntry(object):
    """
    Represents an entry from external database.
    """
    _license = None

    def __init__(self, db_name=None, db_uri=None, id=None,
                 version=None, extras={}, uri=None):
        """
        Sets the basic parameters for the database entry:

        :param db_name: name of the source database
        :param db_uri: URI of the source database
        :param id: structure identifyer in the database
        :param version: version of the database
        :param extras: a dictionary with some extra parameters
            (e.g. database ID number)
        :param uri: URI of the structure (should be permanent)
        """
        self.source = {
            'db_name': db_name,
            'db_uri': db_uri,
            'id': id,
            'version': version,
            'extras': extras,
            'uri': uri,
            'source_md5': None,
            'license': self._license,
        }
        self._contents = None

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,
                               ",".join(["{}={}".format(k, '"{}"'.format(self.source[k])
                               if issubclass(self.source[k].__class__, six.string_types)
                               else self.source[k])
                                         for k in sorted(self.source.keys())]))

    @property
    def contents(self):
        """
        Returns raw contents of a file as string.
        """
        if self._contents is None:
            from six.moves import urllib
            from hashlib import md5

            self._contents = urllib.request.urlopen(self.source['uri']).read().decode("utf-8")
            self.source['source_md5'] = md5(self._contents.encode("utf-8")).hexdigest()
        return self._contents

    @contents.setter
    def contents(self, contents):
        """
        Sets raw contents of a file as string.
        """
        from hashlib import md5
        self._contents = contents
        self.source['source_md5'] = md5(self._contents.encode("utf-8")).hexdigest()


class CifEntry(DbEntry):
    """
    Represents an entry from the structure database (COD, ICSD, ...).
    """

    @property
    def cif(self):
        """
        Returns raw contents of a CIF file as string.
        """
        return self.contents

    @cif.setter
    def cif(self, cif):
        """
        Sets raw contents of a CIF file as string.
        """
        self.contents = cif

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
            :py:class:`aiida.orm.nodes.data.cif.CifData`.
        """
        from six.moves import cStringIO as StringIO
        from aiida.orm import CifData
        return CifData.read_cif(StringIO(self.cif))

    def get_cif_node(self, store=False, parse_policy='lazy'):
        """

        Creates a CIF node, that can be used in AiiDA workflow.

        :return: :py:class:`aiida.orm.nodes.data.cif.CifData` object
        """
        from aiida.orm.nodes.data.cif import CifData
        import tempfile

        cifnode = None

        with tempfile.NamedTemporaryFile(mode='w+') as f:
            f.write(self.cif)
            f.flush()
            cifnode = CifData(file=f.name, source=self.source, parse_policy=parse_policy)

        # Maintaining backwards-compatibility. Parameter 'store' should
        # be removed in the future, as the new node can be stored later.
        if store:
            cifnode.store()

        return cifnode

    def get_aiida_structure(self, converter="pymatgen", store=False, **kwargs):
        """
        :return: AiiDA structure corresponding to the CIF file.
        """
        cif = self.get_cif_node(store=store, parse_policy='lazy')
        return cif.get_structure(converter=converter, store=store, **kwargs)

    def get_parsed_cif(self):
        """
        Returns data structure, representing the CIF file. Can be created
        using PyCIFRW or any other open-source parser.

        :return: list of lists
        """
        raise NotImplementedError("not implemented in base class")


class UpfEntry(DbEntry):
    """
    Represents an entry from the pseudopotential database.
    """

    def get_upf_node(self, store=False):
        """
        Creates an UPF node, that can be used in AiiDA workflow.

        :return: :py:class:`aiida.orm.nodes.data.upf.UpfData` object
        """
        from aiida.orm import UpfData
        import tempfile

        upfnode = None

        # Prefixing with an ID in order to start file name with the name
        # of the described element.
        with tempfile.NamedTemporaryFile(mode='w+', prefix=self.source['id']) as f:
            f.write(self.contents)
            f.flush()
            upfnode = UpfData(file=f.name, source=self.source)

        # Maintaining backwards-compatibility. Parameter 'store' should
        # be removed in the future, as the new node can be stored later.
        if store:
            upfnode.store()

        return upfnode
