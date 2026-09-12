from aiida.engine import calcfunction


@calcfunction
def add(x: int, y: int):
    """Add two integers.

    :param x: Left hand operand.
    :param y: Right hand operand.
    """
    return x + y


assert add.spec().inputs['a'].help == 'Left hand operand.'
assert add.spec().inputs['b'].help == 'Right hand operand.'
