from aiida.common.exceptions import InputValidationError, ValidationError
from aiida.restapi.common.exceptions import RestValidationError, \
    RestInputValidationError
from flask import jsonify
from aiida.restapi.common.config import PERPAGE_DEFAULT, PREFIX


def strip_prefix(path):
    if path.startswith(PREFIX):
        return path[len(PREFIX):]
    else:
        raise ValidationError('path has to start with {}'.format(PREFIX))

def split_path(path):
    """
    :param path: entire path contained in flask request
    :return: list of each element separated by '/'
    """
    # type: (string) -> (list_of_strings).
    return filter(None, path.split('/'))


def parse_path(path_string):
    """
    Takes the path and parse it checking its validity. Does not parse "io",
    "content" fields. I do not check the validity of the path, since I assume
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
    path = split_path(strip_prefix(path_string))

    ## Pop out iteratively the "words" of the path until it is an empty list.
    ##  This way it should be easier to plug in more endpoint logic
    # Object type
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
    # Result type (input, output, attributes, extras)
    if path[0] == "io" or path[0] == "content":
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


def validate_request(limit=None, offset=None, perpage=None, page=None):
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


def paginate(page, perpage, total_count):
    """
    Calculates limit and offset for the reults of a query,
    given the page and the number of restuls per page.
    Moreover, calculates the last available page and raises an exception if the
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
        perpage = PERPAGE_DEFAULT

    ## First_page is anyway 1
    first_page = 1

    ## Calculate last page
    if total_count == 0:
        last_page = 1
    else:
        last_page = int(ceil(float(total_count) / float(perpage)))

    ## Check validity of required page and calculate limit, offset, previous,
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


