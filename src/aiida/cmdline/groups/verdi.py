"""Subclass of :class:`click.Group` for the ``verdi`` CLI."""

from __future__ import annotations

import base64
import difflib
import gzip
import typing as t

import click

from aiida.cmdline.utils.echo import echo_deprecated
from aiida.common.exceptions import ConfigurationError
from aiida.common.extendeddicts import AttributeDict
from aiida.manage.configuration import get_config

from ..params import options

__all__ = ('VerdiCommandGroup',)

GIU = (
    'ABzY8%U8Kw0{@klyK?I~3`Ki?#qHQ&IIM|J;6yB`9_+{&w)p(JK}vokj-11jhve8xcx?dZ>+9nwrEF!x*S>9A+EWYrR?6GA-u?jFa+et65GF@1+D{%'
    '8{C~xjt%>uVM4RTSS?j2M)XH%T#>M{K$lE2XGD`<aYaOFUit|Wh*Q?-n)Bs}n0}hc2!oAkoBQyEOaSkqfd=oq;sTs(x@(H&qOKnXDFA52~gq4CvNbk'
    '%p9&pE+KH!2lm^MThvE$xC2x*>RS0T67213wbAs!SZmn+;(-m!>f(T@e%@oxd`yRBp9nu+9N`4xv8AS@O$CaQ;7FXzM=ug^$?3ta2551EDL`wK4|Cm'
    '%RnJdS#0UF<by)B<XQ+8vZ}j$b$@4Q1#kj{G|g6{1#bLd+w)SZ16_wTnfo<QXMd-s4ImikcvSj#7~2Yq-1l@K)y|aS%KqzrV$m)VgR$xs8bGr7%$lJ'
    '_ObpObgS_mhZ7M97P}ATen9Zil^7;P;<I08Mv_;!$Eb2P)F|&t+wT?>wVwe<Fez}g$`Zi>DkcfdNjtUv1N^iSQui#TL(q!FmIeKb!yW4|L`@!@-4x6'
    'B6I^ptRdH+4o0ODM;1_f^}4@LMe@#_YHz0wQdq@d)@n)uYNtAb2OLo&fpBkct5{~3kbRag^_5QG%qrTksHMXAYAQoz1#2wtHCy0}h?CJtzv&@Q?^9r'
    'd&02;isB7NJMMr7F@>$!ELj(sbwzIR4)rnch=oVZrG;8)%R6}FUk*fv2O&!#ZA)$HloK9!es&4Eb+h=OIyWFha(8PPy9u?NqfkuPYg;GO1RVzBLX)7'
    'ORMM>1hEM`-96mGjJ+A!e-_}4X{M|4CkKE~uF4j+LW#6IsFa*_da_mLqzr)E<`%ikthkMO2<vdLNlWMLBrceLb&%p<SlbT6NAh+Tz~72^U2(&}V&4H'
    'd8r#{;M;(*9swiCZ2RIx2&yLd0wV^AQs5$V63{q89vFwvV_?Vk!HuDTPr83yG~Wm}YG_*0gIL7B~{>>65cNMtpDE*VejqZV^MyewPJJAS*VM6jY;QY'
    '#g7gOKgPbFg{@;YDL6Gbxxr|2T&BQunB?PBetq?X<bp0b)qASa|!TspwLp%9CE7Y#XI@}Wa3E6#mZC62W0F#k>>jW1hFF7&>EaYkKYqIa_ld(Z@AJT'
    '+lJ(Pd;+?<&&M>A0agti19^z3n4Z6_WG}c~_+XHyJI_iau7+V$#YA$pJ~H)yHEVy1D?5^Sw`tb@{nnNNo=eSMZLf0>m^A@7f{y$nb_HJWgLRtZ?<Vq'
    'Glx*4Tkeba)%-_D&vG1uUL0(DEK)&;4yGQ@C_0d4x%#)?G?XfN*{PN40X3QeC3@;*9uMwABesu!8?(0#>x2?*>SwM?JoQ>p|-1ZRU0#+{^UhK22+~o'
    'R9k7rh<eeM8~?e5)U+OloQYk-ebZsXE8KFmR5;uE)C;wlw}@dIbx-{${l+HbC|PrK*6{Q(q6jMpni4Be``)PJJRU>(GH9y|jm){jY9_xAI4N_EfU#4'
    'taTUXFY4a4l$v=N-+f+w&wuH;Z(6p6#=n8XwlZ;*L&-rcL~T_vEm@#-Xi8&g06!MO+R(<NRBkE$(0Y_~^2C_k<o~_a3*HAHukZKXCs8^y%UZZVvze'
)


