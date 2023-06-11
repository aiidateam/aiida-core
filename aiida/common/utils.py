# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Miscellaneous generic utility functions and classes."""
from datetime import datetime
import filecmp
import inspect
import io
import os
import re
import sys
from typing import Any, Dict
from uuid import UUID

from .lang import classproperty


def get_new_uuid():
    """
    Return a new UUID (typically to be used for new nodes).
    """
    import uuid
    return str(uuid.uuid4())


def validate_uuid(given_uuid: str) -> bool:
    """A simple check for the UUID validity."""
    try:
        parsed_uuid = UUID(given_uuid, version=4)
    except ValueError:
        # If not a valid UUID
        return False

    # Check if there was any kind of conversion of the hex during
    # the validation
    return str(parsed_uuid) == given_uuid


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

    err_msg = (
        'the value must be a list (or tuple) '
        'of length-N list (or tuples), whose elements are strings; '
        'N={}'.format(tuple_length)
    )

    if not isinstance(val, (list, tuple)):
        raise ValidationError(err_msg)

    for element in val:
        if (
            not isinstance(element, (list, tuple)) or (len(element) != tuple_length) or
            not all(isinstance(s, str) for s in element)
        ):
            raise ValidationError(err_msg)

    return True


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
        new_filename = f'{basename:s}-{append_int:d}{ext:s}'
        if new_filename not in list_of_filenames:
            break
        append_int += 1
    return new_filename


def str_timedelta(dt, max_num_fields=3, short=False, negative_to_zero=False):  # pylint: disable=invalid-name
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
        raise ValueError('max_num_fields must be > 0')

    s_tot = dt.total_seconds()  # Important to get more than 1 day, and for
    # negative values. dt.seconds would give
    # wrong results in these cases, see
    # http://docs.python.org/2/library/datetime.html
    s_tot = int(s_tot)

    if negative_to_zero:
        s_tot = max(s_tot, 0)

    negative = s_tot < 0
    s_tot = abs(s_tot)

    negative_string = ' in the future' if negative else ' ago'

    # For the moment stay away from months and years, difficult to get
    days, remainder = divmod(s_tot, 3600 * 24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    all_fields = [(days, 'D'), (hours, 'h'), (minutes, 'm'), (seconds, 's')]
    fields = []
    start_insert = False
    counter = 0
    for idx, field in enumerate(all_fields):
        if field[0] != 0:
            start_insert = True
        if (len(all_fields) - idx) <= max_num_fields:
            start_insert = True
        if start_insert:
            if counter >= max_num_fields:
                break
            fields.append(field)
            counter += 1

    if short:
        while len(fields) > 1:  # at least one element has to remain
            if fields[0][0] != 0:
                break
            fields.pop(0)  # remove first element

    # Join the fields
    raw_string = ':'.join(['{:02d}{}'.format(*f) for f in fields])

    if raw_string.startswith('0'):
        raw_string = raw_string[1:]

    # Return the resulting string, appending a suitable string if the time
    # is negative
    return f'{raw_string}{negative_string}'


def get_class_string(obj):
    """
    Return the string identifying the class of the object (module + object name,
    joined by dots).

    It works both for classes and for class instances.
    """
    if inspect.isclass(obj):
        return f'{obj.__module__}.{obj.__name__}'

    return f'{obj.__module__}.{obj.__class__.__name__}'


def get_object_from_string(class_string):
    """
    Given a string identifying an object (as returned by the get_class_string
    method) load and return the actual object.
    """
    import importlib

    the_module, _, the_name = class_string.rpartition('.')

    return getattr(importlib.import_module(the_module), the_name)


def grouper(n, iterable):  # pylint: disable=invalid-name
    """
    Given an iterable, returns an iterable that returns tuples of groups of
    elements from iterable of length n, except the last one that has the
    required length to exaust iterable (i.e., there is no filling applied).

    :param n: length of each tuple (except the last one,that will have length
       <= n
    :param iterable: the iterable to divide in groups
    """
    import itertools

    iterator = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(iterator, n))
        if not chunk:
            return
        yield chunk


