from aiida import work


def create_test_runner():
    runner = work.Runner(
        poll_interval=0., rmq_config=None, enable_persistence=False
    )
    work.set_runner(runner)
    return runner