class LazyVerdiObjAttributeDict(AttributeDict):
    """Subclass of ``AttributeDict`` that lazily initializes the ``config`` and ``profile`` attributes.

    This class guarantees that the ``config`` and ``profile`` attributes never raise an ``AttributeError``. When the
    attributes are accessed when they are not set, ``config`` is initialized by the value returned by the method
    :meth:`aiida.manage.configuration.get_config`. The ``profile`` attribute is initialized to ``None``.
    """

    _KEY_CONFIG = 'config'
    _KEY_PROFILE = 'profile'

    def __init__(self, ctx: click.Context, dictionary: dict[str, t.Any] | None = None):
        super().__init__(dictionary)  # type: ignore[no-untyped-call]
        self.ctx = ctx

    def __getattr__(self, attr: str) -> t.Any:
        """Override of ``AttributeDict.__getattr__`` to lazily initialize the ``config`` and ``profile`` attributes.

        :param attr: The attribute to return.
        :returns: The value of the attribute.
        :raises AttributeError: If the attribute does not correspond to an existing key.
        :raises click.exceptions.UsageError: If loading of the configuration fails.
        """
        if attr == self._KEY_PROFILE:
            self.setdefault(self._KEY_PROFILE, None)

        elif attr == self._KEY_CONFIG and self._KEY_CONFIG not in self:
            try:
                self[self._KEY_CONFIG] = get_config(create=True)
            except ConfigurationError as exception:
                self.ctx.fail(str(exception))

        return super().__getattr__(attr)  # type: ignore[no-untyped-call]


class VerdiContext(click.Context):
    """Custom context implementation that defines the ``obj`` user object and adds the ``Config`` instance."""

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        if self.obj is None:
            self.obj = LazyVerdiObjAttributeDict(self)


class VerdiCommand(click.Command):
    """Custom command implementation to customize the logic of printing deprecation messages.

    If a command is deprecated, the :class:`click.Command` adds a deprecation marker in the short help and the full
    help text, and prints a deprecation warning when the command is invoked. The problem is that the deprecation warning
    is printed after the prompting for parameters, which for interactive commands mean the deprecation warning comes too
    late, when the user has already provided all prompts.

    Here, the `click.Command.parse_args
    <https://github.com/pallets/click/blob/f8d811e5d5644aca8d32eebff196bf7c659ebf45/src/click/core.py#L1369>`_ method is
    overridden, which is called before the interactive options start to prompt, such that the deprecation warning can be
    printed. The :meth:`click.Command.invoke` method is also overridden in order to skip the printing of the deprecation
    message handled by ``click`` as that would result in the deprecation message being printed twice.
    """

    def parse_args(self, ctx: click.Context, args: t.List[str]) -> t.List[str]:
        """Given a context and a list of arguments this creates the parser and parses the arguments.

        Then context is modified as necessary.

        This is automatically invoked by `click.BaseCommand.make_context
        <https://github.com/pallets/click/blob/f8d811e5d5644aca8d32eebff196bf7c659ebf45/src/click/core.py#L884>`_.
        """
        if self.deprecated:
            # We are abusing click.Command `deprecated` member variable by using a
            # string instead of a bool to also use it as optional deprecated message
            echo_deprecated(
                self.deprecated
                if isinstance(self.deprecated, str)  # type: ignore[redundant-expr]
                else 'This command is deprecated.'
            )

        return super().parse_args(ctx, args)

    def invoke(self, ctx: click.Context) -> t.Any:
        if self.callback is not None:
            return ctx.invoke(self.callback, **ctx.params)


