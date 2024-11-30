"""Tests for :mod:`aiida.tools.ipython.ipython_magics`."""

import textwrap

from IPython.testing.globalipapp import get_ipython

from aiida.tools.ipython.ipython_magics import register_ipython_extension


def test_ipython_magics():
    """Test that the ``%aiida`` magic can be loaded and imports the ``QueryBuilder`` and ``Node`` classes."""
    ipy = get_ipython()
    register_ipython_extension(ipy)
    cell = textwrap.dedent(
        """
        %aiida
        qb=QueryBuilder()
        qb.append(Node)
        qb.all()
        Dict().store()
        """
    )
    result = ipy.run_cell(cell)
    assert result.success
