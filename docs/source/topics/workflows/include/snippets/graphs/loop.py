from aiida.engine import graph, loop, run, task


@task(outputs=['value', 'keep_going'])
def step_down(value: int) -> tuple[int, bool]:
    return value - 1, value - 1 > 0


@graph
def count_down(start):
    with loop(condition='keep_going', value=start) as counting:
        stepped = step_down(value=counting.value)
        counting.returns(value=stepped.value, keep_going=stepped.keep_going)

    return {'value': counting.value}


results = run(count_down, start=3)
