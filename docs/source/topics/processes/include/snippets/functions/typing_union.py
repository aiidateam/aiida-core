# -*- coding: utf-8 -*-
import typing as t

from aiida.engine import calcfunction
from aiida.orm import Float, Int


@calcfunction
def add(x: t.Union[Int, Float], y: t.Union[Int, Float]):
    return x + y

add(Int(1), Float(1.0))
