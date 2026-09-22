from aiida.engine import submit
from aiida.orm import Int

builder = AddAndMultiplyWorkChain.get_builder()  # noqa: F821
builder.a = Int(value=1)
builder.b = Int(value=2)
builder.c = Int(value=3)

node = submit(builder)
