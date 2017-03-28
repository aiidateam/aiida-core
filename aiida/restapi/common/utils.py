# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from datetime import datetime, timedelta

from flask import jsonify
from flask.json import JSONEncoder

from aiida.common.exceptions import InputValidationError, ValidationError
from aiida.restapi.common.exceptions import RestValidationError, \
    RestInputValidationError

# Important to match querybuilder keys
pk_dbsynonym = 'id'


########################## Classes #####################
class CustomJSONEncoder(JSONEncoder):
    """
    Custom json encoder for serialization.
    This has to be provided to the Flask app in order to replace the default
    encoder.
    """

    def default(self, obj):

        from aiida.restapi.common.config import SERIALIZER_CONFIG

        # Treat the datetime objects
        if isinstance(obj, datetime):
            if 'datetime_format' in SERIALIZER_CONFIG.keys() and \
                            SERIALIZER_CONFIG[
                                'datetime_format'] is not 'default':
                if SERIALIZER_CONFIG['datetime_format'] == 'asinput':
                    if obj.utcoffset() is not None:
                        obj = obj - obj.utcoffset()
                        return '-'.join([str(obj.year), str(obj.month).zfill(2),
                                         str(obj.day).zfill(2)]) + 'T' + \
                               ':'.join([str(
                                   obj.hour).zfill(2), str(obj.minute).zfill(2),
                                         str(obj.second).zfill(2)])

        # If not returned yet, do it in the default way
        return JSONEncoder.default(self, obj)


class datetime_precision():
    """
    A simple class which stores a datetime object with its precision. No
    internal check is done (cause itis not possible).

    precision:  1 (only full date)
                2 (date plus hour)
                3 (date + hour + minute)
                4 (dare + hour + minute +second)
    """

    def __init__(self, dt, precision):

        if not isinstance(dt, datetime):
            raise TypeError("dt argument has to be a datetime object")

        if type(precision) is not int:
            raise TypeError("precision argument has to be an integer")

        self.dt = dt
        self.precision = precision


