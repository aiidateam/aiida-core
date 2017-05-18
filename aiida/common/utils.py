# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import datetime
import filecmp
import functools
import inspect
import os.path
import string
import sys

from dateutil.parser import parse

from aiida.common.exceptions import ConfigurationError



class classproperty(object):
    """
    A class that, when used as a decorator, works as if the
    two decorators @property and @classmethod where applied together
    (i.e., the object works as a property, both for the Class and for any
    of its instance; and is called with the class cls rather than with the
    instance as its first argument).
    """

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class abstractclassmethod(classmethod):
    """
    A decorator indicating abstract classmethods.

    Backported from python3.
    """
    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class abstractstaticmethod(staticmethod):
    """
    A decorator indicating abstract staticmethods.

    Similar to abstractmethod.
    Backported from python3.
    """

    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractstaticmethod, self).__init__(callable)


def get_configured_user_email():
    """
    Return the email (that is used as the username) configured during the
    first verdi install.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.common.setup import get_profile_config, DEFAULT_USER_CONFIG_FIELD
    from aiida.backends import settings

    try:
        profile_conf = get_profile_config(settings.AIIDADB_PROFILE,
                                          set_test_location=False)
        email = profile_conf[DEFAULT_USER_CONFIG_FIELD]
    # I do not catch the error in case of missing configuration, because
    # it is already a ConfigurationError
    except KeyError:
        raise ConfigurationError("No 'default_user' key found in the "
                                 "AiiDA configuration file".format(
            DEFAULT_USER_CONFIG_FIELD))
    return email


def get_new_uuid():
    """
    Return a new UUID (typically to be used for new nodes).
    It uses the UUID version specified in
    aiida.backends.settings.AIIDANODES_UUID_VERSION
    """
    from aiida.backends.settings import AIIDANODES_UUID_VERSION
    import uuid

    if AIIDANODES_UUID_VERSION != 4:
        raise NotImplementedError("Only version 4 of UUID supported currently")

    the_uuid = uuid.uuid4()
    return unicode(the_uuid)


# To speed up the process (os.path.abspath calls are slow)
_repository_folder_cache = {}


def get_repository_folder(subfolder=None):
    """
    Return the top folder of the local repository.
    """
    try:
        return _repository_folder_cache[subfolder]
    except KeyError:
        try:
            from aiida.settings import REPOSITORY_PATH

            if not os.path.isdir(REPOSITORY_PATH):
                raise ImportError
        except ImportError:
            raise ConfigurationError(
                "The REPOSITORY_PATH variable is not set correctly.")
        if subfolder is None:
            retval = os.path.abspath(REPOSITORY_PATH)
        elif subfolder == "sandbox":
            retval = os.path.abspath(os.path.join(REPOSITORY_PATH, 'sandbox'))
        elif subfolder == "repository":
            retval = os.path.abspath(
                os.path.join(REPOSITORY_PATH, 'repository'))
        else:
            raise ValueError("Invalid 'subfolder' passed to "
                             "get_repository_folder: {}".format(subfolder))
        _repository_folder_cache[subfolder] = retval
        return retval


def escape_for_bash(str_to_escape):
    """
    This function takes any string and escapes it in a way that
    bash will interpret it as a single string.

    Explanation:

    At the end, in the return statement, the string is put within single
    quotes. Therefore, the only thing that I have to escape in bash is the
    single quote character. To do this, I substitute every single
    quote ' with '"'"' which means:

    First single quote: exit from the enclosing single quotes

    Second, third and fourth character: "'" is a single quote character,
    escaped by double quotes

    Last single quote: reopen the single quote to continue the string

    Finally, note that for python I have to enclose the string '"'"'
    within triple quotes to make it work, getting finally: the complicated
    string found below.
    """
    escaped_quotes = str_to_escape.replace("'", """'"'"'""")
    return "'{}'".format(escaped_quotes)


def get_suggestion(provided_string, allowed_strings):
    """
    Given a string and a list of allowed_strings, it returns a string to print
    on screen, with sensible text depending on whether no suggestion is found,
    or one or more than one suggestions are found.

    Args:
        provided_string: the string to compare
        allowed_strings: a list of valid strings

    Returns:
        A string to print on output, to suggest to the user a possible valid
        value.
    """
    import difflib

    similar_kws = difflib.get_close_matches(provided_string,
                                            allowed_strings)
    if len(similar_kws) == 1:
        return "(Maybe you wanted to specify {0}?)".format(similar_kws[0])
    elif len(similar_kws) > 1:
        return "(Maybe you wanted to specify one of these: {0}?)".format(
            string.join(similar_kws, ', '))
    else:
        return "(No similar keywords found...)"


