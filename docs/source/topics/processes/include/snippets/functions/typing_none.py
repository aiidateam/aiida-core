# -*- coding: utf-8 -*-
import typing

from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add_multiply(x: Int, y: Int, z: typing.Optional[Int] = None):
    if z is None:
        z = Int(3)

    return (x + y) * z


result = add_multiply(Int(1), Int(2))
result = add_multiply(Int(1), Int(2), Int(3))
