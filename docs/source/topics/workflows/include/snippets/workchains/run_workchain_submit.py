from aiida.engine import submit
from aiida.orm import Int

node = submit(AddAndMultiplyWorkChain, a=Int(value=1), b=Int(value=2), c=Int(value=3))  # noqa: F821
