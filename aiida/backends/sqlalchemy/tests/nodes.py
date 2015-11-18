# -*- coding: utf-8 -*-

from aiida.backends.sqlalchemy.tests.base import SqlAlchemyTests

from aiida.orm.node import Node


class TestTransitiveNoLoops(SqlAlchemyTests):
    """
    Test the creation of the transitive closure table
    """

    def test_loop_not_allowed(self):
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        n2._add_link_from(n1)
        n3._add_link_from(n2)
        n4._add_link_from(n3)

        with self.assertRaises(ValueError):  # This would generate a loop
            n1._add_link_from(n4)
