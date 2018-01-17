from aiida import work


def create_test_runner():
    runner = work.new_runner(poll_interval=0., enable_persistence=False)
    work.set_runner(runner)
    return runner
