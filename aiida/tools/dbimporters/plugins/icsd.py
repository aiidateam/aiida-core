# -*- coding: utf-8 -*-

import aiida.tools.dbimporters.baseclasses

class IcsdDbImporter(aiida.tools.dbimporters.baseclasses.DbImporter):
    """
    Database importer for ICSD.
    """

    def parse_icsdcode(k,code_list):
        """
        Should take list as well as single entry
        """
        if type(code_list) is list:
            retval = ' '.join(code_list)
        elif type(code_list) is int:
            retval = str(code_list)
        elif type(code_list) is str:
            retval = code_list
        return ("authors", retval)

    def parse_elements(k,el_list):
        #retval = v.split()
        retval = ' '.join(el_list)
        return ("elements", retval)

    def parse_num(k,v):
        retval = v
        return ("elementc", retval)

    def parse_mineral(k,v):
        retval = v
        return ("mineral", retval)

    def parse_formula(k,v):
        #should start with either A=, P= or T=
        #do some checks
        retval = v
        return ("formula", retval)

    def parse_spacegroup(k,v):
        #should start with either A=, P= or T=
        #do some checks
        retval = v
        return ("spaceg", retval)

    def parse_journal(k,v):
        #should start with either A=, P= or T=
        #do some checks
        retval = v
        return ("journal", retval)

    def parse_title(k,v):
        retval = v
        return ("title", retval)

    def parse_year(k,v):
        retval = v
        return ("year", retval)

    def parse_volume(k,v):
        # volume v=, density d=, molecular mass m=
        # cell dimensions a= b= c=, angles al be ga
        retval = v
        return ("volume", retval)

    def parse_system(v):
        valid_systems = {
        "cubic": "CU",
        "hexagonal": "HE",
        "monoclinic": "MO",
        "orthorhombic": "OR",
        "tetragonal": "TE",
        "trigonal": "TG",
        "triclinic": "TC"
        }

    keywords = { 'id'                : parse_icsdcode,
                 'element'           : parse_elements,
                 'number_of_elements': parse_num,
                 'mineral_name'      : parse_mineral,
                 'chemical_name'     : parse_mineral,
                 'formula'           : parse_formula,
                 'volume'            : parse_volume,
                 'spacegroup'        : parse_spacegroup,
                 'a'                 : parse_volume,
                 'b'                 : parse_volume,
                 'c'                 : parse_volume,
                 'alpha'             : parse_volume,
                 'beta'              : parse_volume,
                 'gamma'             : parse_volume,
                 'authors'           : parse_icsdcode,
                 'journal'           : parse_journal,
                 'title'             : parse_title,
                 'year'              : parse_year}

    def __init__(self, **kwargs):
        #import logging
        #aiidalogger  =  logging.getLogger('aiida')
        #self.logger  =  aiidalogger.getChild('ICSDImporter')
        self.db_parameters = { 'server':   '',
                               #'db':     'icsd',
                               'urladd': 'index.php?',
                               #'urladd': 'index.php?format=cif&action=Export&id%5B%5D={}'
                            }
        self.setup_db( **kwargs )

    def query(self, **kwargs):
        """
        Performs a query on the Icsd database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        """

        self.actual_args = {
            "action": "Search",
            "page" : "{}",
            "nb_rows" : "100", #max is 100
            "order_by" : "yearDesc",
            "authors" : "",
            "volume" : "",
            "mineral" : ""
        }

        for k, v in kwargs.iteritems():
            try:
                realname, newv = keywords[k](k,v)
                # Because different keys correspond to the same search field.
                if realname in  ["authors", "volume","mineral"]:
                    self.actual_args[realname] = self.actual_args[realname] + newv + " "

                else:
                    self.actual_args[realname] = newv
            except KeyError as e:
                raise TypeError("ICSDImporter got an unexpected keyword argument '{}'".format(e.message))

        url_values = urllib.urlencode(self.actual_args)
        query_url = self.urladd + url_values

        return IcsdSearchResults(query = query_url, server = self.server)



    def setup_db(self, **kwargs):
        """
        Changes the database connection details. At least the server has to be defined.
        """
        for key in self.db_parameters.keys():
            if key in kwargs.keys():
                self.db_parameters[key] = kwargs[key]

    def _connect_db(self):
        """
        Connects to the MySQL database for performing searches.
        """
        self.db = MySQLdb.connect( host =   self.db_parameters['host'],
                                   user =   self.db_parameters['user'],
                                   passwd = self.db_parameters['passwd'],
                                   db =     self.db_parameters['db'] )
        self.cursor = self.db.cursor()

    def _disconnect_db(self):
        """
        Closes connection to the MySQL database.
        """
        self.db.close()


class IcsdSearchResults(aiida.tools.dbimporters.baseclasses.DbSearchResults):
    """
    Results of the search, performed on Icsd.
    """

    cif_url = "index.php?format=cif&action=Export&id%5B%5D={}"
    db_name = "Icsd"

    def __init__(self, results):
        import urllib2
        from bs4 import BeautifulSoup
        import re

        self.server = server
        self.query = query
        self.number_of_results = None
        self.results = []
        self.entries = {}
        self.page = 1
        self.position = 0

        query_page()

    def next(self):
        """
        Returns next result as IcsdEntry.
        """
        if len( self.results ) > self.position:
            self.position = self.position + 1
            return self.at( self.position - 1 )
        elif number_of_results > self.position:
            self.position = self.position + 1
            self.page = self.page + 1
            query_page()
            return self.at (self.position - 1)
        else:
            raise StopIteration()

    def at(self, position):
        """
        Returns ``position``-th result as IcsdEntry.
        """
        if position < 0 | position >= number_of_results:
            raise IndexError( "index out of bounds" )
        if position not in self.entries:
            self.entries[position] = IcsdEntry( self.server + cif_url.format(self.results[position]), \
                          source_db = self.db_name, \
                          db_id = self.results[position] )
        return self.entries[position]

    def query_page(self):

        self.html = urllib2.urlopen(self.query.format(self.page)).read()

        self.soup = BeautifulSoup(self.html)

        if number_of_results is None:
            #is there a better way to get this number?
            number_of_results = int(re.findall(r'\d+', str(self.soup.find_all("i")[-1])[0]))
            print number_of_results

        for i in self.soup.find_all('input', type="checkbox"):
            #x = SearchResult(server, cif_url, i['id'])
            results.append(i['id'])


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