def build_headers(rel_pages=None, url=None, total_count=None):
    """
    Construct the header dictionary for an HTTP response. It includes related
     pages, total count of results (before pagination).
    :param rel_pages: a dictionary defining related pages (first, prev, next,
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
        path_elems = split_path(path)

        if path_elems.pop(-1) == 'page' or path_elems.pop(-1) == 'page':
            links = []
            for (rel, page) in rel_pages.iteritems():
                if page is not None:
                    links.append(make_rel_url(rel, page))
            headers['Link'] = ''.join(links)
        else:
            pass

    return headers


def build_response(status=200, headers=None, data=None):
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


def parse_query_string(query_string):
    """
    Function that parse the querystring, extracting infos for limit, offset,
    ordering, filters, attribute and extra projections.
    :param query_string (as obtained from request.query_string)
    :return: parsed values for the querykeys
    """

    op_conv_map = {
        '=': '==',
        '=in=': '==',
        '>': '>',
        '<': '<',
        '>=': '>=',
        '<=': '<=',
        '=like=': 'like',
        '=ilike=': 'ilike'
        }


    from pyparsing import Word, alphas, nums, alphanums, ZeroOrMore, \
        OneOrMore, \
        Suppress, Optional, Literal, Group, QuotedString, Combine,\
        StringStart as SS, StringEnd as SE, ParseException

    from pyparsing import pyparsing_common as ppc

    ## Define grammar
    # key types
    key = Word(alphas + '_', alphanums + '_')
    # operators
    operator = (Literal('=like=') | Literal('=ilike=') | Literal('=in=') |
                Literal('=') | Literal('>=') | Literal('>') |
                Literal('<=') | Literal('<'))
    # Value types
    valueNum = ppc.number
    valueBool = (Literal('true') | Literal('false')).addParseAction(lambda toks: bool(toks[0]))
    valueString = QuotedString('"', escQuote='""')
    valueOrderby = Combine(Optional(Word('+-',exact=1)) + key)
    #TODO support for datetime
    #valueDateTime = Combine()


    # More General types
    value = (valueString | valueBool | valueNum | valueOrderby)
    # List of values (I do not check the homogeneity of the types of values,
    # query builder will do it in a sense)
    valueList = Group(value + OneOrMore(Suppress(',') + value) + Optional(
        Suppress(',')))

    # Fields
    singleField = Group(key + operator + value)
    listField = Group(key + Literal('=in=') + valueList)
    orderbyField = Group(key + Literal('=') + valueList)
    Field = (listField | orderbyField | singleField)

    # Fields separator
    separator = Suppress(Literal('&'))

    # General query string
    generalGrammar = SS() + Optional(Field) + ZeroOrMore(separator + Field) + \
                     Optional(separator) + SE()

    ## Parse the query string
    try:
        fields = generalGrammar.parseString(query_string).asList()
    except ParseException:
        #raise RestInputValidationError("The query string format is invalid")
        raise ParseException("The query string format is invalid")

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
    for field in fields:
        field_key = field[0]
        if field_key not in field_counts.keys():
            field_counts[field_key] = 1
        else:
            field_counts[field_key] = field_counts[field_key] + 1

    ## Check the reserved keywords
    if 'limit' in field_counts.keys() and field_counts['limit'] > 1:
        raise RestInputValidationError("You cannot specify limit more than "
                                       "once")
    if 'offset' in field_counts.keys() and field_counts['offset'] > 1:
        raise RestInputValidationError("You cannot specify offset more than "
                                       "once")
    if 'perpage' in field_counts.keys() and field_counts['perpage'] > 1:
        raise RestInputValidationError("You cannot specify perpage more than "
                                       "once")
    if 'orderby' in field_counts.keys() and field_counts['orderby'] > 1:
        raise RestInputValidationError("You cannot specify orderby more than "
                                       "once")
    if 'alist' in field_counts.keys() and field_counts['alist'] > 1:
        raise RestInputValidationError("You cannot specify alist more than "
                                       "once")
    if 'nalist' in field_counts.keys() and field_counts['nalist'] > 1:
        raise RestInputValidationError("You cannot specify nalist more than "
                                       "once")
    if 'elist' in field_counts.keys() and field_counts['elist'] > 1:
        raise RestInputValidationError("You cannot specify elist more than "
                                       "once")
    if 'nelist' in field_counts.keys() and field_counts['nelist'] > 1:
        raise RestInputValidationError("You cannot specify nelist more than "
                                       "once")


    ## Extract results
    for field in fields:
        if field[0] == 'limit':
            if field[1] == '=':
                limit = field[2]
            else:
                raise RestInputValidationError("only assignment operator '=' "
                                               "is permitted after 'limit'")
        elif field[0] == 'offset':
            if field[1] == '=':
                offset = field[2]
            else:
                raise RestInputValidationError("only assignment operator '=' "
                                               "is permitted after 'offset'")
        elif field[0] == 'perpage':
            if field[1] == '=':
                perpage = field[2]
            else:
                raise RestInputValidationError("only assignment operator '=' "
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
                raise RestInputValidationError("only assignment operator '=' "
                                               "is permitted after 'orderby'")
        else:
            # Treat the ordinary filter case
            field_key = field[0]
            # Here I treat the AND clause
            if field_counts[field_key] > 1:
                if field_key not in filters.keys():
                    filters.update({field_key: {'and': [{op_conv_map[field[
                        1]]: field[2]}]}})
                else:
                    filters[field_key]['and'].append({op_conv_map[field[1]]:
                                                     field[2]})
            else:
                filters.update({field_key: {op_conv_map[field[1]]: field[2]}})

    return (limit, offset, perpage, orderby, filters, alist, nalist, elist,
            nelist)


# ## Define grammar
# # Key types
# key = Word(alphanums + '_-')
# timekey = key.copy().addCondition(lambda toks: 'time' in toks[0])
# # Operators
# operator = (Literal('=like=') | Literal('=ilike=') | Literal('=') |
#             Literal('>=') | Literal('>') |
#             Literal('<=') | Literal('<'))
# # Values
# valueString = QuotedString('"', escQuote='""')
# valueBool = (Literal('true') | Literal('false')).addParseAction(lambda
#                                                                     toks: bool(
#     toks[0]))
# valueInt = Word(nums + '+-').addParseAction(lambda toks: int(toks[0]))
# valueFloat = Word(nums + '+-.').addParseAction(
#     lambda toks: float(toks[0]))
# valueGeneric = Word(alphanums + '+-%_.')
# valueNum = (valueInt | valueFloat)
# value = (valueString | valueBool | valueNum | valueGeneric)
# valueList = Group(value + OneOrMore(Suppress(',') + value) + Optional(
#     Suppress(',')))
#
# ##TODO manage better the parse exceptions in general
# from dateutil.parser import parse
#
# valueTime = Word(nums + 'TZ' + '+-:.')
#
#
# # Function compliant with ParseAction definition
# def validate_time(s, loc, toks):
#     try:
#         return parse(toks[0])
#     except ValueError:
#         raise RestInputValidationError("time value has wrong format. The "
#                                        "right format is "
#                                        "<date>T<time>Z<offset>, "
#                                        "where <date> is expressed as [MM]-["
#                                        "DD]-[YY], "
#                                        "<time> is expressed as [HH]:[MM]:["
#                                        "SS], "
#                                        "<offset> is expressed as [HH]:[MM] "
#                                        "given with "
#                                        "respect to UTC")
#
#
# valueTime.addParseAction(validate_time)
#
# # time values list
# valueTimeList = Group(valueTime + OneOrMore(Suppress(',') + valueTime) +
#                       Optional(Suppress(',')))
#
# # Query eparator
# separator = Suppress('&')
#
# # Define field types (or lists of values)
# basicField = Group(key + operator + value)
# timeField = Group(timekey + operator + valueTime)
# listField = Group(key + Literal('=') + valueList)
# timeListField = Group(timekey + Literal('=') + valueTimeList)
#
# Field = (timeListField | timeField | listField | basicField)
#
# generalGrammar = SS() + Optional(Field) + ZeroOrMore(separator + Field) + \
#                  Optional(separator) + SE()
