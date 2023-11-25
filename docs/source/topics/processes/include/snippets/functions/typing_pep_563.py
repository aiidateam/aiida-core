# -*- coding: utf-8 -*-
from __future__ import annotations

from aiida.engine import calcfunction


@calcfunction
def add(x: int, y: int):
    return x + y


add(1, 2)
