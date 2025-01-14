#!/usr/bin/env python


def add(*args, **kwargs):
    return sum(args) + sum(kwargs.values())


add(4, 5, z=6)  # Returns 15
