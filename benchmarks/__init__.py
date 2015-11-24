# -*- coding: utf-8 -*-

"""
Regroup the benchmarks to run. Currently, we have four of them:
    * `verdi data structure list -G ...`. List the datastructure from a list of
    groups, and get the attributes `kinds` and `sites`, all of that ordered by
    time.
    * Three queries about attributes. The way it is described in the README, it
    first get a list of nodes from the group, and then the attributes whoses
    key starts with: `kinds`, `sites`, `cell`.
    * get_closest_cif(nodes): get the closest parents for all the  nodes which is a
    CifData node. The way it is done in the function:
        - it first get from the DbPath table (and with joins) the depth of the
        closest parent which contains the requested type.
        - it then query all the parent at this depth
        - and then get all the CifData node with a children in the list of the
        requested node and who are a parent (<- not sure about this)
    * get_farthest_struc(node): built in a similar way as get_closest_cif, but
    with structure instead, and getting the farthest.

The two last query could probably be optimized, and they don't include
benchmarking JSON, so we will leave them for later.
"""



# Various queries to test. The first one is about querying attributes.
# There is different ways to achieve it.
# With JSON columns, it is quite straightforward. You simply obtain all the
# nodes.
# For the seperate table case, you can either do it with a JOIN, or with a
# separated query. A variante of the last one is implemented in AiiDA for
# retrieving the data structure nodes and their attributes, which is doing it
# by batch of 100. That is, one query for the node, then for each group of 100
# nodes, you get their attributes.
# With separate columns, we also need to take into account the deserialisation
# time. We should take care of computing this time.
# Finally, we should also time (using \timing) the SQL request themselves, and
# see how much overhead we have from both Django & SqlAlchemy.
#
# Once each of those query can easily be benchmarked (with protocol and such),
# we should also try to benchmark the effect of some PostgreSQL parameters on
# those query.

import argparse
import time

from collections import namedtuple

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
    size = len(res)

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

    parser.add_argument('-r', '--reboot', dest='reboot', action='store_true',
                        default=False, help='reboot the database between queries')

    parser.add_argument('-n', dest='times', default=10, type=int,
                        help='number of times to run each query')

    parser.add_argument('--gin-index', dest='gin_index', default=False,
                        action='store_true', help="add a gin index to attributes")
    parser.add_argument('--delete-gin-index', dest='delete_gin_index', default=False,
                        action='store_true', help="delete the gin index if existing")

    args = parser.parse_args()

    if args.backend != "sqlalchemy" and (args.gin_index or args.delete_gin_index):
        raise parser.error("You can't use a GIN index with Django.")

    load_profile(profile=profiles[args.backend])

    from aiida.backends.utils import load_dbenv
    load_dbenv()

    if args.backend == "django":
        from dj import queries
    else:
        from sqla import queries, create_gin_index, delete_gin_index
        from aiida.backends import sqlalchemy as sa

    if args.delete_gin_index:
        print('Deleting GIN index on attributes..')
        delete_gin_index()
    if args.gin_index:
        print('Recreating GIN index on attributes..')
        create_gin_index()


    for key, q in queries.iteritems():
        print('Running queries "{}":'.format(key))
        for name, query in q.iteritems():
            print('  Query "{}":'.format(name))
            res = time_it(query, n=args.times)
            print(res)