class VerdiCommandGroup(click.Group):
    """Subclass of :class:`click.Group` for the ``verdi`` CLI.

    The class automatically adds the verbosity option to all commands in the interface. It also adds some functionality
    to provide suggestions of commands in case the user provided command name does not exist.
    """

    context_class = VerdiContext
    command_class = VerdiCommand

    @staticmethod
    def add_verbosity_option(cmd: click.Command) -> click.Command:
        """Apply the ``verbosity`` option to the command, which is common to all ``verdi`` commands."""
        # Only apply the option if it hasn't been already added in a previous call.
        if 'verbosity' not in [param.name for param in cmd.params]:
            cmd = options.VERBOSITY()(cmd)

        return cmd

    def fail_with_suggestions(self, ctx: click.Context, cmd_name: str) -> None:
        """Fail the command while trying to suggest commands to resemble the requested ``cmd_name``."""
        # We might get better results with the Levenshtein distance or more advanced methods implemented in FuzzyWuzzy
        # or similar libs, but this is an easy win for now.
        matches = difflib.get_close_matches(cmd_name, self.list_commands(ctx), cutoff=0.5)

        if not matches:
            # Single letters are sometimes not matched so also try with a simple startswith
            matches = [c for c in sorted(self.list_commands(ctx)) if c.startswith(cmd_name)][:3]

        if matches:
            formatted = '\n'.join(f'\t{m}' for m in sorted(matches))
            ctx.fail(f'`{cmd_name}` is not a {self.name} command.\n\nThe most similar commands are:\n{formatted}')
        else:
            ctx.fail(f'`{cmd_name}` is not a {self.name} command.\n\nNo similar commands found.')

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return the command that corresponds to the requested ``cmd_name``.

        This method is overridden from the base class in order to two functionalities:

            * If the command is found, automatically add the verbosity option.
            * If the command is not found, attempt to provide a list of suggestions with existing commands that resemble
              the requested command name.

        Note that if the command is not found and ``resilient_parsing`` is set to True on the context, then the latter
        feature is disabled because most likely we are operating in tab-completion mode.
        """
        if int(cmd_name.lower().encode('utf-8').hex(), 16) == 0x6769757365707065:
            click.echo(gzip.decompress(base64.b85decode(GIU.encode('utf-8'))).decode('utf-8'))
            return None

        cmd = super().get_command(ctx, cmd_name)

        if cmd is not None:
            return self.add_verbosity_option(cmd)

        # If this command is called during tab-completion, we do not want to print an error message if the command can't
        # be found, but instead we want to simply return here. However, in a normal command execution, we do want to
        # execute the rest of this method to try and match commands that are similar in order to provide the user with
        # some hints. The problem is that there is no one canonical way to determine whether the invocation is due to a
        # normal command execution or a tab-complete operation. The `resilient_parsing` attribute of the `Context` is
        # designed to allow things like tab-completion, however, it is not the only purpose. For now this is our best
        # bet though to detect a tab-complete event. When `resilient_parsing` is switched on, we assume a tab-complete
        # and do nothing in case the command name does not match an actual command.
        if ctx.resilient_parsing:
            return None

        self.fail_with_suggestions(ctx, cmd_name)

        return None

    def group(self, *args: t.Any, **kwargs: t.Any) -> click.Group:
        """Ensure that sub command groups use the same class but do not override an explicitly set value."""
        kwargs.setdefault('cls', self.__class__)
        return super().group(*args, **kwargs)  # type: ignore[no-any-return]
