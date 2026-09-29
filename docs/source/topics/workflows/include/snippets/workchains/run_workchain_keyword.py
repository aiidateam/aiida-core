from aiida.engine import run
from aiida.orm import Int

result = run(AddAndMultiplyWorkChain, a=Int(value=1), b=Int(value=2), c=Int(value=3))  # noqa: F821
