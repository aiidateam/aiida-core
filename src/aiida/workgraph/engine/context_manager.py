from __future__ import annotations

from aiida.common.extendeddicts import AttributeDict
import logging


class ContextManager:
    """Manages the context for the WorkGraphEngine."""

    _CONTEXT = 'CONTEXT'

    def __init__(self, _context, process, logger: logging.Logger):
        self.process = process
        self._context = _context
        self.logger = logger

    @property
    def ctx(self) -> AttributeDict:
        """Access the context."""
        return self._context

    def resolve_nested_context(self, key: str) -> tuple[AttributeDict, str]:
        """
        Returns a reference to a sub-dictionary of the context and the last key,
        after resolving a potentially segmented key where required sub-dictionaries are created as needed.

        :param key: A key into the context, where words before a dot are interpreted as a key for a sub-dictionary
        """
        ctx = self.ctx
        ctx_path = key.split('.')

        for index, path in enumerate(ctx_path[:-1]):
            try:
                ctx = ctx[path]
            except KeyError:  # see below why this is the only exception we have to catch here
                ctx[path] = AttributeDict()  # create the sub-dict and update the context
                ctx = ctx[path]
                continue

            # Notes:
            # * the first ctx (self.ctx) is guaranteed to be an AttributeDict, hence the post-"dereference" checking
            # * the values can be many different things: on insertion they are either AtrributeDict, List or Awaitables
            #   (subclasses of AttributeDict) but after resolution of an Awaitable this will be the value itself
            # * assumption: a resolved value is never a plain AttributeDict, on the other hand if a resolved Awaitable
            #   would be an AttributeDict we can append things to it since the order of tasks is maintained.
            if isinstance(ctx, AttributeDict):
                raise ValueError(
                    f'Can not update the context for key `{key}`: '
                    f' found instance of `{type(ctx)}` at `{".".join(ctx_path[: index + 1])}`, expected AttributeDict'
                )

        return ctx, ctx_path[-1]
