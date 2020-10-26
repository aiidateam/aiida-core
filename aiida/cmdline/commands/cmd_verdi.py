# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The main `verdi` click group."""

import difflib
import click

from aiida.cmdline.params import options, types

GIU = (
    'ABzY8%U8Kw0{@klyK?I~3`Ki?#qHQ&IIM|J;6yB`9_+{&w)p(JK}vokj-11jhve8xcx?dZ>+9nwrEF!x'
    '*S>9A+EWYrR?6GA-u?jFa+et65GF@1+D{%8{C~xjt%>uVM4RTSS?j2M)XH%T#>M{K$lE2XGD`<aYaOFU'
    'it|Wh*Q?-n)Bs}n0}hc2!oAkoBQyEOaSkqfd=oq;sTs(x@(H&qOKnXDFA52~gq4CvNbk%p9&pE+KH!2l'
    'm^MThvE$xC2x*>RS0T67213wbAs!SZmn+;(-m!>f(T@e%@oxd`yRBp9nu+9N`4xv8AS@O$CaQ;7FXzM='
    'ug^$?3ta2551EDL`wK4|Cm%RnJdS#0UF<by)B<XQ+8vZ}j$b$@4Q1#kj{G|g6{1#bLd+w)SZ16_wTnfo'
    '<QXMd-s4ImikcvSj#7~2Yq-1l@K)y|aS%KqzrV$m)VgR$xs8bGr7%$lJ_ObpObgS_mhZ7M97P}ATen9Z'
    'il^7;P;<I08Mv_;!$Eb2P)F|&t+wT?>wVwe<Fez}g$`Zi>DkcfdNjtUv1N^iSQui#TL(q!FmIeKb!yW4'
    '|L`@!@-4x6B6I^ptRdH+4o0ODM;1_f^}4@LMe@#_YHz0wQdq@d)@n)uYNtAb2OLo&fpBkct5{~3kbRag'
    '^_5QG%qrTksHMXAYAQoz1#2wtHCy0}h?CJtzv&@Q?^9rd&02;isB7NJMMr7F@>$!ELj(sbwzIR4)rnch'
    '=oVZrG;8)%R6}FUk*fv2O&!#ZA)$HloK9!es&4Eb+h=OIyWFha(8PPy9u?NqfkuPYg;GO1RVzBLX)7OR'
    'MM>1hEM`-96mGjJ+A!e-_}4X{M|4CkKE~uF4j+LW#6IsFa*_da_mLqzr)E<`%ikthkMO2<vdLNlWMLBr'
    'ceLb&%p<SlbT6NAh+Tz~72^U2(&}V&4Hd8r#{;M;(*9swiCZ2RIx2&yLd0wV^AQs5$V63{q89vFwvV_?'
    'Vk!HuDTPr83yG~Wm}YG_*0gIL7B~{>>65cNMtpDE*VejqZV^MyewPJJAS*VM6jY;QY#g7gOKgPbFg{@;'
    'YDL6Gbxxr|2T&BQunB?PBetq?X<bp0b)qASa|!TspwLp%9CE7Y#XI@}Wa3E6#mZC62W0F#k>>jW1hFF7'
    '&>EaYkKYqIa_ld(Z@AJT+lJ(Pd;+?<&&M>A0agti19^z3n4Z6_WG}c~_+XHyJI_iau7+V$#YA$pJ~H)y'
    'HEVy1D?5^Sw`tb@{nnNNo=eSMZLf0>m^A@7f{y$nb_HJWgLRtZ?<VqGlx*4Tkeba)%-_D&vG1uUL0(DE'
    'K)&;4yGQ@C_0d4x%#)?G?XfN*{PN40X3QeC3@;*9uMwABesu!8?(0#>x2?*>SwM?JoQ>p|-1ZRU0#+{^'
    'UhK22+~oR9k7rh<eeM8~?e5)U+OloQYk-ebZsXE8KFmR5;uE)C;wlw}@dIbx-{${l+HbC|PrK*6{Q(q6'
    'jMpni4Be``)PJJRU>(GH9y|jm){jY9_xAI4N_EfU#4taTUXFY4a4l$v=N-+f+w&wuH;Z(6p6#=n8XwlZ'
    ';*L&-rcL~T_vEm@#-Xi8&g06!MO+R(<NRBkE$(0Y_~^2C_k<o~_a3*HAHukZKXCs8^y%UZZVvze'
)


class MostSimilarCommandGroup(click.Group):
    """
    Overloads the get_command to display a list of possible command
    candidates if the command could not be found with an exact match.
    """

    def get_command(self, ctx, cmd_name):
        """
        Override the default click.Group get_command with one giving the user
        a selection of possible commands if the exact command name could not be found.
        """
        cmd = click.Group.get_command(self, ctx, cmd_name)

        # return the exact match
        if cmd is not None:
            return cmd

        if int(cmd_name.lower().encode('utf-8').hex(), 16) == 0x6769757365707065:
            import base64
            import gzip
            click.echo(gzip.decompress(base64.b85decode(GIU.encode('utf-8'))).decode('utf-8'))
            return None

        # we might get better results with the Levenshtein distance
        # or more advanced methods implemented in FuzzyWuzzy or similar libs,
        # but this is an easy win for now
        matches = difflib.get_close_matches(cmd_name, self.list_commands(ctx), cutoff=0.5)

        if not matches:
            # single letters are sometimes not matched, try with a simple startswith
            matches = [c for c in sorted(self.list_commands(ctx)) if c.startswith(cmd_name)][:3]

        if matches:
            ctx.fail(
                "'{cmd}' is not a verdi command.\n\n"
                'The most similar commands are: \n'
                '{matches}'.format(cmd=cmd_name, matches='\n'.join('\t{}'.format(m) for m in sorted(matches)))
            )
        else:
            ctx.fail(f"'{cmd_name}' is not a verdi command.\n\nNo similar commands found.")

        return None


@click.command(cls=MostSimilarCommandGroup, context_settings={'help_option_names': ['-h', '--help']})
@options.PROFILE(type=types.ProfileParamType(load_profile=True))
@click.version_option(None, '-v', '--version', message='AiiDA version %(version)s')
@click.pass_context
def verdi(ctx, profile):
    """The command line interface of AiiDA."""
    from aiida.common import extendeddicts
    from aiida.manage.configuration import get_config

    if ctx.obj is None:
        ctx.obj = extendeddicts.AttributeDict()

    ctx.obj.config = get_config()
    ctx.obj.profile = profile
