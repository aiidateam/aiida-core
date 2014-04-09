import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

class Computer(VerdiCommand):
    """
    Setup and manage computers to be used

    This command allows to list, add, modify and configure computers.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'list': (self.computer_list, self.complete_none),
            'show' : (self.computer_show, self.complete_computers),
            'setup': (self.computer_setup, self.complete_computers),
            'rename': (self.computer_rename, self.complete_computers),
            'configure': (self.computer_configure, self.complete_computers),
            'delete': (self.computer_delete, self.complete_computers),
            }

    def run(self,*args):       
        """
        Run the specified subcommand.
        """
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
        # Only one-level completion allowed
        else:
            print self.complete_none()

    def complete_none(self):
        return ""
        
    def complete_computers(self):
        computer_names = self.get_computer_names()
        return "\n".join(computer_names)

    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'computer'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'computer'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def computer_list(self, *args):
        """
        List available computers
        """
        if args:
            print >> sys.stderr, "No arguments allowed to the 'list' command."
            sys.exit(1)
        
        computer_names = self.get_computer_names()
        
        print "# List of configured computers:"
        print "# (use 'verdi computer show COMPUTERNAME' to see the details)"
        if computer_names:
            print "\n".join("* {}".format(i) for i in computer_names)
        else:
            print "# No computers configured yet. Use 'verdi computer setup'"
        
    def computer_show(self, *args):
        """
        Show information on a given computer
        """
        from aiida.common.exceptions import NotExistent
        if len(args) != 1:
            print >> sys.stderr, ("after 'computer show' there should be one "
                                  "argument only, being the computer name.")
            sys.exit(1)
        try:
            computer = self.get_computer(name=args[0])
        except NotExistent:
            print >> sys.stderr, "No computer in the DB with name {}.".format(
                 args[0])
            sys.exit(1)    
        print computer.full_text_info
        
    def computer_setup(self, *args):
        """
        Setup a new or existing computer
        """
        import inspect
        import readline
        
        from aiida.common.exceptions import NotExistent, ValidationError
        from aiida.orm import Computer as AiidaOrmComputer
          
        if len(args) != 1:
            print >> sys.stderr, ("after 'computer setup' there should be one "
                                  "argument only, being the computer name.")
            sys.exit(1)
        
        load_django()
        
        computer_name = args[0]
        
        try:
            computer = self.get_computer(name=computer_name)
            print "*"*75
            print "WARNING! Modifying existing computer with name '{}'".format(computer_name)
            print "Are you sure you want to continue? The UUID will remain the same!"
            print "Continue only if you know what you are doing."
            print "If you just want to rename a computer, use the 'verdi computer rename'"
            print "command. In most cases, it is better to create a new computer."
            print "Moreover, if you change the transport, you must also reconfigure"
            print "each computer for each user!"
            print "*"*75
            print "Press [Enter] to continue, or [Ctrl]+C to exit."
            raw_input()
        except NotExistent:
            computer = AiidaOrmComputer(name=computer_name)    
            print "Creating new computer with name '{}'".format(computer_name)
        
        print "At any prompt, type ? to get some help."
        print "---------------------------------------"

        for internal_name, name, desc, multiline in (
          AiidaOrmComputer._conf_attributes):

            getter_name = '_get_{}_string'.format(internal_name)
            try:
                getter = dict(inspect.getmembers(
                   computer))[getter_name]
            except KeyError:
                print >> sys.stderr, ("Internal error! "
                    "No {} getter defined in Computer".format(getter_name))
                sys.exit(1)
            previous_value = getter()
                
            setter_name = '_set_{}_string'.format(internal_name)
            try:
                setter = dict(inspect.getmembers(
                   computer))[setter_name]
            except KeyError:
                print >> sys.stderr, ("Internal error! "
                    "No {} setter defined in Computer".format(setter_name))
                sys.exit(1)
            
            valid_input = False
            while not valid_input:
                if multiline:
                    newlines = []
                    print "=> {}: ".format(name)
                    print "   # This is a multiline input, press CTRL+D on a"
                    print "   # empty line when you finish"

                    try:
                        for l in previous_value.splitlines():                        
                            while True: 
                                readline.set_startup_hook(lambda:
                                    readline.insert_text(l))
                                input_txt = raw_input()
                                if input_txt.strip() == '?':
                                    print ["  > {}".format(descl) for descl
                                           in "HELP: {}".format(desc).split('\n')]
                                    continue
                                else:
                                    newlines.append(input_txt)
                                    break
                        
                        # Reset the hook (no default text printed)
                        readline.set_startup_hook()
                        
                        print "   # ------------------------------------------"
                        print "   # End of old input. You can keep adding     "
                        print "   # lines, or press CTRL+D to store this value"
                        print "   # ------------------------------------------"
                        
                        while True: 
                            input_txt = raw_input()
                            if input_txt.strip() == '?':
                                print "\n".join(["  > {}".format(descl) for descl
                                       in "HELP: {}".format(desc).split('\n')])
                                continue
                            else:
                                newlines.append(input_txt)
                    except EOFError:
                        #Ctrl+D pressed: end of input.
                        pass
                    
                    input_txt = "\n".join(newlines)
                    
                else: # No multiline
                    readline.set_startup_hook(lambda: readline.insert_text(
                        previous_value))
                    input_txt = raw_input("=> {}: ".format(name))
                    if input_txt.strip() == '?':
                        print "HELP:", desc
                        continue

                try:
                    setter(input_txt)
                    valid_input = True
                except ValidationError as e:
                    print >> sys.stderr, "Invalid input: {}".format(e.message)
                    print >> sys.stderr, "Enter '?' for help".format(e.message)
        
        try:
            computer.store()
        except ValidationError as e:
            print "Unable to store the computer: {}. Exiting...".format(e.message)
            sys.exit(1)
                
        print "Computer '{}' successfully stored in DB.".format(computer_name)
        print "pk={}, uuid={}".format(computer.pk, computer.uuid)
        print "Note: before using it with AiiDA, configure it using the command"
        print "  verdi computer configure {}".format(computer_name)
        print "(Note: machine_dependent transport parameters cannot be set via "
        print "the command-line interface at the moment)"

    def computer_rename(self, *args):
        """
        Rename a computer
        """
        from aiida.common.exceptions import (
            NotExistent, UniquenessError, ValidationError)
        try:
            oldname = args[0]
            newname = args[1]
        except IndexError:
            print >> sys.stderr, "Pass as parameters the old and the new name"
            sys.exit(1)
        
        if oldname == newname:
            print >> sys.stderr, "The initial and final name are the same."
            sys.exit(1)
            
        
        try:
            computer = self.get_computer(name=oldname)
        except NotExistent:
            print >> sys.stderr, "No computer exists with name '{}'".format(
                oldname)
            sys.exit(1)
        
        try:
            computer.set_name(newname)
            computer.store()
        except ValidationError as e:
            print >> sys.stderr, "Invalid input! {}".format(e.message)
            sys.exit(1)
        except UniquenessError as e:
            print >> sys.stderr, ("Uniqueness error encountered! Probably a "
                                  "computer with name '{}' already exists"
                                  "".format(newname))
            print >> sys.stderr, "(Message was: {})".format(e.message)
            sys.exit(1)
        
        print "Computer '{}' renamed to '{}'".format(oldname, newname)

    def computer_configure(self, *args):
        """
        Configure the authentication information for a given computer
        """
        load_django()

        import readline
        import inspect
                
        from django.core.exceptions import ObjectDoesNotExist
        
        from aiida.common.exceptions import (
            NotExistent, ValidationError)
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.models import DbAuthInfo

        if len(args) != 1:
            print >> sys.stderr, ("after 'computer configure' there should be one "
                                  "argument only, being the computer name.")
            sys.exit(1)
        
        computername = args[0]
            
        try:
            computer = self.get_computer(name=computername)
        except NotExistent:
            print >> sys.stderr, "No computer exists with name '{}'".format(
                computername)
            sys.exit(1)

        user = get_automatic_user()
        
        try:
            authinfo = DbAuthInfo.objects.get(
                dbcomputer=computer.dbcomputer, 
                aiidauser=user)
        
            old_authparams = authinfo.get_auth_params()
        except ObjectDoesNotExist:
            authinfo = DbAuthInfo(dbcomputer=computer.dbcomputer, aiidauser=user)
            old_authparams = {}

        Transport = computer.get_transport_class()
        
        print "Computer {} has transport of type {}".format(computername,
                                                            computer.get_transport_type())
        
        valid_keys = Transport.get_valid_auth_params()

        default_authparams = {}
        for k in valid_keys:
            if k in old_authparams:
                default_authparams[k] = old_authparams.pop(k)
        if old_authparams:
            print ("WARNING: the following keys were previously in the "
                   "authorization parameters,")
            print "but have not been recognized and have been deleted:"
            print ", ".join(old_authparams.keys())

        if not valid_keys:
            print "There are no special keys to be configured. Configuration completed."
            authinfo.set_auth_params({})
            authinfo.save()
            return
            
        print ""
        print "Note: to leave a field unconfigured, leave it empty and press [Enter]"
        
        # I strip out the old auth_params that are not among the valid keys
        
        new_authparams = {}
        
        for k in valid_keys:
            key_set = False
            while not key_set:
                try: 
                    converter_name = '_convert_{}_fromstring'.format(k)
                    try:
                        converter = dict(inspect.getmembers(
                            Transport))[converter_name]
                    except KeyError:
                        print >> sys.stderr, ("Internal error! "
                          "No {} defined in Transport {}".format(
                                converter_name, computer.get_transport_type()))
                        sys.exit(1)

                    if k in default_authparams:
                        readline.set_startup_hook(lambda:
                            readline.insert_text(str(default_authparams[k])))
                    else:
                        # Use suggestion only if parameters were not already set
                        suggester_name = '_get_{}_suggestion_string'.format(k)
                        try:
                            suggester = dict(inspect.getmembers(
                                Transport))[suggester_name]
                            suggestion = suggester(computer)
                            readline.set_startup_hook(lambda:
                                readline.insert_text(suggestion))
                        except KeyError:
                            readline.set_startup_hook()
                        

                    txtval = raw_input("=> {} = ".format(k))
                    if txtval:
                        new_authparams[k] = converter(txtval)
                    key_set = True
                except ValidationError as e:
                    print "Error in the inserted value: {}".format(e.message)
                    
        authinfo.set_auth_params(new_authparams)
        authinfo.save()
        print "Configuration stored for your user on computer '{}'.".format(
            computername)

    def computer_delete(self, *args):
        """
        Configure the authentication information for a given computer
        
        Does not delete the computer if there are calculations that are using
        it.
        """
        from aiida.common.exceptions import (
            NotExistent, InvalidOperation)
        from aiida.orm.computer import delete_computer

        if len(args) != 1:
            print >> sys.stderr, ("after 'computer delete' there should be one "
                                  "argument only, being the computer name.")
            sys.exit(1)
        
        computername = args[0]
            
        try:
            computer = self.get_computer(name=computername)
        except NotExistent:
            print >> sys.stderr, "No computer exists with name '{}'".format(
                computername)
            sys.exit(1)
               
        try:
            delete_computer(computer)
        except InvalidOperation as e:
            print >> sys.stderr, e.message       
            sys.exit(1)
         
        print "Computer '{}' deleted.".format(computername)

    def get_computer_names(self):
        """
        Retrieve the list of computers in the DB.
        
        ToDo: use an API or cache the results, sometime it is quite slow!
        """
        from aiida.orm import Computer as AiidaOrmComputer

        load_django()
        return AiidaOrmComputer.list_names()

    def get_computer(self, name):
        """
        Get a Computer object with given name, or raise NotExistent
        """    
        from aiida.orm import Computer as AiidaOrmComputer
        
        load_django()        
        return AiidaOrmComputer.get(name)
    
