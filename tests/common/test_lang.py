# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :py:mod:`~aiida.common.lang` module."""

from aiida.backends.testbase import AiidaTestCase
from aiida.common import lang

protected_checked = lang.protected_decorator(check=True)  # pylint: disable=invalid-name
protected_unchecked = lang.protected_decorator(check=False)  # pylint: disable=invalid-name


class Protected:
    """Class to test the protected decorator."""

    # pylint: disable=no-self-use

    def member_internal(self):
        """Class method that is allowed to call the protected methods."""
        result = self.member_unprotected()
        result &= self.member_protected_checked()
        result &= self.member_protected_unchecked()
        result &= self.property_correct_order
        return result

    def member_unprotected(self):
        """Simple unproctected method."""
        return True

    @protected_unchecked
    def member_protected_unchecked(self):
        """Decorated method but without check - can be called outside scope."""
        return True

    @protected_checked
    def member_protected_checked(self):
        """Decorated method but without check - cannot be called outside scope."""
        return True

    @property
    @protected_checked
    def property_correct_order(self):
        """Decorated property but without check - cannot be called outside scope."""
        return True


class TestProtectedDecorator(AiidaTestCase):
    """Tests for the :py:func:`~aiida.common.lang.protected` decorator."""

    # pylint: disable=unused-variable

    def test_free_function(self):
        """Decorating a free function should raise."""
        with self.assertRaises(RuntimeError):

            @protected_unchecked
            def some_function():
                pass

    def test_property_incorrect_order(self):
        """The protected decorator should raise if applied before the property decorator."""
        with self.assertRaises(RuntimeError):

            class InvalidProtected:
                """Invalid use of protected decorator."""

                @staticmethod
                @protected_checked
                @property
                def property_incorrect_order():
                    return True

    def test_internal(self):
        """Calling protected internally from a public class method should work."""
        instance = Protected()
        self.assertTrue(instance.member_internal())

    def test_unprotected(self):
        """Test that calling unprotected class method is allowed."""
        instance = Protected()
        self.assertTrue(instance.member_unprotected())

    def test_protected_unchecked(self):
        """Test that calling an unchecked protected class method is allowed."""
        instance = Protected()
        self.assertTrue(instance.member_protected_unchecked())

    def test_protected_checked(self):
        """Test that calling a checked protected class method raises."""
        instance = Protected()
        with self.assertRaises(RuntimeError):
            self.assertTrue(instance.member_protected_checked())

    def test_protected_property_correct_order(self):
        """Test that calling a checked protected property raises."""
        instance = Protected()
        with self.assertRaises(RuntimeError):
            self.assertEqual(instance.property_correct_order, True)