class ArrayCounter:
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

    # Directory comparison
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if dirs_cmp.left_only or dirs_cmp.right_only or dirs_cmp.funny_files:
        return (
            False, 'Left directory: {}, right directory: {}, files only '
            'in left directory: {}, files only in right directory: '
            '{}, not comparable files: {}'.format(
                dir1, dir2, dirs_cmp.left_only, dirs_cmp.right_only, dirs_cmp.funny_files
            )
        )

    # If the directories contain the same files, compare the common files
    (_, mismatch, errors) = filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files, shallow=False)
    if mismatch:
        return (False, f"The following files in the directories {dir1} and {dir2} don't match: {mismatch}")
    if errors:
        return (False, f"The following files in the directories {dir1} and {dir2} aren't regular: {errors}")

    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        res, msg = are_dir_trees_equal(new_dir1, new_dir2)
        if not res:
            return False, msg

    return True, f'The given directories ({dir1} and {dir2}) are equal'


class Prettifier:
    """
    Class to manage prettifiers (typically for labels of kpoints
    in band plots)
    """

    @classmethod
    def _prettify_label_pass(cls, label):
        """
        No-op prettifier, simply returns  the same label

        :param label: a string to prettify
        """
        return label

    @classmethod
    def _prettify_label_agr(cls, label):
        """
        Prettifier for XMGrace

        :param label: a string to prettify
        """

        label = (
            label
                .replace('GAMMA', r'\xG\f{}')
                .replace('DELTA', r'\xD\f{}')
                .replace('LAMBDA', r'\xL\f{}')
                .replace('SIGMA', r'\xS\f{}')
        )  # yapf:disable
        return re.sub(r'_(.?)', r'\\s\1\\N', label)

    @classmethod
    def _prettify_label_agr_simple(cls, label):
        """
        Prettifier for XMGrace (for old label names)

        :param label: a string to prettify
        """

        if label == 'G':
            return r'\xG'

        return re.sub(r'(\d+)', r'\\s\1\\N', label)

    @classmethod
    def _prettify_label_gnuplot(cls, label):
        """
        Prettifier for Gnuplot

        :note: uses unicode, returns unicode strings (potentially, if needed)

        :param label: a string to prettify
        """

        label = (
            label
                .replace('GAMMA', 'Γ')
                .replace('DELTA', 'Δ')
                .replace('LAMBDA', 'Λ')
                .replace('SIGMA', 'Σ')
        )  # yapf:disable
        return re.sub(r'_(.?)', r'_{\1}', label)

    @classmethod
    def _prettify_label_gnuplot_simple(cls, label):
        """
        Prettifier for Gnuplot (for old label names)

        :note: uses unicode, returns unicode strings (potentially, if needed)

        :param label: a string to prettify
        """

        if label == 'G':
            return 'Γ'

        return re.sub(r'(\d+)', r'_{\1}', label)

    @classmethod
    def _prettify_label_latex(cls, label):
        """
        Prettifier for matplotlib, using LaTeX syntax

        :param label: a string to prettify
        """

        label = (
            label
                .replace('GAMMA', r'$\Gamma$')
                .replace('DELTA', r'$\Delta$')
                .replace('LAMBDA', r'$\Lambda$')
                .replace('SIGMA', r'$\Sigma$')
        )  # yapf:disable
        label = re.sub(r'_(.?)', r'$_{\1}$', label)

        # label += r"$_{\vphantom{0}}$"

        return label

    @classmethod
    def _prettify_label_latex_simple(cls, label):
        """
        Prettifier for matplotlib, using LaTeX syntax (for old label names)

        :param label: a string to prettify
        """
        if label == 'G':
            return r'$\Gamma$'

        return re.sub(r'(\d+)', r'$_{\1}$', label)

    @classproperty
    def prettifiers(cls) -> Dict[str, Any]:  # pylint: disable=no-self-argument
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

    def __init__(self, format):  # pylint: disable=redefined-builtin
        """
        Create a class to pretttify strings of a given format

        :param format: a string with the format to use to prettify.
           Valid formats are obtained from self.prettifiers
        """
        if format is None:
            format = 'pass'

        try:
            self._prettifier_f = self.prettifiers[format]  # pylint: disable=unsubscriptable-object
        except KeyError:
            raise ValueError(f"Unknown prettifier format {format}; valid formats: {', '.join(self.get_prettifiers())}")

    def prettify(self, label):
        """
        Prettify a label using the format passed in the initializer

        :param label: the string to prettify
        :return: a prettified string
        """
        return self._prettifier_f(label)


