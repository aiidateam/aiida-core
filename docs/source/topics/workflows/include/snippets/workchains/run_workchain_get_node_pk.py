from aiida.engine import run_get_node, run_get_pk
from aiida.orm import Int

result, node = run_get_node(AddAndMultiplyWorkChain, a=Int(value=1), b=Int(value=2), c=Int(value=3))  # noqa: F821
result, pk = run_get_pk(AddAndMultiplyWorkChain, a=Int(value=1), b=Int(value=2), c=Int(value=3))  # noqa: F821
