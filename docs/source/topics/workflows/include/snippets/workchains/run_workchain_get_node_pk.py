# -*- coding: utf-8 -*-
from aiida.engine import run_get_node, run_get_pk
from aiida.orm import Int

result, node = run_get_node(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
result, pk = run_get_pk(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
