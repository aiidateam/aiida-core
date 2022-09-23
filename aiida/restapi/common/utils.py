# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Util methods """
from datetime import datetime, timedelta
import urllib.parse

from flask import jsonify
from flask.json import JSONEncoder
from wrapt import decorator

from aiida.common.exceptions import InputValidationError, ValidationError
from aiida.common.utils import DatetimePrecision
from aiida.manage import get_manager
from aiida.restapi.common.exceptions import RestInputValidationError, RestValidationError

# Important to match querybuilder keys
PK_DBSYNONYM = 'id'
# Example uuid (version 4)
UUID_REF = 'd55082b6-76dc-426b-af89-0e08b59524d2'


########################## Classes #####################
class CustomJSONEncoder(JSONEncoder):
    """
    Custom json encoder for serialization.
    This has to be provided to the Flask app in order to replace the default
    encoder.
    """

    def default(self, o):
        # pylint: disable=method-hidden
        """
        Override default method from JSONEncoder to change serializer
        :param o: Object e.g. dict, list that will be serialized
        :return: serialized object
        """

        from aiida.restapi.common.config import SERIALIZER_CONFIG

        # Treat the datetime objects
        if isinstance(o, datetime):
            if 'datetime_format' in SERIALIZER_CONFIG and SERIALIZER_CONFIG['datetime_format'] != 'default':
                if SERIALIZER_CONFIG['datetime_format'] == 'asinput':
                    if o.utcoffset() is not None:
                        o = o - o.utcoffset()
                        return '-'.join([str(o.year), str(o.month).zfill(2),
                                         str(o.day).zfill(2)]) + 'T' + \
                               ':'.join([str(
                                   o.hour).zfill(2), str(o.minute).zfill(2),
                                         str(o.second).zfill(2)])

        # To support bytes objects, try to decode to a string
        try:
            return o.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            pass

        # If not returned yet, do it in the default way
        return JSONEncoder.default(self, o)


