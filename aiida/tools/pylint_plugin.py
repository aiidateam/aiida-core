# -*- coding: utf-8 -*-
"""pylint plugin for ``aiida-core`` specific linting issues.

the plugin can be loaded into pylint in the pyproject.toml::

    [tool.pylint.master]
    load-plugins = ["aiida.tools.pylint_plugin"]
"""
import astroid


def register(linter):  # pylint: disable=unused-argument
    """Register linters (unused)"""


def remove_classprop_imports(import_from: astroid.ImportFrom):
    """Remove any ``classproperty`` imports (handled in ``replace_classprops``)"""
    import_from.names = [name for name in import_from.names if name[0] != 'classproperty']


def replace_classprops(func: astroid.FunctionDef):
    """Replace ``classproperty`` decorated methods.

    As discussed in https://github.com/PyCQA/pylint/issues/1694, pylint does not understand the ``@classproperty``
    decorator, and so mistakes the method as a function, rather than an attribute of the class.
    If the method is annotated, this leads to pylint issuing ``no-member`` errors.

    This transform replaces ``classproperty`` decorated methods with an annotated attribute::

        from aiida.common.lang import classproperty

        class MyClass:
            @classproperty
            def my_property(cls) -> AnnotatedType:
                return cls.my_value

        MyClass.my_property.attribute  # <-- pylint issues: Method 'my_property' has no 'attribute' member (no-member)

        class MyClass:
            my_property: AnnotatedType

    """
    # ignore methods without annotations or decorators
    if not (func.returns and func.decorators and func.decorators.nodes):
        return
    # ignore methods that are specified as abstract
    if any(isinstance(node, astroid.Name) and 'abstract' in node.name for node in func.decorators.nodes):
        return
    if any(isinstance(node, astroid.Attribute) and 'abstract' in node.attrname for node in func.decorators.nodes):
        return
    # convert methods with @classproperty decorator
    if isinstance(func.decorators.nodes[0], astroid.Name) and func.decorators.nodes[0].name == 'classproperty':
        assign = astroid.AnnAssign(lineno=func.lineno, col_offset=func.col_offset, parent=func.parent)
        assign.simple = 1
        assign.target = astroid.AssignName(func.name, lineno=assign.lineno, col_offset=assign.col_offset, parent=assign)
        assign.annotation = func.returns
        assign.annotation.parent = assign
        func.parent.locals[func.name] = [assign.target]
        return assign


astroid.MANAGER.register_transform(astroid.ImportFrom, remove_classprop_imports)
astroid.MANAGER.register_transform(astroid.FunctionDef, replace_classprops)
