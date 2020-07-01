#!/usr/bin/env python
# -*- coding: utf-8 -*-

def add(*args, **kwargs):
    return sum(args) + sum(kwargs.values())

add(4, 5, z=6)  # Returns 15
