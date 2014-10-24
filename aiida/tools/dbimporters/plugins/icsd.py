# -*- coding: utf-8 -*-

import aiida.tools.dbimporters.baseclasses

class IcsdDbImporter(aiida.tools.dbimporters.baseclasses.DbImporter):
    """
    Database importer for ICSD.
    """
    # Put similar functions together into one

    def parse_all(k,v):
        """
        Takes numbers, strings, list and returns a string.
        """
        if type(v) is list:
            retval = ' '.join(v)
        elif type(v) is int:
            retval = str(v)
        elif type(v) is str:
            retval = v
        return retval

    def parse_number(k,v):
        """
        int to string
        """
        if type(v) is int:
            retval = str(v)
        elif type (v) is str:
            retval = v
        return retval

    def parse_mineral(k,v):
        if k == "mineral_name":
            retval = "M="+ v
        elif k == "chemical_name":
            retval = "C=" + v
        return retval

    def parse_volume(k,v):
        if k == "volume":
            return "v=" + v
        elif k == "a":
            return "a=" + v
        elif k == "b":
            return "b=" + v
        elif k == "c":
            return "c=" + v
        elif k == "alpha":
            return "al=" + v
        elif k == "beta":
            return "be=" + v
        elif k == "gamma":
            return "ga=" + v


    def parse_system(k,v):
        valid_systems = {
        "cubic": "CU",
        "hexagonal": "HE",
        "monoclinic": "MO",
        "orthorhombic": "OR",
        "tetragonal": "TE",
        "trigonal": "TG",
        "triclinic": "TC"
        }
        return valid_systems[v]

    keywords = { "id"                : ("authors", parse_all),
                 "authors"           : ("authors", parse_all),
                 "element"           : ("elements", parse_all),
                 "number_of_elements": ("elementc", parse_all),
                 "mineral_name"      : ("mineral", parse_mineral),
                 "chemical_name"     : ("mineral", parse_mineral),
                 "formula"           : ("formula", parse_all),
                 "volume"            : ("volume", parse_volume),
                 "a"                 : ("volume", parse_volume),
                 "b"                 : ("volume", parse_volume),
                 "c"                 : ("volume", parse_volume),
                 "alpha"             : ("volume", parse_volume),
                 "beta"              : ("volume", parse_volume),
                 "gamma"             : ("volume", parse_volume),
                 "spacegroup"        : ("spaceg", parse_all),
                 "journal"           : ("journal", parse_all),
                 "title"             : ("title", parse_all),
                 "year"              : ("year", parse_all),
                 #"crystal_system"    : ("system", parse_system),
                 }

    def __init__(self, **kwargs):
        #import logging
        #aiidalogger  =  logging.getLogger("aiida")
        #self.logger  =  aiidalogger.getChild("ICSDImporter")
        self.db_parameters = { "server":   "",
                               #"db":     "icsd",
                               "urladd": "index.php?",
                               #'urladd': 'index.php?format=cif&action=Export&id%5B%5D={}'
                            }
        self.setup_db( **kwargs )

    def query(self, **kwargs):
        """
        Performs a query on the Icsd database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        """
        import urllib

        self.actual_args = {
            "action": "Search",
            "nb_rows" : "100", #max is 100
            "order_by" : "yearDesc",
            "authors" : "",
            "volume" : "",
            "mineral" : ""
        }

        for k, v in kwargs.iteritems():
            try:
                realname = self.keywords[k][0]
                newv = self.keywords[k][1](k,v)
                # Because different keys correspond to the same search field.
                if realname in  ["authors","volume","mineral"]:
                    self.actual_args[realname] = self.actual_args[realname] + newv + " "
                else:
                    self.actual_args[realname] = newv
            except KeyError as e:
                raise TypeError("ICSDImporter got an unexpected keyword argument '{}'".format(e.message))

        url_values = urllib.urlencode(self.actual_args)
        query_url = self.db_parameters["urladd"] + url_values

        return IcsdSearchResults(query = query_url, server = self.db_parameters["server"])



    def setup_db(self, **kwargs):
        """
        Changes the database connection details. At least the server has to be defined.
        """
        for key in self.db_parameters.keys():
            if key in kwargs.keys():
                self.db_parameters[key] = kwargs[key]


