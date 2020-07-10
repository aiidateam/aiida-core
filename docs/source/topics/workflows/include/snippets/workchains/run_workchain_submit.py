# -*- coding: utf-8 -*-
from aiida.engine import submit
from aiida.orm import Int

node = submit(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
