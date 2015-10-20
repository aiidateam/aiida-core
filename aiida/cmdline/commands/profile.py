# -*- coding: utf-8 -*-
"""
This allows to manage profiles from command line.
"""
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands


__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"


class Profile(VerdiCommandWithSubcommands):
    """
    List AiiDA profiles, and set the default profile.
    
    Allow to see the list of AiiDA profiles, and to set the default profile
    (the to be used by any verdi command when no '-p' option is given).
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'setdefault': (self.profile_setdefault, self.complete_profiles),
            'list': (self.profile_list, self.complete_none),
        }

    def complete_profiles(self, subargs_idx, subargs):
        from aiida.common.setup import get_profiles_list
        
        return "\n".join(get_profiles_list())

    def profile_setdefault(self, *args):
        from aiida.common.setup import set_default_profile

        if len(args) != 1:
            print >> sys.stderr, ("You have to pass (only) one parameter after "
                                  "'profile setdefault', the name of")
            print >> sys.stderr, "the profile to be set as the default."
            sys.exit(1)

        profile = args[0]        
        # set default DB profiles
        set_default_profile('verdi', profile, force_rewrite=True)
        set_default_profile('daemon', profile, force_rewrite=True)


    def profile_list(self, *args):
        from aiida.common.setup import get_profiles_list, get_default_profile
        from aiida.djsite.settings import settings_profile

        current_profile = settings_profile.AIIDADB_PROFILE
        default_profile = get_default_profile(
                settings_profile.CURRENT_AIIDADB_PROCESS)
        if current_profile is None:
            current_profile = default_profile

        use_colors = False
        if args:
            try:
                if len(args) != 1:
                    raise ValueError
                if args[0] != "--color":
                    raise ValueError
                use_colors = True
            except ValueError:
                print >> sys.stderr, ("You can pass only one further argument, "
                                      "--color, to show the results with colors")
                sys.exit(1)

        if current_profile is not None:
            # print >> sys.stderr, "### The '>' symbol indicates the current default user ###"
            pass
        else:
            print >> sys.stderr, "### No default profile configured yet, "\
                                 "run 'verdi install'! ###"

        for profile in get_profiles_list():
            color_id = 39  # Default foreground color
            if profile == current_profile:
                symbol = ">"
                color_id = 31
            else:
                symbol = "*"
                
            if profile == default_profile:
                color_id = 34
                default_str = ' (DEFAULT)'
            else:
                default_str = ''

            if use_colors:
                start_color = "\x1b[{}m".format(color_id)
                end_color = "\x1b[0m"
                bold_sequence = "\x1b[1;{}m".format(color_id)
                nobold_sequence = "\x1b[0;{}m".format(color_id)
            else:
                start_color = ""
                end_color = ""
                bold_sequence = ""
                nobold_sequence = ""

            print "{}{} {}{}{} {}{}".format(
                start_color, symbol,
                bold_sequence, profile, default_str, nobold_sequence, end_color)
        