def validate_list_of_string_tuples(val, tuple_length):
    """
    Check that:

    1. ``val`` is a list or tuple
    2. each element of the list:

      a. is a list or tuple
      b. is of length equal to the parameter tuple_length
      c. each of the two elements is a string

    Return if valid, raise ValidationError if invalid
    """
    from aiida.common.exceptions import ValidationError

    err_msg = ("the value must be a list (or tuple) "
               "of length-N list (or tuples), whose elements are strings; "
               "N={}".format(tuple_length))
    if not isinstance(val, (list, tuple)):
        raise ValidationError(err_msg)
    for f in val:
        if (not isinstance(f, (list, tuple)) or
                    len(f) != tuple_length or
                not all(isinstance(s, basestring) for s in f)):
            raise ValidationError(err_msg)

    return True


def conv_to_fortran(val):
    """
    :param val: the value to be read and converted to a Fortran-friendly string.
    """
    # Note that bool should come before integer, because a boolean matches also
    # isinstance(...,int)
    if (isinstance(val, bool)):
        if val:
            val_str = '.true.'
        else:
            val_str = '.false.'
    elif (isinstance(val, (int, long))):
        val_str = "{:d}".format(val)
    elif (isinstance(val, float)):
        val_str = ("{:18.10e}".format(val)).replace('e', 'd')
    elif (isinstance(val, basestring)):
        val_str = "'{!s}'".format(val)
    else:
        raise ValueError("Invalid value passed, accepts only bools, ints, "
                         "floats and strings")

    return val_str


def conv_to_fortran_withlists(val):
    """
    Same as conv_to_fortran but with extra logic to handle lists
    :param val: the value to be read and converted to a Fortran-friendly string.
    """
    # Note that bool should come before integer, because a boolean matches also
    # isinstance(...,int)
    if (isinstance(val, (list, tuple))):
        out_list = []
        for thing in val:
            out_list.append(conv_to_fortran(thing))
        val_str = ", ".join(out_list)
        return val_str
    if (isinstance(val, bool)):
        if val:
            val_str = '.true.'
        else:
            val_str = '.false.'
    elif (isinstance(val, (int, long))):
        val_str = "{:d}".format(val)
    elif (isinstance(val, float)):
        val_str = ("{:18.10e}".format(val)).replace('e', 'd')
    elif (isinstance(val, basestring)):
        val_str = "'{!s}'".format(val)
    else:
        raise ValueError("Invalid value passed, accepts only bools, ints, "
                         "floats and strings")

    return val_str


def get_unique_filename(filename, list_of_filenames):
    """
    Return a unique filename that can be added to the list_of_filenames.

    If filename is not in list_of_filenames, it simply returns the filename
    string itself. Otherwise, it appends a integer number to the filename
    (before the extension) until it finds a unique filename.

    :param filename: the filename to add
    :param list_of_filenames: the list of filenames to which filename
        should be added, without name duplicates

    :returns: Either filename or its modification, with a number appended
        between the name and the extension.
    """
    if filename not in list_of_filenames:
        return filename

    basename, ext = os.path.splitext(filename)

    # Not optimized, but for the moment this should be fast enough
    append_int = 1
    while True:
        new_filename = "{:s}-{:d}{:s}".format(basename, append_int, ext)
        if new_filename not in list_of_filenames:
            break
        append_int += 1
    return new_filename