def prettify_labels(labels, format=None):  # pylint: disable=redefined-builtin
    """
    Prettify label for typesetting in various formats

    :param labels: a list of length-2 tuples, in the format(position, label)
    :param format: a string with the format for the prettifier (e.g. 'agr',
         'matplotlib', ...)
    :return: the same list as labels, but with the second value possibly replaced
         with a prettified version that typesets nicely in the selected format
    """
    prettifier = Prettifier(format)

    return [(pos, prettifier.prettify(label)) for pos, label in labels]


def join_labels(labels, join_symbol='|', threshold=1.e-6):
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


def strip_prefix(full_string, prefix):
    """
    Strip the prefix from the given string and return it. If the prefix is not present
    the original string will be returned unaltered

    :param full_string: the string from which to remove the prefix
    :param prefix: the prefix to remove
    :return: the string with prefix removed
    """
    if full_string.startswith(prefix):
        return full_string.rsplit(prefix)[1]

    return full_string


class Capturing:
    """
    This class captures stdout and returns it
    (as a list, split by lines).

    Note: if you raise a SystemExit, you have to catch it outside.
    E.g., in our tests, this works::

        import sys
        with self.assertRaises(SystemExit):
            with Capturing() as output:
                sys.exit()

    But out of the testing environment, the code instead just exits.

    To use it, access the obj.stdout_lines, or just iterate over the object

    :param capture_stderr: if True, also captures sys.stderr. To access the
        lines, use obj.stderr_lines. If False, obj.stderr_lines is None.
    """

    # pylint: disable=attribute-defined-outside-init

    def __init__(self, capture_stderr=False):
        """Construct a new instance."""
        self.stdout_lines = []
        super().__init__()

        self._capture_stderr = capture_stderr
        if self._capture_stderr:
            self.stderr_lines = []
        else:
            self.stderr_lines = None

    def __enter__(self):
        """Enter the context where all output is captured."""
        self._stdout = sys.stdout
        self._stringioout = io.StringIO()
        sys.stdout = self._stringioout
        if self._capture_stderr:
            self._stderr = sys.stderr
            self._stringioerr = io.StringIO()
            sys.stderr = self._stringioerr
        return self

    def __exit__(self, *args):
        """Exit the context where all output is captured."""
        self.stdout_lines.extend(self._stringioout.getvalue().splitlines())
        sys.stdout = self._stdout
        del self._stringioout  # free up some memory
        if self._capture_stderr:
            self.stderr_lines.extend(self._stringioerr.getvalue().splitlines())
            sys.stderr = self._stderr
            del self._stringioerr  # free up some memory

    def __str__(self):
        return str(self.stdout_lines)

    def __iter__(self):
        return iter(self.stdout_lines)


class ErrorAccumulator:
    """
    Allows to run a number of functions and collect all the errors they raise

    This allows to validate multiple things and tell the user about all the
    errors encountered at once. Works best if the individual functions do not depend on each other.

    Does not allow to trace the stack of each error, therefore do not use for debugging, but for
    semantical checking with user friendly error messages.
    """

    def __init__(self, *error_cls):
        self.error_cls = error_cls
        self.errors = {k: [] for k in self.error_cls}

    def run(self, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except self.error_cls as err:
            self.errors[err.__class__].append(err)

    def success(self):
        return bool(not any(self.errors.values()))

    def result(self, raise_error=Exception):
        if raise_error:
            self.raise_errors(raise_error)
        return self.success(), self.errors

    def raise_errors(self, raise_cls):
        if not self.success():
            raise raise_cls(f'The following errors were encountered: {self.errors}')


class DatetimePrecision:
    """
    A simple class which stores a datetime object with its precision. No
    internal check is done (cause itis not possible).

    precision:  1 (only full date)
                2 (date plus hour)
                3 (date + hour + minute)
                4 (dare + hour + minute +second)
    """

    def __init__(self, dtobj, precision):
        """ Constructor to check valid datetime object and precision """

        if not isinstance(dtobj, datetime):
            raise TypeError('dtobj argument has to be a datetime object')

        if not isinstance(precision, int):
            raise TypeError('precision argument has to be an integer')

        self.dtobj = dtobj
        self.precision = precision