class IcsdSearchResults(aiida.tools.dbimporters.baseclasses.DbSearchResults):
    """
    Results of the search, performed on Icsd.
    """

    cif_url = "index.php?format=cif&action=Export&id%5B%5D={}"
    db_name = "Icsd"

    def __init__(self, query, server):


        self.server = server
        self.query = query
        self.number_of_results = None
        self.results = []
        self.entries = {}
        self.page = 1
        self.position = 0

        self.query_page()

    def next(self):
        """
        Returns next result as IcsdEntry.
        """
        if len( self.results ) > self.position:
            self.position = self.position + 1
            return self.at( self.position - 1 )
        elif self.number_of_results > self.position:
            self.position = self.position + 1
            self.page = self.page + 1
            self.query_page()
            return self.at (self.position - 1)
        else:
            raise StopIteration()

    def at(self, position):
        """
        Returns ``position``-th result as IcsdEntry.
        """
        if position < 0 | position >= self.number_of_results:
            raise IndexError( "index out of bounds" )
        if position not in self.entries:
            self.entries[position] = IcsdEntry( self.server + self.cif_url.format(self.results[position]), \
                          source_db = self.db_name, \
                          db_id = self.results[position] )
        return self.entries[position]

    def query_page(self):
        import urllib2
        from bs4 import BeautifulSoup
        import re

        self.html = urllib2.urlopen(self.server + self.query.format(str(self.page))).read()

        self.soup = BeautifulSoup(self.html)

        if self.number_of_results is None:
            #is there a better way to get this number?
            number_of_results = int(re.findall(r'\d+', str(self.soup.find_all("i")[-1]))[0])

        for i in self.soup.find_all('input', type="checkbox"):
            #x = SearchResult(server, cif_url, i['id'])
            self.results.append(i['id'])


class IcsdEntry(aiida.tools.dbimporters.baseclasses.DbEntry):
    """
    Represents an entry from Icsd.
    """

    def __init__(self, url, **kwargs):
        """
        Creates an instance of IcsdEntry, related to the supplied URL.
        """
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

    def get_corrected_cif(self):
        """
        Adds quotes to the lines in the author loop if missing.
        :note: ase raises an AssertionError if the quotes in the author loop are missing.
        """
        return correct_cif(self.cif())

    def get_ase_structure(self):
        """
        Returns ASE representation of the CIF.
        """
        import ase.io.cif
        import StringIO
        return ase.io.cif.read_cif( StringIO.StringIO( self.get_corrected_cif() ) )



def correct_cif(cif):
    """
    This function corrects the format of the cif files

    :note: the ase.read.io only works if the author names are quoted, if not an AssertionError is raised.

    :param cif: A string containing the content of the CIF file.
    """
    #Do more checks to be sure it's working in everycase -> no _publ_author_name, several lines, correct input
    lines = cif.split('\n')

    try:
        author_index = lines.index('_publ_author_name')
    except ValueError:
        pass
    else:
        inc = 1
        while True:
            words = lines[author_index+inc].split()
            #in case loop is finished -> return cif lines.
            #use regular expressions ?
            if len(words) == 0 or words[0] == "loop_" or words[0][0] == '_':
                return '\n'.join(lines)
            elif (words[0][0] == "'" and words[-1][-1] == "'") or (words[0][0] == '"' and words[-1][-1] == '"'):
                # if quotes are already there, check next line
                inc = inc + 1
            else:
                lines[author_index+inc] = "'" + lines[author_index+inc] + "'"
                inc = inc + 1

