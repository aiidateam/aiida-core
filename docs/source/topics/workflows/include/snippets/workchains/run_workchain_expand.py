from aiida.engine import run
from aiida.orm import Int

inputs = {'a': Int(value=1), 'b': Int(value=2), 'c': Int(value=3)}
result = run(AddAndMultiplyWorkChain, **inputs)  # noqa: F821
