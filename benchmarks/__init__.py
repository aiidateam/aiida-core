# -*- coding: utf-8 -*-

import argparse
import time
import sys

from collections import namedtuple

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

class Result(namedtuple("Result", "length first_run mean mean_minus_first")):
    __slots__ = ()

    def __new__(cls, length, first_run, mean=None, mean_minus_first=None):
        return super(cls, Result).__new__(cls, length, first_run, mean,
                                          mean_minus_first)

    def __str__(self):
        s = ("  - Length: {length}\n"
             "  - First: {first}")
        if self.mean:
            s += "\n  - Mean: {mean}"
        if self.mean_minus_first:
            s += "\n  - Mean minus first: {mean_minus_first}"

        return s.format(length=self.length, first=self.first_run,
                        mean=self.mean, mean_minus_first=self.mean_minus_first)

from aiida.backends.profile import load_profile

profiles = {
    "django": "default",
    "sqlalchemy": "sqla"
}

def time_it(f, n=10):
    """
    Time the call of the function f, running it n times.

    It returns the time of the first run, the mean of all the run, and the mean
    of all the run but the first one. In the case of database timing, some
    caching might happens.
    If it was asked to be only run once, only the time of the run is returned.
    """

    if n < 1:
        raise ValueError("I think we need to run it at least once..")
    times = []
    for _ in xrange(n):
        start = time.time()
        res = f()
        end = time.time()
        times.append(end - start)
    try:
        size = len(res)
    except TypeError:
        size = 1


    ret = {
        "length": size,
        "first_run": times[0],
    }

    if n > 1:
        ret["mean"] = sum(times)/len(times)
        ret["mean_minus_first"] = sum(times[1:])/len(times[1:])

    return Result(**ret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AiiDA benchmarks")

    parser.add_argument('-b', '--backend', dest='backend',
                        choices=["sqlalchemy", "django"],
                        required=True,
                        help="backend to use")
    parser.add_argument('-p', '--profile', dest='profile',
                        help="specify a profile to use")

    parser.add_argument('-r', '--reboot', dest='reboot', action='store_true',
                        default=False, help='reboot the database between queries')

    parser.add_argument('-n', dest='times', default=10, type=int,
                        help='number of times to run each query')

    parser.add_argument('--gin-index', dest='gin_index', default=False,
                        action='store_true', help="add a gin index to attributes")
    parser.add_argument('--delete-gin-index', dest='delete_gin_index', default=False,
                        action='store_true', help="delete the gin index if existing")

    parser.add_argument('--json', dest="json", default=None,
                        help=("json function to use between "
                              "ujson (no date) and json (Python module)"),
                        choices=["ujson", "json"])

    parser.add_argument('-g', '--group', dest='group',
                        help="group of queries to run")
    parser.add_argument('-q', '--query', dest='query',
                        help="specify the query to run")
    parser.add_argument('--bprofile', dest='bprofile',
                        help="store the bprofile output into the specified file")

    args = parser.parse_args()

    if args.backend != "sqlalchemy" and (args.gin_index or args.delete_gin_index):
        raise parser.error("You can't use a GIN index with Django.")

    if args.bprofile:
        from bprofile import BProfile
        profiler = lambda: BProfile(args.bprofile)
    else:
        from contextlib import contextmanager
        # noop context manager
        profiler = contextmanager(lambda: (yield))

    profile = args.profile or profiles[args.backend]
    load_profile(profile=profile)

    from aiida.backends.utils import load_dbenv
    load_dbenv()

    # XXX remove this and use the profile to decide which backend to use
    if args.backend == "django":
        from dj import queries
    else:
        from sqla import queries, create_gin_index, delete_gin_index
        from aiida.backends import sqlalchemy

    if args.delete_gin_index:
        print('Deleting GIN index on attributes..')
        delete_gin_index()
    if args.gin_index:
        print('Recreating GIN index on attributes..')
        create_gin_index()

    if args.json and args.backend != "sqlalchemy":
        print("Specifying the JSON functions to use is only available for SqlAlchemy")

    if args.json == "ujson":
        try:
            import ultrajson
            sqlalchemy.session.bind.dialect._json_serializer = ultrajson.dumps
            sqlalchemy.session.bind.dialect._json_deserializer = ultrajson.loads
        except ImportError:
            print("ultrajson doesn't seem to be installed..")
            sys.exit(-1)
    elif args.json == "json":
        import json
        sqlalchemy.session.bind.dialect._json_serializer = json.dumps
        sqlalchemy.session.bind.dialect._json_deserializer = json.loads


    print('Start of benchmarking..')
    for key, q in queries.iteritems():
        if args.group and args.group != key:
            continue
        print('Running queries "{}":'.format(key))
        for name, query in q.iteritems():
            if args.query and args.query != name:
                continue
            print('  Query "{}":'.format(name))
            with profiler():
                res = time_it(query, n=args.times)
            print(res)