class Utils:
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

        self.prefix = kwargs['PREFIX']
        self.perpage_default = kwargs['PERPAGE_DEFAULT']
        self.limit_default = kwargs['LIMIT_DEFAULT']

    def strip_api_prefix(self, path):
        """
        Removes the PREFIX from an URL path. PREFIX must be defined in the
        config.py file::

            PREFIX = "/api/v2"
            path = "/api/v2/calculations/page/2"
            strip_api_prefix(path) ==> "/calculations/page/2"

        :param path: the URL path string
        :return: the same URL without the prefix
        """
        if path.startswith(self.prefix):
            return path[len(self.prefix):]

        raise ValidationError(f'path has to start with {self.prefix}')

    @staticmethod
    def split_path(path):
        """
        :param path: entire path contained in flask request
        :return: list of each element separated by '/'
        """
        return [f for f in path.split('/') if f]

    def parse_path(self, path_string, parse_pk_uuid=None):
        # pylint: disable=too-many-return-statements,too-many-branches, too-many-statements
        """
        Takes the path and parse it checking its validity. Does not parse "io",
        "content" fields. I do not check the validity of the path, since I assume
        that this is done by the Flask routing methods.

        :param path_string: the path string
        :param parse_id_uuid: if 'pk' ('uuid') expects an integer (uuid starting pattern)
        :return: resource_type (string)
            page (integer)
            node_id (string: uuid starting pattern, int: pk)
            query_type (string))
        """

        ## Initialization
        page = None
        node_id = None
        query_type = 'default'
        path = self.split_path(self.strip_api_prefix(path_string))

        ## Pop out iteratively the "words" of the path until it is an empty
        # list.
        ##  This way it should be easier to plug in more endpoint logic

        # Resource type
        resource_type = path.pop(0)
        if not path:
            return (resource_type, page, node_id, query_type)

        # Validate uuid or starting pattern of uuid.
        # Technique: - take our UUID_REF and replace the first characters the
        #  string to be validated as uuid.
        #            - validate instead the newly built string
        if parse_pk_uuid == 'pk':
            raw_id = path[0]
            try:
                # Check whether it can be an integer
                node_id = int(raw_id)
            except ValueError:
                pass
            else:
                path.pop(0)
        elif parse_pk_uuid == 'uuid':
            import uuid
            raw_id = path[0]
            maybe_uuid = raw_id + UUID_REF[len(raw_id):]
            try:
                _ = uuid.UUID(maybe_uuid, version=4)
            except ValueError:
                # assume that it cannot be an id and go to the next check
                pass
            else:
                # It is a node_id so pop out the path element
                node_id = raw_id
                path.pop(0)

        if not path:
            return (resource_type, page, node_id, query_type)

        if path[0] in [
            'projectable_properties', 'statistics', 'full_types', 'full_types_count', 'download', 'download_formats',
            'report', 'status', 'input_files', 'output_files'
        ]:
            query_type = path.pop(0)
            if path:
                raise RestInputValidationError('Given url does not accept further fields')
        elif path[0] in ['links', 'contents']:
            path.pop(0)
            query_type = path.pop(0)
        elif path[0] in ['repo']:
            path.pop(0)
            query_type = f'repo_{path.pop(0)}'

        if not path:
            return (resource_type, page, node_id, query_type)

        # Page (this has to be in any case the last field)
        if path[0] == 'page':
            path.pop(0)
            if not path:
                page = 1
                return (resource_type, page, node_id, query_type)
            page = int(path.pop(0))
        else:
            raise RestInputValidationError('The requested URL is not found on the server.')

        return (resource_type, page, node_id, query_type)

    def validate_request(
        self, limit=None, offset=None, perpage=None, page=None, query_type=None, is_querystring_defined=False
    ):
        # pylint: disable=fixme,no-self-use,too-many-arguments,too-many-branches
        """
        Performs various checks on the consistency of the request.
        Add here all the checks that you want to do, except validity of the page
        number that is done in paginate().
        Future additional checks must be added here
        """

        # TODO Consider using **kwargs so to make easier to add more validations
        # 1. perpage incompatible with offset and limits
        if perpage is not None and (limit is not None or offset is not None):
            raise RestValidationError('perpage key is incompatible with limit and offset')
        # 2. /page/<int: page> in path is incompatible with limit and offset
        if page is not None and (limit is not None or offset is not None):
            raise RestValidationError('requesting a specific page is incompatible with limit and offset')
        # 3. perpage requires that the path contains a page request
        if perpage is not None and page is None:
            raise RestValidationError(
                'perpage key requires that a page is '
                'requested (i.e. the path must contain '
                '/page/)'
            )
        # 4. No querystring if query type = projectable_properties'
        if query_type in ('projectable_properties',) and is_querystring_defined:
            raise RestInputValidationError('projectable_properties requests do not allow specifying a query string')

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
            raise InputValidationError('page number must be an integer')
        try:
            total_count = int(total_count)
        except ValueError:
            raise InputValidationError('total_count must be an integer')
        # Non-mandatory params
        if perpage is not None:
            try:
                perpage = int(perpage)
            except ValueError:
                raise InputValidationError('perpage must be an integer')
        else:
            perpage = self.perpage_default

        ## First_page is anyway 1
        first_page = 1

        ## Calculate last page
        if total_count == 0:
            last_page = 1
        else:
            last_page = int(ceil(total_count / perpage))

        ## Check validity of required page and calculate limit, offset,
        # previous,
        #  and next page
        if page > last_page or page < 1:
            raise RestInputValidationError(
                f'Non existent page requested. The page range is [{first_page} : {last_page}]'
            )

        limit = perpage
        offset = (page - 1) * perpage
        prev_page = None
        if page > 1:
            prev_page = page - 1

        next_page = None
        if page < last_page:
            next_page = page + 1

        rel_pages = dict(prev=prev_page, next=next_page, first=first_page, last=last_page)

        return (limit, offset, rel_pages)

    def build_headers(self, rel_pages=None, url=None, total_count=None):
        """
        Construct the header dictionary for an HTTP response. It includes related
        pages, total count of results (before pagination).

        :param rel_pages: a dictionary defining related pages (first, prev, next, last)
        :param url: (string) the full url, i.e. the url that the client uses to get Rest resources
        """

        ## Type validation
        # mandatory parameters
        try:
            total_count = int(total_count)
        except ValueError:
            raise InputValidationError('total_count must be a long integer')

        # non mandatory parameters
        if rel_pages is not None and not isinstance(rel_pages, dict):
            raise InputValidationError('rel_pages must be a dictionary')

        if url is not None:
            try:
                url = str(url)
            except ValueError:
                raise InputValidationError('url must be a string')

        ## Input consistency
        # rel_pages cannot be defined without url
        if rel_pages is not None and url is None:
            raise InputValidationError("'rel_pages' parameter requires 'url' parameter to be defined")

        headers = {}

        ## Setting mandatory headers
        # set X-Total-Count
        headers['X-Total-Count'] = total_count
        expose_header = ['X-Total-Count']

        ## Two auxiliary functions
        def split_url(url):
            """ Split url into path and query string """
            if '?' in url:
                [path, query_string] = url.split('?')
                question_mark = '?'
            else:
                path = url
                query_string = ''
                question_mark = ''
            return (path, query_string, question_mark)

        def make_rel_url(rel, page):
            new_path_elems = path_elems + ['page', str(page)]
            return f"<{'/'.join(new_path_elems)}{question_mark}{query_string}>; rel={rel}, "

        ## Setting non-mandatory parameters
        # set links to related pages
        if rel_pages is not None:
            (path, query_string, question_mark) = split_url(url)
            path_elems = self.split_path(path)

            if path_elems.pop(-1) == 'page' or path_elems.pop(-1) == 'page':
                links = []
                for (rel, page) in rel_pages.items():
                    if page is not None:
                        links.append(make_rel_url(rel, page))
                headers['Link'] = ''.join(links)
                expose_header.append('Link')
            else:
                pass

        # to expose header access in cross-domain requests
        headers['Access-Control-Expose-Headers'] = ','.join(expose_header)

        return headers

    @staticmethod
    def build_response(status=200, headers=None, data=None):
        """
        Build the response

        :param status: status of the response, e.g. 200=OK, 400=bad request
        :param headers: dictionary for additional header k,v pairs,
            e.g. X-total-count=<number of rows resulting from query>
        :param data: a dictionary with the data returned by the Resource

        :return: a Flask response object
        """

        ## Type checks
        # mandatory parameters
        if not isinstance(data, dict):
            raise InputValidationError('data must be a dictionary')

        # non-mandatory parameters
        if status is not None:
            try:
                status = int(status)
            except ValueError:
                raise InputValidationError('status must be an integer')

        if headers is not None and not isinstance(headers, dict):
            raise InputValidationError('header must be a dictionary')

        # Build response
        response = jsonify(data)
        response.status_code = status

        if headers is not None:
            for key, val in headers.items():
                response.headers[key] = val

        return response

    @staticmethod
    def build_datetime_filter(dtobj):
        """
        This function constructs a filter for a datetime object to be in a
        certain datetime interval according to the precision.

        The interval is [reference_datetime, reference_datetime + delta_time],
        where delta_time is a function fo the required precision.

        This function should be used to replace a datetime filter based on
        the equality operator that is inehrently "picky" because it implies
        matching two datetime objects down to the microsecond or something,
        by a "tolerant" operator which checks whether the datetime is in an
        interval.

        :return: a suitable entry of the filter dictionary
        """

        if not isinstance(dtobj, DatetimePrecision):
            TypeError('dtobj argument has to be a DatetimePrecision object')

        reference_datetime = dtobj.dtobj
        precision = dtobj.precision

        ## Define interval according to the precision
        if precision == 1:
            delta_time = timedelta(days=1)
        elif precision == 2:
            delta_time = timedelta(hours=1)
        elif precision == 3:
            delta_time = timedelta(minutes=1)
        elif precision == 4:
            delta_time = timedelta(seconds=1)
        else:
            raise RestValidationError('The datetime resolution is not valid.')

        filters = {'and': [{'>=': reference_datetime}, {'<': reference_datetime + delta_time}]}

        return filters

    def build_translator_parameters(self, field_list):
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        """
        Takes a list of elements resulting from the parsing the query_string and
        elaborates them in order to provide translator-compliant instructions

        :param field_list: a (nested) list of elements resulting from parsing the query_string
        :returns: the filters in the
        """
        ## Create void variables
        filters = {}
        orderby = []
        limit = None
        offset = None
        perpage = None
        filename = None
        download_format = None
        download = True
        attributes = None
        attributes_filter = None
        extras = None
        extras_filter = None
        full_type = None
        profile = None

        # io tree limit parameters
        tree_in_limit = None
        tree_out_limit = None

        ## Count how many time a key has been used for the filters
        # and check if reserved keyword have been used twice
        field_counts = {}
        for field in field_list:
            field_key = field[0]
            if field_key not in field_counts:
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
        if 'limit' in field_counts and field_counts['limit'] > 1:
            raise RestInputValidationError('You cannot specify limit more than once')
        if 'offset' in field_counts and field_counts['offset'] > 1:
            raise RestInputValidationError('You cannot specify offset more than once')
        if 'perpage' in field_counts and field_counts['perpage'] > 1:
            raise RestInputValidationError('You cannot specify perpage more than once')
        if 'orderby' in field_counts and field_counts['orderby'] > 1:
            raise RestInputValidationError('You cannot specify orderby more than once')
        if 'download' in field_counts and field_counts['download'] > 1:
            raise RestInputValidationError('You cannot specify download more than once')
        if 'download_format' in field_counts and field_counts['download_format'] > 1:
            raise RestInputValidationError('You cannot specify download_format more than once')
        if 'filename' in field_counts and field_counts['filename'] > 1:
            raise RestInputValidationError('You cannot specify filename more than once')
        if 'in_limit' in field_counts and field_counts['in_limit'] > 1:
            raise RestInputValidationError('You cannot specify in_limit more than once')
        if 'out_limit' in field_counts and field_counts['out_limit'] > 1:
            raise RestInputValidationError('You cannot specify out_limit more than once')
        if 'attributes' in field_counts and field_counts['attributes'] > 1:
            raise RestInputValidationError('You cannot specify attributes more than once')
        if 'attributes_filter' in field_counts and field_counts['attributes_filter'] > 1:
            raise RestInputValidationError('You cannot specify attributes_filter more than once')
        if 'extras' in field_counts and field_counts['extras'] > 1:
            raise RestInputValidationError('You cannot specify extras more than once')
        if 'extras_filter' in field_counts and field_counts['extras_filter'] > 1:
            raise RestInputValidationError('You cannot specify extras_filter more than once')
        if 'full_type' in field_counts and field_counts['full_type'] > 1:
            raise RestInputValidationError('You cannot specify full_type more than once')
        if 'profile' in field_counts and field_counts['profile'] > 1:
            raise RestInputValidationError('You cannot specify profile more than once')

        ## Extract results
        for field in field_list:
            if field[0] == 'profile':
                if field[1] == '=':
                    profile = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'profile'")
            elif field[0] == 'limit':
                if field[1] == '=':
                    limit = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'limit'")
            elif field[0] == 'offset':
                if field[1] == '=':
                    offset = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'offset'")
            elif field[0] == 'perpage':
                if field[1] == '=':
                    perpage = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'perpage'")

            elif field[0] == 'orderby':
                if field[1] == '=':
                    # Consider value (gives string) and value_list (gives list of
                    # strings) cases
                    if isinstance(field[2], list):
                        orderby.extend(field[2])
                    else:
                        orderby.extend([field[2]])
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'orderby'")

            elif field[0] == 'download':
                if field[1] == '=':
                    download = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'download'")

            elif field[0] == 'download_format':
                if field[1] == '=':
                    download_format = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'download_format'")

            elif field[0] == 'filename':
                if field[1] == '=':
                    filename = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'filename'")

            elif field[0] == 'full_type':
                if field[1] == '=':
                    full_type = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'full_type'")

            elif field[0] == 'in_limit':
                if field[1] == '=':
                    tree_in_limit = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'in_limit'")

            elif field[0] == 'out_limit':
                if field[1] == '=':
                    tree_out_limit = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'out_limit'")

            elif field[0] == 'attributes':
                if field[1] == '=':
                    attributes = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'attributes'")

            elif field[0] == 'attributes_filter':
                if field[1] == '=':
                    attributes_filter = field[2]
                else:
                    raise RestInputValidationError(
                        "only assignment operator '=' is permitted after 'attributes_filter'"
                    )
            elif field[0] == 'extras':
                if field[1] == '=':
                    extras = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'extras'")

            elif field[0] == 'extras_filter':
                if field[1] == '=':
                    extras_filter = field[2]
                else:
                    raise RestInputValidationError("only assignment operator '=' is permitted after 'extras_filter'")

            else:

                ## Construct the filter entry.
                field_key = field[0]
                operator = field[1]
                field_value = field[2]

                if isinstance(field_value, DatetimePrecision) and operator == '=':
                    filter_value = self.build_datetime_filter(field_value)
                else:
                    filter_value = {self.op_conv_map[field[1]]: field_value}

                # Here I treat the AND clause
                if field_counts[field_key] > 1:

                    if field_key not in filters.keys():
                        filters.update({field_key: {'and': [filter_value]}})
                    else:
                        filters[field_key]['and'].append(filter_value)
                else:
                    filters.update({field_key: filter_value})

        # #Impose defaults if needed
        # if limit is None:
        #     limit = self.limit_default

        return (
            limit, offset, perpage, orderby, filters, download_format, download, filename, tree_in_limit,
            tree_out_limit, attributes, attributes_filter, extras, extras_filter, full_type, profile
        )

    def parse_query_string(self, query_string):
        # pylint: disable=too-many-locals
        """
        Function that parse the querystring, extracting infos for limit, offset,
        ordering, filters, attribute and extra projections.
        :param query_string (as obtained from request.query_string)
        :return: parsed values for the querykeys
        """
        from psycopg2.tz import FixedOffsetTimezone
        from pyparsing import Combine, Group, Literal, OneOrMore, Optional, ParseException, QuotedString
        from pyparsing import StringEnd as SE
        from pyparsing import StringStart as SS
        from pyparsing import Suppress, Word
        from pyparsing import WordEnd as WE
        from pyparsing import ZeroOrMore, alphanums, alphas, nums, printables
        from pyparsing import pyparsing_common as ppc

        ## Define grammar
        # key types
        key = Word(f'{alphas}_', f'{alphanums}_-')
        # operators
        operator = (
            Literal('=like=') | Literal('=ilike=') | Literal('=in=') | Literal('=notin=') | Literal('=') |
            Literal('!=') | Literal('>=') | Literal('>') | Literal('<=') | Literal('<')
        )
        # Value types
        value_num = ppc.number
        value_bool = (Literal('true') | Literal('false')).addParseAction(lambda toks: toks[0] == 'true')
        value_string = QuotedString('"', escQuote='""')
        value_orderby = Combine(Optional(Word('+-', exact=1)) + key)

        ## DateTimeShift value. First, compose the atomic values and then
        # combine
        #  them and convert them to datetime objects
        # Date
        value_date = Combine(
            Word(nums, exact=4) + Literal('-') + Word(nums, exact=2) + Literal('-') + Word(nums, exact=2)
        )
        # Time
        value_time = Combine(
            Literal('T') + Word(nums, exact=2) + Optional(Literal(':') + Word(nums, exact=2)) +
            Optional(Literal(':') + Word(nums, exact=2))
        )
        # Shift
        value_shift = Combine(Word('+-', exact=1) + Word(nums, exact=2) + Optional(Literal(':') + Word(nums, exact=2)))
        # Combine atomic values
        value_datetime = Combine(
            value_date + Optional(value_time) + Optional(value_shift) + WE(printables.replace('&', ''))
            # To us the
            # word must end with '&' or end of the string
            # Adding  WordEnd  only here is very important. This makes atomic
            # values for date, time and shift not really
            # usable alone individually.
        )

        ########################################################################

        def validate_time(toks):
            """
            Function to convert datetime string into datetime object. The format is
            compliant with ParseAction requirements

            :param toks: datetime string passed in tokens
            :return: datetime object
            """
            datetime_string = toks[0]

            # Check the precision
            precision = len(datetime_string.replace('T', ':').split(':'))

            # Parse
            try:
                dtobj = datetime.fromisoformat(datetime_string)
            except ValueError:
                raise RestInputValidationError(
                    'time value has wrong format. The '
                    'right format is '
                    '<date>T<time><offset>, '
                    'where <date> is expressed as '
                    '[YYYY]-[MM]-[DD], '
                    '<time> is expressed as [HH]:[MM]:['
                    'SS], '
                    '<offset> is expressed as +/-[HH]:['
                    'MM] '
                    'given with '
                    'respect to UTC'
                )
            if dtobj.tzinfo is not None and dtobj.utcoffset() is not None:
                tzoffset_minutes = int(dtobj.utcoffset().total_seconds() // 60)
                return DatetimePrecision(
                    dtobj.replace(tzinfo=FixedOffsetTimezone(offset=tzoffset_minutes, name=None)), precision
                )

            return DatetimePrecision(dtobj.replace(tzinfo=FixedOffsetTimezone(offset=0, name=None)), precision)

        ########################################################################

        # Convert datetime value to datetime object
        value_datetime.setParseAction(validate_time)

        # More General types
        value = (value_string | value_bool | value_datetime | value_num | value_orderby)
        # List of values (I do not check the homogeneity of the types of values,
        # query builder will do it somehow)
        value_list = Group(value + OneOrMore(Suppress(',') + value) + Optional(Suppress(',')))

        # Fields
        single_field = Group(key + operator + value)
        list_field = Group(key + (Literal('=in=') | Literal('=notin=')) + value_list)
        orderby_field = Group(key + Literal('=') + value_list)
        field = (list_field | orderby_field | single_field)

        # Fields separator
        separator = Suppress(Literal('&'))

        # General query string
        general_grammar = SS() + Optional(field) + ZeroOrMore(
            separator + field) + \
                          Optional(separator) + SE()

        ## Parse the query string
        try:
            fields = general_grammar.parseString(query_string)

            # JQuery adds _=timestamp a parameter to not use cached data/response.
            # To handle query, remove this "_" parameter from the query string
            # For more details check issue #789
            # (https://github.com/aiidateam/aiida-core/issues/789) in aiida-core
            field_list = [entry for entry in fields.asList() if entry[0] != '_']

        except ParseException as err:
            raise RestInputValidationError(
                'The query string format is invalid. '
                "Parser returned this massage: \"{"
                "}.\" Please notice that the column "
                'number '
                'is counted from '
                'the first character of the query '
                'string.'.format(err)
            )

        ## return the translator instructions elaborated from the field_list
        return self.build_translator_parameters(field_list)


def list_routes():
    """List available routes"""
    from flask import current_app

    output = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue

        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f'{rule.endpoint:15s} {methods:20s} {rule}')
        output.append(line)

    return sorted(set(output))


@decorator
def close_thread_connection(wrapped, _, args, kwargs):
    """Close the profile's storage connection, for the current thread.

    This decorator can be used for router endpoints.
    It is needed due to the server running in threaded mode, i.e., creating a new thread for each incoming request,
    and leaving connections unreleased.

    Note, this is currently hard-coded to the `PsqlDosBackend` storage backend.
    """
    try:
        return wrapped(*args, **kwargs)
    finally:
        get_manager().get_profile_storage().get_session().close()