class Utils(object):
    """
    A class that gathers all the utility functions for parsing URI,
    validating request, pass it to the translator, and building HTTP response

    An istance of Utils has to be included in the api class so that the
    configuration parameters used to build the api are automatically
    accessible by the methods of Utils without the need to import them from
    the config.py file.

    """

    # Conversion map from the query_string operators to the query_builder
    #  operators
    op_conv_map = {
        '=': '==',
        '!=': '!==',
        '=in=': 'in',
        '=notin=': '!in',
        '>': '>',
        '<': '<',
        '>=': '>=',
        '<=': '<=',
        '=like=': 'like',
        '=ilike=': 'ilike'
    }

    def __init__(self, **kwargs):
        """
        Sets internally the configuration parameters
        """

        self.PREFIX = kwargs['PREFIX']
        self.PERPAGE_DEFAULT = kwargs['PERPAGE_DEFAULT']
        self.LIMIT_DEFAULT = kwargs['LIMIT_DEFAULT']

    def strip_prefix(self, path):
        """
        Removes the PREFIX from an URL path. PREFIX must be defined in the
        config.py file.
        Ex. PREFIX = "/api/v2"
            path = "/api/v2/calculations/page/2"
            strip_prefix(path) ==> "/calculations/page/2"

        :param path: the URL path string
        :return: the same URL without the prefix
        """

        if path.startswith(self.PREFIX):
            return path[len(self.PREFIX):]
        else:
            raise ValidationError(
                'path has to start with {}'.format(self.PREFIX))

    def split_path(self, path):
        """
        :param path: entire path contained in flask request
        :return: list of each element separated by '/'
        """
        # type: (string) -> (list_of_strings).
        return filter(None, path.split('/'))

    def parse_path(self, path_string):
        """
        Takes the path and parse it checking its validity. Does not parse "io",
        "content" fields. I do not check the validity of the path, since I
        assume
        that this is done by the Flask routing methods.
        It assunme

        :param path_string: the path string
        :return:resource_type (string)
                page (integer)
                pk (integer)
                result_type (string))
        """

        ## Initialization
        page = None
        pk = None
        query_type = "default"
        path = self.split_path(self.strip_prefix(path_string))

        ## Pop out iteratively the "words" of the path until it is an empty
        # list.
        ##  This way it should be easier to plug in more endpoint logic
        # Resource type
        resource_type = path.pop(0)
        if not path:
            return (resource_type, page, pk, query_type)
        # Node_pk
        try:
            pk = int(path[0])
            foo = path.pop(0)
        except ValueError:
            pass
        if not path:
            return (resource_type, page, pk, query_type)
        # Result type (input, output, attributes, extras, schema)
        if path[0] == 'schema':
            query_type = path.pop(0)
            if path:
                raise RestInputValidationError(
                    "url requesting schema resources do not "
                    "admit further fields")
            else:
                return (resource_type, page, pk, query_type)
        elif path[0] == 'statistics':
            query_type = path.pop(0)
            if path:
                raise RestInputValidationError(
                    "url requesting statistics resources do not "
                    "admit further fields")
            else:
                return (resource_type, page, pk, query_type)
        elif path[0] == "io" or path[0] == "content":
            foo = path.pop(0)
            query_type = path.pop(0)
            if not path:
                return (resource_type, page, pk, query_type)
        # Page (this has to be in any case the last field)
        if path[0] == "page":
            do_paginate = True
            foo = path.pop(0)
            if not path:
                page = 1
                return (resource_type, page, pk, query_type)
            else:
                page = int(path.pop(0))
                return (resource_type, page, pk, query_type)

    def validate_request(self, limit=None, offset=None, perpage=None, page=None,
                         query_type=None, is_querystring_defined=False):
        """
        Performs various checks on the consistency of the request.
        Add here all the checks that you want to do, except validity of the page
        number that is done in paginate().
        Future additional checks must be added here
        """

        # TODO Consider using **kwargs so to make easier to add more validations
        # 1. perpage incompatible with offset and limits
        if perpage is not None and (limit is not None or offset is not None):
            raise RestValidationError("perpage key is incompatible with "
                                      "limit and offset")
        # 2. /page/<int: page> in path is incompatible with limit and offset
        if page is not None and (limit is not None or offset is not None):
            raise RestValidationError("requesting a specific page is "
                                      "incompatible "
                                      "with limit and offset")
        # 3. perpage requires that the path contains a page request
        if perpage is not None and page is None:
            raise RestValidationError("perpage key requires that a page is "
                                      "requested (i.e. the path must contain "
                                      "/page/)")
        # 4. if resource_type=='schema'
        if query_type == 'schema' and is_querystring_defined:
            raise RestInputValidationError("schema requests do not allow "
                                           "specifying a query string")

    def paginate(self, page, perpage, total_count):
        """
        Calculates limit and offset for the reults of a query,
        given the page and the number of restuls per page.
        Moreover, calculates the last available page and raises an exception
        if the
        required page exceeds that limit.
        If number of rows==0, only page 1 exists
        :param page: integer number of the page that has to be viewed
        :param perpage: integer defining how many results a page contains
        :param total_count: the total number of rows retrieved by the query
        :return: integers: limit, offset, rel_pages
        """
        from math import ceil

        ## Type checks
        # Mandatory params
        try:
            page = int(page)
        except ValueError:
            raise InputValidationError("page number must be an integer")
        try:
            total_count = int(total_count)
        except ValueError:
            raise InputValidationError("total_count must be an integer")
        # Non-mandatory params
        if perpage is not None:
            try:
                perpage = int(perpage)
            except ValueError:
                raise InputValidationError("perpage must be an integer")
        else:
            perpage = self.PERPAGE_DEFAULT

        ## First_page is anyway 1
        first_page = 1

        ## Calculate last page
        if total_count == 0:
            last_page = 1
        else:
            last_page = int(ceil(float(total_count) / float(perpage)))

        ## Check validity of required page and calculate limit, offset,
        # previous,
        #  and next page
        if page > last_page or page < 1:
            raise RestInputValidationError("Non existent page requested. The "
                                           "page range is [{} : {}]".format(
                first_page, last_page))
        else:
            limit = perpage
            offset = (page - 1) * perpage
            if page > 1:
                prev_page = page - 1
            else:
                prev_page = None
            if page < last_page:
                next_page = page + 1
            else:
                next_page = None

        rel_pages = dict(prev=prev_page,
                         next=next_page,
                         first=first_page,
                         last=last_page)

        return (limit, offset, rel_pages)

    def build_headers(self, rel_pages=None, url=None, total_count=None):
        """
        Construct the header dictionary for an HTTP response. It includes
        related
         pages, total count of results (before pagination).
        :param rel_pages: a dictionary defining related pages (first, prev,
        next,
        last)
        :param url: (string) the full url, i.e. the url that the client uses to
        get Rest resources
        :return:
        """

        ## Type validation
        # mandatory parameters
        try:
            total_count = int(total_count)
        except ValueError:
            raise InputValidationError("total_count must be a long integer")

        # non mandatory parameters
        if rel_pages is not None and not isinstance(rel_pages, dict):
            raise InputValidationError("rel_pages must be a dictionary")

        if url is not None:
            try:
                url = str(url)
            except ValueError:
                raise InputValidationError("url must be a string")

        ## Input consistency
        # rel_pages cannot be defined without url
        if rel_pages is not None and url is None:
            raise InputValidationError("'rel_pages' parameter requires 'url' "
                                       "parameter to be defined")

        headers = {}

        ## Setting mandatory headers
        # set X-Total-Count
        headers['X-Total-Count'] = total_count
        expose_header = ["X-Total-Count"]

        ## Two auxiliary functions
        def split_url(url):
            if '?' in url:
                [path, query_string] = url.split('?')
                question_mark = '?'
            else:
                path = url
                query_string = ""
                question_mark = ""
            return (path, query_string, question_mark)

        def make_rel_url(rel, page):
            new_path_elems = path_elems + ['page', str(page)]
            return '<' + '/'.join(new_path_elems) + \
                   question_mark + query_string + ">; rel={}, ".format(rel)

        ## Setting non-mandatory parameters
        # set links to related pages
        if rel_pages is not None:
            (path, query_string, question_mark) = split_url(url)
            path_elems = self.split_path(path)

            if path_elems.pop(-1) == 'page' or path_elems.pop(-1) == 'page':
                links = []
                for (rel, page) in rel_pages.iteritems():
                    if page is not None:
                        links.append(make_rel_url(rel, page))
                headers['Link'] = ''.join(links)
                expose_header.append("Link")
            else:
                pass

        # to expose header access in cross-domain requests
        headers['Access-Control-Expose-Headers'] = ','.join(expose_header)

        return headers

    def build_response(self, status=200, headers=None, data=None):
        """

        :param status: status of the response, e.g. 200=OK, 400=bad request
        :param headers: dictionary for additional header k,v pairs,
        e.g. X-total-count=<number of rows resulting from query>
        :param data: a dictionary with the data returned by the Resource
        :return: a Flask response object
        """

        ## Type checks
        # mandatory parameters
        if not isinstance(data, dict):
            raise InputValidationError("data must be a dictionary")

        # non-mandatory parameters
        if status is not None:
            try:
                status = int(status)
            except ValueError:
                raise InputValidationError("status must be an integer")

        if headers is not None and not isinstance(headers, dict):
            raise InputValidationError("header must be a dictionary")

        # Build response
        response = jsonify(data)
        response.status_code = status

        if headers is not None:
            for k, v in headers.iteritems():
                response.headers[k] = v

        return response

    def build_datetime_filter(self, dt):
        """
        This function constructs a filter for a datetime object to be in a
        certain datetime interval according to the precision.

        The interval is [reference_datetime, reference_datetime + Dt],
        where Dt is a function fo the required precision.

        This function should be used to replace a datetime filter based on
        the equality operator that is inehrently "picky" because it implies
        matching two datetime objects down to the microsecond or something,
        by a "tolerant" operator which checks whether the datetime is in an
        interval.

        :return: a suitable entry of the filter dictionary
        """

        if not isinstance(dt, datetime_precision):
            TypeError("dt argument has to be a datetime_precision object")

        reference_datetime = dt.dt
        precision = dt.precision

        ## Define interval according to the precision
        if precision == 1:
            Dt = timedelta(days=1)
        elif precision == 2:
            Dt = timedelta(hours=1)
        elif precision == 3:
            Dt = timedelta(minutes=1)
        elif precision == 4:
            Dt = timedelta(seconds=1)
        else:
            raise RestValidationError("The datetime resolution is not valid.")

        filter = {
            'and': [{'>=': reference_datetime}, {'<': reference_datetime + Dt}]
        }

        return filter

    def build_translator_parameters(self, field_list):
        """
        Takes a list of elements resulting from the parsing the query_string and
        elaborates them in order to provide translator-compliant instructions

        :param field_list: a (nested) list of elements resulting from parsing
        the
        query_string
        :return: the filters in the
        """

        ## Create void variables
        filters = {}
        orderby = []
        limit = None
        offset = None
        perpage = None
        alist = None
        nalist = None
        elist = None
        nelist = None

        ## Count how many time a key has been used for the filters and check if
        # reserved keyword
        # have been used twice,
        field_counts = {}
        for field in field_list:
            field_key = field[0]
            if field_key not in field_counts.keys():
                field_counts[field_key] = 1
                # Store the information whether membership operator is used
                # is_membership = (field[1] is '=in=')
            else:
                # Check if the key of a filter using membership operator is used
                # in multiple filters
                # if is_membership is True or field[1] is '=in=':
                # raise RestInputValidationError("If a key appears in "
                #                                "multiple filters, "
                #                                "those cannot use "
                #                                "membership opertor '=in='")
                field_counts[field_key] = field_counts[field_key] + 1

        ## Check the reserved keywords
        if 'limit' in field_counts.keys() and field_counts['limit'] > 1:
            raise RestInputValidationError("You cannot specify limit more than "
                                           "once")
        if 'offset' in field_counts.keys() and field_counts['offset'] > 1:
            raise RestInputValidationError(
                "You cannot specify offset more than "
                "once")
        if 'perpage' in field_counts.keys() and field_counts['perpage'] > 1:
            raise RestInputValidationError(
                "You cannot specify perpage more than "
                "once")
        if 'orderby' in field_counts.keys() and field_counts['orderby'] > 1:
            raise RestInputValidationError(
                "You cannot specify orderby more than "
                "once")
        if 'alist' in field_counts.keys() and field_counts['alist'] > 1:
            raise RestInputValidationError("You cannot specify alist more than "
                                           "once")
        if 'nalist' in field_counts.keys() and field_counts['nalist'] > 1:
            raise RestInputValidationError(
                "You cannot specify nalist more than "
                "once")
        if 'elist' in field_counts.keys() and field_counts['elist'] > 1:
            raise RestInputValidationError("You cannot specify elist more than "
                                           "once")
        if 'nelist' in field_counts.keys() and field_counts['nelist'] > 1:
            raise RestInputValidationError(
                "You cannot specify nelist more than "
                "once")

        ## Extract results
        for field in field_list:

            if field[0] == 'limit':
                if field[1] == '=':
                    limit = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'limit'")
            elif field[0] == 'offset':
                if field[1] == '=':
                    offset = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'offset'")
            elif field[0] == 'perpage':
                if field[1] == '=':
                    perpage = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'perpage'")

            elif field[0] == 'alist':
                if field[1] == '=':
                    alist = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'alist'")
            elif field[0] == 'nalist':
                if field[1] == '=':
                    nalist = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'nalist'")
            elif field[0] == 'elist':
                if field[1] == '=':
                    elist = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'elist'")
            elif field[0] == 'nelist':
                if field[1] == '=':
                    nelist = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'nelist'")

            elif field[0] == 'orderby':
                if field[1] == '=':
                    # Consider value (gives string) and valueList (gives list of
                    # strings) cases
                    if type(field[2]) == list:
                        orderby.extend(field[2])
                    else:
                        orderby.extend([field[2]])
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' "
                        "is permitted after 'orderby'")
            else:

                ## Construct the filter entry.
                field_key = field[0]
                operator = field[1]
                field_value = field[2]

                if isinstance(field_value,
                              datetime_precision) and operator == '=':
                    filter_value = self.build_datetime_filter(field_value)
                else:
                    filter_value = {self.op_conv_map[field[1]]: field_value}

                # Here I treat the AND clause
                if field_counts[field_key] > 1:

                    if field_key not in filters.keys():
                        filters.update({
                            field_key: {
                                'and': [filter_value]
                            }
                        })
                    else:
                        filters[field_key]['and'].append(filter_value)
                else:
                    filters.update({field_key: filter_value})

        # #Impose defaults if needed
        # if limit is None:
        #     limit = self.LIMIT_DEFAULT

        return (limit, offset, perpage, orderby, filters, alist, nalist, elist,
                nelist)

    def parse_query_string(self, query_string):
        """
        Function that parse the querystring, extracting infos for limit, offset,
        ordering, filters, attribute and extra projections.
        :param query_string (as obtained from request.query_string)
        :return: parsed values for the querykeys
        """

        from pyparsing import Word, alphas, nums, alphanums, printables, \
            ZeroOrMore, OneOrMore, Suppress, Optional, Literal, Group, \
            QuotedString, Combine, \
            StringStart as SS, StringEnd as SE, \
            WordEnd as WE, \
            ParseException

        from pyparsing import pyparsing_common as ppc
        from dateutil import parser as dtparser
        from psycopg2.tz import FixedOffsetTimezone

        ## Define grammar
        # key types
        key = Word(alphas + '_', alphanums + '_')
        # operators
        operator = (Literal('=like=') | Literal('=ilike=') |
                    Literal('=in=') | Literal('=notin=') |
                    Literal('=') | Literal('!=') |
                    Literal('>=') | Literal('>') |
                    Literal('<=') | Literal('<'))
        # Value types
        valueNum = ppc.number
        valueBool = (Literal('true') | Literal('false')).addParseAction(
            lambda toks: bool(toks[0]))
        valueString = QuotedString('"', escQuote='""')
        valueOrderby = Combine(Optional(Word('+-', exact=1)) + key)

        ## DateTimeShift value. First, compose the atomic values and then
        # combine
        #  them and convert them to datetime objects
        # Date
        valueDate = Combine(
            Word(nums, exact=4) +
            Literal('-') + Word(nums, exact=2) +
            Literal('-') + Word(nums, exact=2)
        )
        # Time
        valueTime = Combine(
            Literal('T') +
            Word(nums, exact=2) +
            Optional(Literal(':') + Word(nums, exact=2)) +
            Optional(Literal(':') + Word(nums, exact=2))
        )
        # Shift
        valueShift = Combine(
            Word('+-', exact=1) +
            Word(nums, exact=2) +
            Optional(Literal(':') + Word(nums, exact=2))
        )
        # Combine atomic values
        valueDateTime = Combine(
            valueDate +
            Optional(valueTime) +
            Optional(valueShift) + WE(printables.translate(None, '&'))
            # To us the
            # word must end with '&' or end of the string
            # Adding  WordEnd  only here is very important. This makes atomic
            # values for date, time and shift not really
            # usable alone individually.
        )

        ############################################################################
        # Function to convert datetime string into datetime object. The
        # format is
        # compliant with ParseAction requirements
        def validate_time(s, loc, toks):

            datetime_string = toks[0]

            # Check the precision
            precision = len(datetime_string.replace('T', ':').split(':'))

            # Parse
            try:
                dt = dtparser.parse(datetime_string)
            except ValueError:
                raise RestInputValidationError(
                    "time value has wrong format. The "
                    "right format is "
                    "<date>T<time><offset>, "
                    "where <date> is expressed as "
                    "[YYYY]-[MM]-[DD], "
                    "<time> is expressed as [HH]:[MM]:["
                    "SS], "
                    "<offset> is expressed as +/-[HH]:["
                    "MM] "
                    "given with "
                    "respect to UTC")
            if dt.tzinfo is not None:
                tzoffset_minutes = int(
                    dt.tzinfo.utcoffset(None).total_seconds() / 60)

                return datetime_precision(dt.replace(tzinfo=FixedOffsetTimezone(
                    offset=tzoffset_minutes, name=None)), precision)
            else:
                return datetime_precision(dt.replace(tzinfo=FixedOffsetTimezone(
                    offset=0, name=None)), precision)

        ########################################################################

        # Convert datetime value to datetime object
        valueDateTime.setParseAction(validate_time)

        # More General types
        value = (valueString | valueBool | valueDateTime | valueNum |
                 valueOrderby)
        # List of values (I do not check the homogeneity of the types of values,
        # query builder will do it in a sense)
        valueList = Group(value + OneOrMore(Suppress(',') + value) + Optional(
            Suppress(',')))

        # Fields
        singleField = Group(key + operator + value)
        listField = Group(
            key + (Literal('=in=') | Literal('=notin=')) + valueList)
        orderbyField = Group(key + Literal('=') + valueList)
        Field = (listField | orderbyField | singleField)

        # Fields separator
        separator = Suppress(Literal('&'))

        # General query string
        generalGrammar = SS() + Optional(Field) + ZeroOrMore(
            separator + Field) + \
                         Optional(separator) + SE()

        ## Parse the query string
        try:
            fields = generalGrammar.parseString(query_string)
            field_dict = fields.asDict()
            field_list = fields.asList()
        except ParseException as e:
            raise RestInputValidationError(
                "The query string format is invalid. "
                "Parser returned this massage: \"{"
                "}.\" Please notice that the column "
                "number "
                "is counted from "
                "the first character of the query "
                "string.".format(e))

        ## return the translator instructions elaborated from the field_list
        return self.build_translator_parameters(field_list)
