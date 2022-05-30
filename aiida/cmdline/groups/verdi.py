# -*- coding: utf-8 -*-
"""Subclass of :class:`click.Group` for the ``verdi`` CLI."""
import base64
import difflib
import gzip

import click

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


class VerdiContext(click.Context):
    """Custom context implementation that defines the ``obj`` user object and adds the ``Config`` instance."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.obj is None:
            self.obj = AttributeDict()

        try:
            self.obj.config = get_config(create=True)
        except ConfigurationError as exception:
            self.fail(str(exception))


class VerdiCommandGroup(click.Group):
    """Subclass of :class:`click.Group` for the ``verdi`` CLI.

    The class automatically adds the verbosity option to all commands in the interface. It also adds some functionality
    to provide suggestions of commands in case the user provided command name does not exist.
    """

    context_class = VerdiContext

    @staticmethod
    def add_verbosity_option(cmd):
        """Apply the ``verbosity`` option to the command, which is common to all ``verdi`` commands."""
        # Only apply the option if it hasn't been already added in a previous call.
        if cmd is not None and 'verbosity' not in [param.name for param in cmd.params]:
            cmd = options.VERBOSITY()(cmd)

        return cmd

    def fail_with_suggestions(self, ctx, cmd_name):
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

    def get_command(self, ctx, cmd_name):
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
            return

        self.fail_with_suggestions(ctx, cmd_name)

    def group(self, *args, **kwargs):
        """Ensure that sub command groups use the same class but do not override an explicitly set value."""
        kwargs.setdefault('cls', self.__class__)
        return super().group(*args, **kwargs)
