# -*- coding: utf-8 -*-
from __future__ import annotations

from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add_multiply(x: int, y: int, z: int | None = None):
    if z is None:
        z = Int(3)

    return (x + y) * z


result = add_multiply(1, 2)
result = add_multiply(1, 2, 3)
