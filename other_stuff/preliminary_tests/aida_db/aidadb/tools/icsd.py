#!/usr/bin/python
import requests, json
import unicodedata
from .. import nodes
import logging

apiUrl="http://theospc12.epfl.ch/icsd/api/"
debug = False

def query(params_in):

  """Query the ICSD APIs (this is a special extension of the ICSD).

  Keyword arguments:
  params_in -- The query dictionary. Each key is a ICSD query parameter and each value
  is the argument. Right now the possibile parameters are:
  
  authors, years, vol, pages, remarks, title, elements, elementc, mineral, journal, 
  formula, laue, center, system, spaceg, wyckoff, volume, min_dist, dist_select, 
  dist_range, ncoord, page, nb_rows, order_by, nb_results
  
  Returns:
  A json strcuture with the ID and title of each structure resulting from the query.
  """

  logging.info('Running ICDS API query...')
  r = requests.get(apiUrl+"search.php", params=params_in)
  if r.status_code == requests.codes.ok:
    logging.info('Respose query received')
    #return json.loads(r.text)
    return json.loads(unicodedata.normalize('NFKD', r.text).encode('ascii','ignore'))

  else:
    logging.info('Error searching ICSD [code '+r.status_code+']')
    return None

def get(cid):

  """Get a specific CIF file from the ICSD API database.

  Keyword arguments:
  cid -- The ICSD ID of the structure
  
  Returns:
  A CIF text for the structure.
  """

  logging.info('Downloading ICDS API data...')
  r = requests.get(apiUrl+"get.php", params={"c":cid})
  if r.status_code == requests.codes.ok:
    logging.info('Respose query received')
    return json.loads(unicodedata.normalize('NFKD', r.text).encode('ascii','ignore'))
  else:
    logging.info('Error downloading '+str(cid)+' [code '+r.status_code+']')
    if debug: print ""
    return None

def download(cid, fname=None):

  """Download and stores ina  file a specific CIF file from the ICSD API database.

  Keyword arguments:
  cid -- The ICSD ID of the structure
  
  Returns:
  The filename of the CIF structure stored.
  """

  d = get(cid)
  t = d['cif']
  
  ccid = cid
  for l in t.split("\n"):
    if l.strip().startswith("data_") and l.strip().endswith("-ICSD"):
      ccid = l.strip().split("_")[1].split("-")[0]
      break

  if (fname==None):
    fname = "icsd_"+ccid+".cif" 
  f = open(fname, "w")
  f.write(t)
  f.close()

  return fname


def asDataNode(cid):
  
  d = get(cid)
  data = {'cid':cid,'cif':d['cif']};  
  return nodes.Data('icsd', d['title'], data)

