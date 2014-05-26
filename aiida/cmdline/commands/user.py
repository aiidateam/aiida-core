"""
This allows to setup and configure a user from command line.
"""
import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django


class User(VerdiCommand):
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

    def run(self,*args):       
        try:
            function_to_call = self.valid_subcommands[args[0]][0]
        except IndexError:
            function_to_call = self.no_subcommand
        except KeyError:
            function_to_call = self.invalid_subcommand
            
        function_to_call(*args[1:])

    def complete(self,subargs_idx, subargs):
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        elif subargs_idx == 1:
            try:
                first_subarg = subargs[0]
            except  IndexError:
                first_subarg = ''
            try:
                complete_function = self.valid_subcommands[first_subarg][1] 
            except KeyError:
                print ""
                return
            print complete_function()

    def complete_none(self):
        return ""
        
    def complete_emails(self):
        load_django()
        
        from aiida.djsite.db import models
        
        emails = models.DbUser.objects.all().values_list('email',flat=True)
        return "\n".join(emails)

    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'user'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self, *args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'user'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def user_configure(self, *args):
        load_django()

        import readline
        import getpass
        
        from aiida.djsite.db import models
        from django.core.exceptions import ObjectDoesNotExist

        
        if len(args) != 1:
            print >> sys.stderr, ("You have to pass (only) one parameter after "
                                  "'user configure', the email of")
            print >> sys.stderr,  "the user to be configured."
            sys.exit(1)
            
        email = args[0]

        try:
            user = models.DbUser.objects.get(email=email)
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
        except ObjectDoesNotExist:
            configure_user = True
            user = models.DbUser(email=email)
            print "Configuring a new user with email '{}'".format(email)

            
        if configure_user:
            try:
                kwargs = {}
    
                for field in models.DbUser.REQUIRED_FIELDS:
                    verbose_name = models.DbUser._meta.get_field_by_name(
                        field)[0].verbose_name.capitalize()
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
                user.set_password(new_password)
            
            user.save()
            print ">> User {} saved. <<".format(user.get_full_name())
            if not user.has_usable_password():
                print "** NOTE: no password set for this user, "
                print "         so he/she will not be able to login"
                print "         via the REST API and the Web Interface."

    def user_list(self, *args):
        load_django()
        
        from aiida.djsite.db.models import DbUser
        from aiida.djsite.utils import get_configured_user_email
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
            #print >> sys.stderr, "### The '>' symbol indicates the current default user ###"
            pass
        else:
            print >> sys.stderr, "### No default user configured yet, run 'verdi install'! ###"
            
        for user in DbUser.objects.all().order_by('email'):
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
            
            color_id = 39 # Default foreground color
            permissions_list = []
            if user.is_staff:
                permissions_list.append("STAFF")
            if user.is_superuser:
                permissions_list.append("SUPERUSER")
            if not user.has_usable_password():
                permissions_list.append("NO_PWD")
                color_id = 90 # Dark gray
            else:
                color_id = 34 # Blue
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
                