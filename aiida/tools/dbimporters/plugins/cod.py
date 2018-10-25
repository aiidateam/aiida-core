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

from aiida.tools.dbimporters.baseclasses import (DbImporter, DbSearchResults,
                                                 CifEntry)


class CodDbImporter(DbImporter):
    """
    Database importer for Crystallography Open Database.
    """

    def _int_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying integer fields.
        """
        for e in values:
            if not isinstance(e, int) and not isinstance(e, six.string_types):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return key + " IN (" + ", ".join(str(int(i)) for i in values) + ")"

    def _str_exact_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying string fields.
        """
        clause_parts = []
        for e in values:
            if not isinstance(e, int) and not isinstance(e, six.string_types):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
            if isinstance(e, int):
                e = str(e)
            clause_parts.append("'" + e + "'")
        return key + " IN (" + ", ".join(clause_parts) + ")"

    def _str_exact_or_none_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying string fields, allowing
        to use Python's "None" in addition.
        """
        if None in values:
            values_now = []
            for e in values:
                if e is not None:
                    values_now.append(e)
            if len(values_now):
                clause = self._str_exact_clause(key, alias, values_now)
                return "{} OR {} IS NULL".format(clause, key)
            else:
                return "{} IS NULL".format(key)
        else:
            return self._str_exact_clause(key, alias, values)

    def _formula_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying formula fields.
        """
        for e in values:
            if not isinstance(e, six.string_types):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return self._str_exact_clause(key, \
                                      alias, \
                                      ["- {} -".format(f) for f in values])

    def _str_fuzzy_clause(self, key, alias, values):
        """
        Returns SQL query predicate for fuzzy querying of string fields.
        """
        clause_parts = []
        for e in values:
            if not isinstance(e, int) and not isinstance(e, six.string_types):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
            if isinstance(e, int):
                e = str(e)
            clause_parts.append(key + " LIKE '%" + e + "%'")
        return " OR ".join(clause_parts)

    def _composition_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying elements in formula fields.
        """
        clause_parts = []
        for e in values:
            if not isinstance(e, six.string_types):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
            clause_parts.append("formula REGEXP ' " + e + "[0-9 ]'")
        return " AND ".join(clause_parts)

    def _double_clause(self, key, alias, values, precision):
        """
        Returns SQL query predicate for querying double-valued fields.
        """
        for e in values:
            if not isinstance(e, int) and not isinstance(e, float):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and floats are accepted")
        return " OR ".join("{} BETWEEN {} AND {}".format(key, d-precision, d+precision) for d in values)

    length_precision = 0.001
    angle_precision = 0.001
    volume_precision = 0.001
    temperature_precision = 0.001
    pressure_precision = 1

    def _length_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying lattice vector lengths.
        """
        return self._double_clause(key, alias, values, self.length_precision)

    def _angle_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying lattice angles.
        """
        return self._double_clause(key, alias, values, self.angle_precision)

    def _volume_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying unit cell volume.
        """
        return self._double_clause(key, alias, values, self.volume_precision)

    def _temperature_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying temperature.
        """
        return self._double_clause(key, alias, values, self.temperature_precision)

    def _pressure_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying pressure.
        """
        return self._double_clause(key, alias, values, self.pressure_precision)

    _keywords = {'id': ['file', _int_clause],
                 'element': ['element', _composition_clause],
                 'number_of_elements': ['nel', _int_clause],
                 'mineral_name': ['mineral', _str_fuzzy_clause],
                 'chemical_name': ['chemname', _str_fuzzy_clause],
                 'formula': ['formula', _formula_clause],
                 'volume': ['vol', _volume_clause],
                 'spacegroup': ['sg', _str_exact_clause],
                 'spacegroup_hall': ['sgHall', _str_exact_clause],
                 'a': ['a', _length_clause],
                 'b': ['b', _length_clause],
                 'c': ['c', _length_clause],
                 'alpha': ['alpha', _angle_clause],
                 'beta': ['beta', _angle_clause],
                 'gamma': ['gamma', _angle_clause],
                 'z': ['Z', _int_clause],
                 'measurement_temp': ['celltemp', _temperature_clause],
                 'diffraction_temp': ['diffrtemp', _temperature_clause],
                 'measurement_pressure':
                     ['cellpressure', _pressure_clause],
                 'diffraction_pressure':
                     ['diffrpressure', _pressure_clause],
                 'authors': ['authors', _str_fuzzy_clause],
                 'journal': ['journal', _str_fuzzy_clause],
                 'title': ['title', _str_fuzzy_clause],
                 'year': ['year', _int_clause],
                 'journal_volume': ['volume', _int_clause],
                 'journal_issue': ['issue', _str_exact_clause],
                 'first_page': ['firstpage', _str_exact_clause],
                 'last_page': ['lastpage', _str_exact_clause],
                 'doi': ['doi', _str_exact_clause],
                 'determination_method': ['method', _str_exact_or_none_clause]}

    def __init__(self, **kwargs):
        self._db = None
        self._cursor = None
        self._db_parameters = {'host': 'www.crystallography.net',
                               'user': 'cod_reader',
                               'passwd': '',
                               'db': 'cod'}
        self.setup_db(**kwargs)

    def query_sql(self, **kwargs):
        """
        Forms a SQL query for querying the COD database using
        ``keyword = value`` pairs, specified in ``kwargs``.

        :return: string containing a SQL statement.
        """
        sql_parts = ["(status IS NULL OR status != 'retracted')"]
        for key in sorted(self._keywords.keys()):
            if key in kwargs.keys():
                values = kwargs.pop(key)
                if not isinstance(values, list):
                    values = [values]
                sql_parts.append( \
                    "(" + self._keywords[key][1](self, \
                                                 self._keywords[key][0], \
                                                 key, \
                                                 values) + \
                    ")")
        if len(kwargs.keys()) > 0:
            raise NotImplementedError( \
                "search keyword(s) '" + \
                "', '".join(kwargs.keys()) + "' " + \
                "is(are) not implemented for COD")
        return "SELECT file, svnrevision FROM data WHERE " + \
               " AND ".join(sql_parts)

    def query(self, **kwargs):
        """
        Performs a query on the COD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.cod.CodSearchResults`.
        """
        query_statement = self.query_sql(**kwargs)
        self._connect_db()
        results = []
        try:
            self._cursor.execute(query_statement)
            self._db.commit()
            for row in self._cursor.fetchall():
                results.append({'id': str(row[0]),
                                'svnrevision': str(row[1])})
        finally:
            self._disconnect_db()

        return CodSearchResults(results)

    def setup_db(self, **kwargs):
        """
        Changes the database connection details.
        """
        for key in self._db_parameters.keys():
            if key in kwargs.keys():
                self._db_parameters[key] = kwargs.pop(key)
        if len(kwargs.keys()) > 0:
            raise NotImplementedError( \
                "unknown database connection parameter(s): '" + \
                "', '".join(kwargs.keys()) + \
                "', available parameters: '" + \
                "', '".join(self._db_parameters.keys()) + "'")

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.

        :return: list of strings
        """
        return self._keywords.keys()

    def _connect_db(self):
        """
        Connects to the MySQL database for performing searches.
        """
        try:
            import MySQLdb
        except ImportError:
            import pymysql as MySQLdb

        self._db = MySQLdb.connect(host=self._db_parameters['host'],
                                   user=self._db_parameters['user'],
                                   passwd=self._db_parameters['passwd'],
                                   db=self._db_parameters['db'])
        self._cursor = self._db.cursor()

    def _disconnect_db(self):
        """
        Closes connection to the MySQL database.
        """
        self._db.close()


class CodSearchResults(DbSearchResults):
    """
    Results of the search, performed on COD.
    """
    _base_url = "http://www.crystallography.net/cod/"

    def __init__(self, results):
        super(CodSearchResults, self).__init__(results)
        self._return_class = CodEntry

    def __len__(self):
        return len(self._results)

    def _get_source_dict(self, result_dict):
        """
        Returns a dictionary, which is passed as kwargs to the created
        DbEntry instance, describing the source of the entry.

        :param result_dict: dictionary, describing an entry in the results.
        """
        source_dict = {'id': result_dict['id']}
        if 'svnrevision' in result_dict and \
                        result_dict['svnrevision'] is not None:
            source_dict['version'] = result_dict['svnrevision']
        return source_dict

    def _get_url(self, result_dict):
        """
        Returns an URL of an entry CIF file.

        :param result_dict: dictionary, describing an entry in the results.
        """
        url = self._base_url + result_dict['id'] + ".cif"
        if 'svnrevision' in result_dict and \
                        result_dict['svnrevision'] is not None:
            return "{}@{}".format(url, result_dict['svnrevision'])
        else:
            return url


class CodEntry(CifEntry):
    """
    Represents an entry from COD.
    """
    _license = 'CC0'

    def __init__(self, uri, db_name='Crystallography Open Database',
                 db_uri='http://www.crystallography.net/cod', **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.cod.CodEntry`, related
        to the supplied URI.
        """
        super(CodEntry, self).__init__(db_name=db_name, db_uri=db_uri,
                                       uri=uri, **kwargs)
