#!/usr/bin/env python
# -*- coding: utf-8 -*-

def add_multiply(x, y=1, z):
    return (x + y) * z

add_multiply(x=1, 2, 3)  # Raises `SyntaxError` in definition and call