def md5_file(filename, block_size_factor=128):
    """
    Open a file and return its md5sum (hexdigested).

    :param filename: the filename of the file for which we want the md5sum
    :param block_size_factor: the file is read at chunks of size
        ``block_size_factor * md5.block_size``,
        where ``md5.block_size`` is the block_size used internally by the
        hashlib module.

    :returns: a string with the hexdigest md5.

    :raises: No checks are done on the file, so if it doesn't exists it may
        raise IOError.
    """
    import hashlib

    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        # I read 128 bytes at a time until it returns the empty string b''
        for chunk in iter(
                lambda: f.read(block_size_factor * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def sha1_file(filename, block_size_factor=128):
    """
    Open a file and return its sha1sum (hexdigested).

    :param filename: the filename of the file for which we want the sha1sum
    :param block_size_factor: the file is read at chunks of size
        ``block_size_factor * sha1.block_size``,
        where ``sha1.block_size`` is the block_size used internally by the
        hashlib module.

    :returns: a string with the hexdigest sha1.

    :raises: No checks are done on the file, so if it doesn't exists it may
        raise IOError.
    """
    import hashlib

    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        # I read 128 bytes at a time until it returns the empty string b''
        for chunk in iter(
                lambda: f.read(block_size_factor * sha1.block_size), b''):
            sha1.update(chunk)
    return sha1.hexdigest()


def str_timedelta(dt, max_num_fields=3, short=False, negative_to_zero=False):
    """
    Given a dt in seconds, return it in a HH:MM:SS format.

    :param dt: a TimeDelta object
    :param max_num_fields: maximum number of non-zero fields to show
        (for instance if the number of days is non-zero, shows only
        days, hours and minutes, but not seconds)
    :param short: if False, print always ``max_num_fields`` fields, even
        if they are zero. If True, do not print the first fields, if they
        are zero.
    :param negative_to_zero: if True, set dt = 0 if dt < 0.
    """
    if max_num_fields <= 0:
        raise ValueError("max_num_fields must be > 0")

    s = dt.total_seconds()  # Important to get more than 1 day, and for
    # negative values. dt.seconds would give
    # wrong results in these cases, see
    # http://docs.python.org/2/library/datetime.html
    s = int(s)

    if negative_to_zero:
        if s < 0:
            s = 0

    negative = (s < 0)
    s = abs(s)

    negative_string = " in the future" if negative else " ago"

    # For the moment stay away from months and years, difficult to get
    days, remainder = divmod(s, 3600 * 24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    all_fields = [(days, 'D'), (hours, 'h'), (minutes, 'm'), (seconds, 's')]
    fields = []
    start_insert = False
    counter = 0
    for idx, f in enumerate(all_fields):
        if f[0] != 0:
            start_insert = True
        if (len(all_fields) - idx) <= max_num_fields:
            start_insert = True
        if start_insert:
            if counter >= max_num_fields:
                break
            fields.append(f)
            counter += 1

    if short:
        while len(fields) > 1:  # at least one element has to remain
            if fields[0][0] != 0:
                break
            fields.pop(0)  # remove first element

    # Join the fields
    raw_string = ":".join(["{:02d}{}".format(*f) for f in fields])

    if raw_string.startswith('0'):
        raw_string = raw_string[1:]

    # Return the resulting string, appending a suitable string if the time
    # is negative
    return "{}{}".format(raw_string, negative_string)


def create_display_name(field):
    """
    Given a string, creates the suitable "default" display name: replace
    underscores with spaces, and capitalize each word.

    :return: the converted string
    """
    return ' '.join(_.capitalize() for _ in field.split('_'))


def get_object_string(obj):
    """
    Get a string that identifies this object which can be used to retrieve
    it via :func:`get_object_from_string`.

    :param obj: The object to get the string for
    :return: The string that identifies the object
    """
    if inspect.isfunction(obj):
        return "{}.{}".format(obj.__module__, obj.__name__)
    else:
        return get_class_string(obj)


def get_class_string(obj):
    """
    Return the string identifying the class of the object (module + object name,
    joined by dots).

    It works both for classes and for class instances.
    """
    if inspect.isclass(obj):
        return "{}.{}".format(obj.__module__, obj.__name__)
    else:
        return "{}.{}".format(obj.__module__, obj.__class__.__name__)


def get_object_from_string(string):
    """
    Given a string identifying an object (as returned by the get_class_string
    method) load and return the actual object.
    """
    import importlib

    the_module, _, the_name = string.rpartition('.')

    return getattr(importlib.import_module(the_module), the_name)


def export_shard_uuid(uuid):
    """
    Sharding of the UUID for the import/export
    """
    return os.path.join(uuid[:2], uuid[2:4], uuid[4:])


def grouper(n, iterable):
    """
    Given an iterable, returns an iterable that returns tuples of groups of
    elements from iterable of length n, except the last one that has the
    required length to exaust iterable (i.e., there is no filling applied).

    :param n: length of each tuple (except the last one,that will have length
       <= n
    :param iterable: the iterable to divide in groups
    """
    import itertools

    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def gzip_string(string):
    """
    Gzip string contents.

    :param string: a string
    :return: a gzipped string
    """
    import tempfile, gzip

    with tempfile.NamedTemporaryFile() as f:
        g = gzip.open(f.name, 'wb')
        g.write(string)
        g.close()
        return f.read()


def gunzip_string(string):
    """
    Gunzip string contents.

    :param string: a gzipped string
    :return: a string
    """
    import tempfile, gzip

    with tempfile.NamedTemporaryFile() as f:
        f.write(string)
        f.flush()
        g = gzip.open(f.name, 'rb')
        return g.read()


def xyz_parser_iterator(string):
    """
    Yields a tuple `(natoms, comment, atomiter)`for each frame
    in a XYZ file where `atomiter` is an iterator yielding a
    nested tuple `(symbol, (x, y, z))` for each entry.

    :param string: a string containing XYZ-structured text
    """

    class BlockIterator(object):
        """
        An iterator for wrapping the iterator returned by `match.finditer`
        to extract the required fields directly from the match object
        """

        def __init__(self, it, natoms):
            self._it = it
            self._natoms = natoms
            self._catom = 0

        def __iter__(self):
            return self

        def __next__(self):
            try:
                match = self._it.next()
            except StopIteration:
                # if we reached the number of atoms declared, everything is well
                # and we re-raise the StopIteration exception
                if self._catom == self._natoms:
                    raise
                else:
                    # otherwise we got too less entries
                    raise TypeError("Number of atom entries ({}) is smaller "
                                    "than the number of atoms ({})".format(
                        self._catom, self._natoms))

            self._catom += 1

            if self._catom > self._natoms:
                raise TypeError("Number of atom entries ({}) is larger "
                                "than the number of atoms ({})".format(
                    self._catom, self._natoms))

            return (
                match.group('sym'),
                (
                    float(match.group('x')),
                    float(match.group('y')),
                    float(match.group('z'))
                ))

        def next(self):
            """
            The iterator method expected by python 2.x,
            implemented as python 3.x style method.
            """
            return self.__next__()

    import re

    pos_regex = re.compile(r"""
^                                                                             # Linestart
[ \t]*                                                                        # Optional white space
(?P<sym>[A-Za-z]+[A-Za-z0-9]*)\s+                                             # get the symbol
(?P<x> [\+\-]?  ( \d*[\.]\d+  | \d+[\.]?\d* )  ([Ee][\+\-]?\d+)? ) [ \t]+     # Get x
(?P<y> [\+\-]?  ( \d*[\.]\d+  | \d+[\.]?\d* )  ([Ee][\+\-]?\d+)? ) [ \t]+     # Get y
(?P<z> [\+\-]?  ( \d*[\.]\d+  | \d+[\.]?\d* )  ([Ee][\+\-]?\d+)? )            # Get z
""", re.X | re.M)
    pos_block_regex = re.compile(r"""
                                                            # First line contains an integer
                                                            # and only an integer: the number of atoms
^[ \t]* (?P<natoms> [0-9]+) [ \t]*[\n]                      # End first line
(?P<comment>.*) [\n]                                        # The second line is a comment
(?P<positions>                                              # This is the block of positions
    (
        (
            \s*                                             # White space in front of the element spec is ok
            (
                [A-Za-z]+[A-Za-z0-9]*                       # Element spec
                (
                    \s+                                     # White space in front of the number
                    [\+\-]?                                 # Plus or minus in front of the number (optional)
                    (
                        (
                            \d*                             # optional decimal in the beginning .0001 is ok, for example
                            [\.]                            # There has to be a dot followed by
                            \d+                             # at least one decimal
                        )
                        |                                   # OR
                        (
                            \d+                             # at least one decimal, followed by
                            [\.]?                           # an optional dot
                            \d*                             # followed by optional decimals
                        )
                    )
                    ([Ee][\+\-]?\d+)?                       # optional exponents E+03, e-05
                ){3}                                        # I expect three float values
                |
                \#                                          # If a line is commented out, that is also ok
            )
            .*                                              # I do not care what is after the comment or the position spec
            |                                               # OR
            \s*                                             # A line only containing white space
         )
        [\n]                                                # line break at the end
    )+
)                                                           # A positions block should be one or more lines
                    """, re.X | re.M)

    for block in pos_block_regex.finditer(string):
        natoms = int(block.group('natoms'))
        yield (
            natoms,
            block.group('comment'),
            BlockIterator(
                pos_regex.finditer(block.group('positions')),
                natoms)
        )


class EmptyContextManager(object):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def get_extremas_from_positions(positions):
    """
    returns the minimum and maximum value for each dimension in the positions given
    """
    return zip(*[(min(values), max(values)) for values in zip(*positions)])


def get_fortfloat(key, txt, be_case_sensitive=True):
    """
    Matches a fortran compatible specification of a float behind a defined key in a string.
    :param key: The key to look for
    :param txt: The string where to search for the key
    :param be_case_sensitive: An optional boolean whether to search case-sensitive, defaults to ``True``

    If abc is a key, and f is a float, number, than this regex
    will match t and return f in the following cases:

    *   charsbefore, abc = f, charsafter
    *   charsbefore
        abc = f
        charsafter
    *   charsbefore, abc = f
        charsafter

    and vice-versa.
    If no float is matched, returns None

    Exampes of matchable floats are:

    *   0.1d2
    *   0.D-3
    *   .2e1
    *   -0.23
    *   23.
    *   232
    """
    import re
    pattern = """
        [\n,]                       # key - value pair can be prepended by comma or start
        [ \t]*                      # in a new line and some optional white space
        {}                          # the key goes here
        [ \t]*                      # Optional white space between key and equal sign
        =                           # Equals, you can put [=:,] if you want more specifiers
        [ \t]*                      # optional white space between specifier and float
        (?P<float>                  # Universal float pattern
            ( \d*[\.]\d+  |  \d+[\.]?\d* )
            ([ E | D | e | d ] [+|-]? \d+)?
        )
        [ \t]*[,\n,#]               # Can be followed by comma, end of line, or a comment
        """.format(key)
    REKEYS = re.X | re.M if be_case_sensitive else re.X | re.M | re.I
    match = re.search(
        pattern,
        txt,
        REKEYS)
    if not match:
        return None
    else:
        return float(match.group('float').replace('d', 'e').replace('D', 'e'))


def ask_question(question, reply_type, allow_none_as_answer):
    """
    This method asks a specific question, tries to parse the given reply
    and then it verifies the parsed answer.
    :param question: The question to be asked.
    :param reply_type: The type of the expected answer (int, datetime etc). It
    is needed for the parsing of the answer.
    :param allow_none_as_answer: Allow empty answers?
    :return: The parsed reply.
    """
    final_answer = None

    while True:
        answer = query_string(question, "")

        # If the reply is empty
        if not answer:
            if not allow_none_as_answer:
                continue
        # Otherwise, try to parse it
        else:
            try:
                if reply_type == int:
                    final_answer = int(answer)
                elif reply_type == float:
                    final_answer = float(answer)
                elif reply_type == datetime.datetime:
                    final_answer = parse(answer)
                else:
                    raise ValueError
            # If it is not parsable...
            except ValueError:
                sys.stdout.write("The given value could not be parsed. " +
                                 "Type expected: {}\n".format(reply_type))
                # If the timestamp could not have been parsed,
                # ask again the same question.
                continue

        if query_yes_no("{} was parsed. Is it correct?"
                                .format(final_answer), default="yes"):
            break
    return final_answer


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning
    an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = raw_input(question + prompt).lower()
        if default is not None and not choice:
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def query_string(question, default):
    """
    Asks a question (with the option to have a default, predefined answer,
    and depending on the default answer and the answer of the user the
    following options are available:
    - If the user replies (with a non empty answer), then his answer is
    returned.
    - If the default answer is None then the user has to reply with a non-empty
    answer.
    - If the default answer is not None, then it is returned if the user gives
    an empty answer. In the case of empty default answer and empty reply from
    the user, None is returned.
    :param question: The question that we want to ask the user.
    :param default: The default answer (if there is any) to the question asked.
    :return: The returned reply.
    """

    if default is None or not default:
        prompt = ""
    else:
        prompt = " [{}]".format(default)

    while True:
        reply = raw_input(question + prompt)
        if default is not None and not reply:
            # If the default answer is an empty string.
            if not default:
                return None
            else:
                return default
        elif reply:
            return reply
        else:
            sys.stdout.write("Please provide a non empty answer.\n")


def flatten_list(value):
    """
    Flattens a list or a tuple
    In [2]: flatten_list([[[[[4],3]],[3],['a',[3]]]])
    Out[2]: [4, 3, 3, 'a', 3]

    :param value: A value, whether iterable or not
    :returns: a list of nesting level 1
    """

    if isinstance(value, (list, tuple)):
        return_list = []
        [[return_list.append(i) for i in flatten_list(item)] for item in value]
        return return_list
    return [value]


class combomethod(object):
    """
    A decorator that wraps a function that can be both a classmethod or
    instancemethod and behaves accordingly::

        class A():

            @combomethod
            def do(self, **kwargs):
                isclass = kwargs.get('isclass')
                if isclass:
                    print "I am a class", self
                else:
                    print "I am an instance", self

        A.do()
        A().do()

        >>> I am a class __main__.A
        >>> I am an instance <__main__.A instance at 0x7f2efb116e60>

    Attention: For ease of handling, pass keyword **isclass**
    equal to True if this was called as a classmethod and False if this
    was called as an instance.
    The argument self is therefore ambiguous!
    """

    def __init__(self, method):
        self.method = method

    def __get__(self, obj=None, objtype=None):
        @functools.wraps(self.method)
        def _wrapper(*args, **kwargs):
            kwargs.pop('isclass', None)
            if obj is not None:
                return self.method(obj, *args, isclass=False, **kwargs)
            return self.method(objtype, *args, isclass=True, **kwargs)

        return _wrapper


class ArrayCounter(object):
    """
    A counter & a method that increments it and returns its value.
    It is used in various tests.
    """
    seq = None

    def __init__(self):
        self.seq = -1

    def array_counter(self):
        self.seq += 1
        return self.seq


def are_dir_trees_equal(dir1, dir2):
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
    """
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or
                len(dirs_cmp.funny_files) > 0):
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


def indent(txt, spaces=4):
    return "\n".join(" " * spaces + ln for ln in txt.splitlines())


def issingular(singularForm):
    """
    Checks whether a noun is singular
    :param pluralForm: a string defining an English noun
    :return: the t-ple (singular, pluralform).
    singular: True/Flalse if noun is singular/plural
    pluralfrom: (a string with the noun in the plural form))
    """

    from pattern.en import pluralize

    pluralForm = pluralize(singularForm)
    singular = True if singularForm is not pluralForm else False
    return singular, pluralForm


class Prettifier(object):
    """
    Class to manage prettifiers (typically for labels of kpoints
    in band plots)
    """

    @classmethod
    def _prettify_label_pass(cls,label):
        """
        No-op prettifier, simply returns  the same label

        :param label: a string to prettify
        """
        return label

    @classmethod
    def _prettify_label_agr(cls,label):
        """
        Prettifier for XMGrace

        :param label: a string to prettify
        """
        import re
        newlabel = label

        newlabel = newlabel.replace('GAMMA', r'\xG\f{}')
        newlabel = newlabel.replace('DELTA', r'\xD\f{}')
        newlabel = newlabel.replace('LAMBDA', r'\xL\f{}')
        newlabel = newlabel.replace('SIGMA', r'\xS\f{}')
        newlabel = re.sub('_(.{0,1})', r'\\s\1\\N', newlabel)

        return newlabel

    @classmethod
    def _prettify_label_agr_simple(cls,label):
        """
        Prettifier for XMGrace (for old label names)

        :param label: a string to prettify
        """
        import re

        newlabel = label

        newlabel = re.sub('([0-9])', r'\\s\1\\N', newlabel)

        if newlabel == 'G':
            return r'\xG'
        else:
            return newlabel

    @classmethod
    def _prettify_label_gnuplot(cls,label):
        """
        Prettifier for Gnuplot

        :note: uses unicode, returns unicode strings (potentially, if needed)

        :param label: a string to prettify
        """
        import re
        newlabel = label

        newlabel = newlabel.replace(u'GAMMA', u'Γ')
        newlabel = newlabel.replace(u'DELTA', u'Δ')
        newlabel = newlabel.replace(u'LAMBDA', u'Λ')
        newlabel = newlabel.replace(u'SIGMA', u'Σ')
        newlabel = re.sub(u'_(.{0,1})', ur'_{\1}', newlabel)

        return newlabel

    @classmethod
    def _prettify_label_gnuplot_simple(cls,label):
        """
        Prettifier for Gnuplot (for old label names)

        :note: uses unicode, returns unicode strings (potentially, if needed)

        :param label: a string to prettify
        """
        import re

        newlabel = label

        newlabel = re.sub(u'([0-9])', ur'_{\1}', newlabel)

        if newlabel == 'G':
            return u'Γ'
        else:
            return newlabel


    @classmethod
    def _prettify_label_latex(cls,label):
        """
        Prettifier for matplotlib, using LaTeX syntax

        :param label: a string to prettify
        """
        import re
        newlabel = label

        newlabel = newlabel.replace('GAMMA', r'$\Gamma$')
        newlabel = newlabel.replace('DELTA', r'$\Delta$')
        newlabel = newlabel.replace('LAMBDA', r'$\Lambda$')
        newlabel = newlabel.replace('SIGMA', r'$\Sigma$')
        newlabel = re.sub('_(.{0,1})', r'$_{\1}$', newlabel)

        #newlabel = newlabel + r"$_{\vphantom{0}}$"

        return newlabel

    @classmethod
    def _prettify_label_latex_simple(cls,label):
        """
        Prettifier for matplotlib, using LaTeX syntax (for old label names)

        :param label: a string to prettify
        """
        import re

        newlabel = label
        newlabel = re.sub('([0-9])', r'$_{\1}$', newlabel)

        if newlabel == 'G':
            return r'$\Gamma$'
        else:
            return newlabel

    @classproperty
    def prettifiers(cls):
        """
        Property that returns a dictionary that for each string associates
        the function to prettify a label

        :return: a dictionary where keys are strings and values are functions
        """
        return {
        'agr_seekpath': cls._prettify_label_agr,
        'agr_simple': cls._prettify_label_agr_simple,
        'latex_simple': cls._prettify_label_latex_simple,
        'latex_seekpath': cls._prettify_label_latex,
        'gnuplot_simple': cls._prettify_label_gnuplot_simple,
        'gnuplot_seekpath': cls._prettify_label_gnuplot,
        'pass': cls._prettify_label_pass,
    }

    @classmethod
    def get_prettifiers(cls):
        """
        Return a list of valid prettifier strings

        :return: a list of strings
        """
        return sorted(cls.prettifiers.keys())

    def __init__(self, format):
        """
        Create a class to pretttify strings of a given format

        :param format: a string with the format to use to prettify.
           Valid formats are obtained from self.prettifiers
        """
        if format is None:
            format = 'pass'
        try:
            self._prettifier_f = self.prettifiers[format]
        except KeyError:
            raise ValueError("Unknown prettifier format {}; "
                             "valid formats: {}".format(
                format,
                ", ".join(self.get_prettifiers())
                ))

    def prettify(self, label):
        """
        Prettify a label using the format passed in the initializer

        :param label: the string to prettify
        :return: a prettified string
        """
        return self._prettifier_f(label)


def prettify_labels(labels, format=None):
    """
    Prettify label for typesetting in various formats

    :param labels: a list of length-2 tuples, in the format(position, label)
    :param format: a string with the format for the prettifier (e.g. 'agr',
         'matplotlib', ...)
    :return: the same list as labels, but with the second value possibly replaced
         with a prettified version that typesets nicely in the selected format
    """
    prettifier = Prettifier(format)

    retlist = []
    for label_pos, label in labels:
        retlist.append((label_pos, prettifier.prettify(label)))
    return retlist


def join_labels(labels, join_symbol="|", threshold=1.e-6):
    """
    Join labels with a joining symbol when they are very close

    :param labels: a list of length-2 tuples, in the format(position, label)
    :param join_symbol: the string to use to join different paths. By default, a pipe
    :param threshold: the threshold to decide if two float values are the same and should
         be joined
    :return: the same list as labels, but with the second value possibly replaced
         with strings joined when close enough
    """
    if labels:
        new_labels = [list(labels[0])]
        # modify labels when in overlapping position
        j = 0
        for i in range(1, len(labels)):
            if abs(labels[i][0] - labels[i - 1][0]) < threshold:
                new_labels[j][1] += join_symbol + labels[i][1]
            else:
                new_labels.append(list(labels[i]))
                j += 1
    else:
        new_labels = []

    return new_labels
