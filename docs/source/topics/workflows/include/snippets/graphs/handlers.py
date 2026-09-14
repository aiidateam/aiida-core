from aiida.engine import ExitCode, ProcessHandlerReport, graph, handler, run, task

DID_NOT_CONVERGE = ExitCode(410, 'did not converge')


@handler(exit_codes=DID_NOT_CONVERGE)
def push_further(node, inputs):
    """Ask for one more step than the run that gave up took."""
    inputs['steps'] = inputs['steps'] + 1
    return ProcessHandlerReport(do_break=True)


@task(outputs=['value'], handlers=[push_further])
def converge(steps: int) -> int:
    if steps < 3:
        return DID_NOT_CONVERGE
    return steps * 10


@graph
def converge_from(steps):
    return {'value': converge(steps=steps, max_iterations=5).value}


results = run(converge_from, steps=1)
