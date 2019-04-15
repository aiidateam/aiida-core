# -*- coding: utf-8 -*-
"""
This allows to setup and configure a user from command line.
"""
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.common.exceptions import NotExistent

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


class User(VerdiCommandWithSubcommands):
    """
    List and configure new AiiDA users.

    Allow to see the list of AiiDA users, their permissions, and to configure
    old and new users.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'configure': (self.user_configure, self.complete_emails),
            'list': (self.user_list, self.complete_none),
        }

    def complete_emails(self, subargs_idx, subargs):
        load_dbenv()

        from aiida.backends.djsite.db import models

        emails = models.DbUser.objects.all().values_list('email', flat=True)
        return "\n".join(emails)

    def user_configure(self, *args):
        from aiida.backends.utils import is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

        import readline
        import getpass

        from aiida.orm.implementation import User

        if len(args) != 1:
            print >> sys.stderr, ("You have to pass (only) one parameter after "
                                  "'user configure', the email of")
            print >> sys.stderr, "the user to be configured."
            sys.exit(1)

        email = args[0]

        user_list = User.search_for_users(email=email)
        if user_list is not None and len(user_list) >= 1:
            user = user_list[0]
            print ""
            print ("An AiiDA user for email '{}' is already present "
                   "in the DB:".format(email))
            print "First name:   {}".format(user.first_name)
            print "Last name:    {}".format(user.last_name)
            print "Institution:  {}".format(user.institution)
            configure_user = False
            reply = raw_input("Do you want to reconfigure it? [y/N] ")
            reply = reply.strip()
            if not reply:
                pass
            elif reply.lower() == 'n':
                pass
            elif reply.lower() == 'y':
                configure_user = True
            else:
                print "Invalid answer, assuming answer was 'NO'"
        else:
            configure_user = True
            user = User(email=email)
            print "Configuring a new user with email '{}'".format(email)

        if configure_user:
            try:
                kwargs = {}
                # for field in models.DbUser.REQUIRED_FIELDS:
                for field in User.REQUIRED_FIELDS:
                    verbose_name = field.capitalize()
                    readline.set_startup_hook(lambda: readline.insert_text(
                        getattr(user, field)))
                    kwargs[field] = raw_input('{}: '.format(verbose_name))
            finally:
                readline.set_startup_hook(lambda: readline.insert_text(""))

            for k, v in kwargs.iteritems():
                setattr(user, k, v)

            change_password = False
            if user.has_usable_password():
                reply = raw_input("Do you want to replace the user password? [y/N] ")
                reply = reply.strip()
                if not reply:
                    pass
                elif reply.lower() == 'n':
                    pass
                elif reply.lower() == 'y':
                    change_password = True
                else:
                    print "Invalid answer, assuming answer was 'NO'"
            else:
                reply = raw_input("The user has no password, do you want to set one? [y/N] ")
                reply = reply.strip()
                if not reply:
                    pass
                elif reply.lower() == 'n':
                    pass
                elif reply.lower() == 'y':
                    change_password = True
                else:
                    print "Invalid answer, assuming answer was 'NO'"

            if change_password:
                match = False
                while not match:
                    new_password = getpass.getpass("Insert the new password: ")
                    new_password_check = getpass.getpass(
                        "Insert the new password (again): ")
                    if new_password == new_password_check:
                        match = True
                    else:
                        print "ERROR, the two passwords do not match."
                ## Set the password here
                user.password = new_password
            else:
                user.password = None

            user.force_save()
            print ">> User {} {} saved. <<".format(user.first_name,
                                                   user.last_name)
            if not user.has_usable_password():
                print "** NOTE: no password set for this user, "
                print "         so he/she will not be able to login"
                print "         via the REST API and the Web Interface."

    def user_list(self, *args):

        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.implementation import User
        from aiida.common.utils import get_configured_user_email

        from aiida.common.exceptions import ConfigurationError

        try:
            current_user = get_configured_user_email()
        except ConfigurationError:
            current_user = None

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

        if current_user is not None:
            # print >> sys.stderr, "### The '>' symbol indicates the current default user ###"
            pass
        else:
            print >> sys.stderr, "### No default user configured yet, run 'verdi install'! ###"

        for user in User.get_all_users():
            name_pieces = []
            if user.first_name:
                name_pieces.append(user.first_name)
            if user.last_name:
                name_pieces.append(user.last_name)
            full_name = " ".join(name_pieces)
            if full_name:
                full_name = " {}".format(full_name)

            institution_str = " ({})".format(
                user.institution) if user.institution else ""

            color_id = 39  # Default foreground color
            permissions_list = []
            if user.is_staff:
                permissions_list.append("STAFF")
            if user.is_superuser:
                permissions_list.append("SUPERUSER")
            if not user.has_usable_password():
                permissions_list.append("NO_PWD")
                color_id = 90  # Dark gray
            else:
                color_id = 34  # Blue
            permissions_str = ",".join(permissions_list)
            if permissions_str:
                permissions_str = " [{}]".format(permissions_str)

            if user.email == current_user:
                symbol = ">"
                color_id = 31
            else:
                symbol = "*"

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

            print "{}{} {}{}{}:{}{}{}{}".format(
                start_color, symbol,
                bold_sequence, user.email, nobold_sequence,
                full_name, institution_str, permissions_str, end_color)

