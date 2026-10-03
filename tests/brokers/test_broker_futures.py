###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from kiwipy.                          #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The kiwipy license is reproduced in open_source_licenses.txt.          #
###########################################################################
"""Tests for :mod:`aiida.brokers.futures`."""

from aiida.brokers import futures as broker_futures


def test_capture_exceptions():
    """Exceptions raised in the context are set on the future."""
    future = broker_futures.Future()

    exception = RuntimeError()
    with broker_futures.capture_exceptions(future):
        raise exception

    assert future.exception() is exception


def test_capture_exceptions_ignore():
    """Exceptions listed in ``ignore`` are re-raised instead of captured."""
    future = broker_futures.Future()

    try:
        with broker_futures.capture_exceptions(future, ignore=(ValueError,)):
            raise ValueError('ignored')
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError to be re-raised')

    assert not future.done()


def test_copy_future():
    """The result of the source future is copied to the target."""
    source = broker_futures.Future()
    target = broker_futures.Future()
    source.set_result(42)
    broker_futures.copy_future(source, target)
    assert target.result(timeout=5) == 42

    source = broker_futures.Future()
    target = broker_futures.Future()
    broker_futures.chain(source, target)
    source.set_result(42)
    assert target.result(timeout=5) == 42


def test_chain_exception():
    """Exceptions propagate through chained futures."""
    source = broker_futures.Future()
    target = broker_futures.Future()
    broker_futures.chain(source, target)
    source.set_exception(RuntimeError('oops'))
    try:
        target.result(timeout=5)
    except RuntimeError as exception:
        assert str(exception) == 'oops'
    else:
        raise AssertionError('expected RuntimeError to propagate')
