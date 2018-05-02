# -*- coding: utf-8 -*-
import uuid
from aiida import work


def create_test_runner(with_communicator=False):
    prefix = 'aiidatest-{}'.format(uuid.uuid4())
    if with_communicator:
        rmq_config = work.rmq.get_rmq_config(prefix)
    else:
        rmq_config = None
    runner = work.Runner(
        poll_interval=0.,
        rmq_config=rmq_config,
        enable_persistence=False
    )
    work.set_runner(runner)
    return runner
