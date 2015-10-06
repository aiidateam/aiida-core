# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"


class AbstractQueryTool(object):
    """
    Class to make easy queries without extensive knowledge of SQL, Django and/or
    the internal storage mechanism of AiiDA.

    .. note:: This feature is under constant development, so the name of the
      methods may change in future versions to allow for increased querying
      capabilities.

    .. todo:: missing
      features:

      * add __in filter
      * allow __in filter to accept other querytool objects to perform a single
        query
      * implement searches through the TC table
      * document the methods
      * allow to get attributes of queried data via a single query with suitable
        methods
      * add checks to verify whether filters as <=, ==, etc are valid for the
        specified data type (e.g., __gt only with numbers and dates, ...)
      * probably many other things...
    """
    # TODO SP: implement it completly.
    raise NotImplementedError
