#!/usr/bin/env python

def add_multiply(x, y=1, z):
    return (x + y) * z

add_multiply(x=1, 2, 3)  # Raises `SyntaxError` in definition and call
