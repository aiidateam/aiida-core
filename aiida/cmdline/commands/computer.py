import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

class Computer(VerdiCommand):
    """
    Manage computers to be used.

    This command allows to list, add 
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        start, stop, status and restart.
        """
        self.valid_subcommands = {
            'list': (self.computer_list, self.complete_none),
            'show' : (self.computer_show, self.complete_computers),
            'setup': (self.computer_setup, self.complete_computers),
            'configure': (self.computer_configure, self.complete_computers),
            'delete': (self.computer_delete, self.complete_computers),
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
        
    def complete_computers(self):
        computer_names = self.get_computer_names()
        return "\n".join(computer_names)

    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'computer'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self):
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
        print "\n".join("* {}".format(i) for i in computer_names)
        
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
            print "Modifying existing computer with name '{}'".format(computer_name)
        except NotExistent:
            computer = AiidaOrmComputer(name=computer_name)    
            print "Creating new computer with name '{}'".format(computer_name)
        
        print "At any prompt, type ? to get some help."
        print "---------------------------------------"

        for internal_name, name, desc in AiidaOrmComputer._conf_attributes:

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
                readline.set_startup_hook(lambda: readline.insert_text(
                    previous_value))
                input_txt = raw_input("{}: ".format(name))
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
        
        raise NotImplementedError("mpiruncommand, append/prepend, description, enabled, transport_params, ...")
        ## Moreover, decide a policy when MODIFYING an existing computer. 
        
        print "Computer '{}' successfully stored in DB.".format(computer_name)
        print "pk={}, uuid={}".format(computer.pk, computer.uuid)
        print "Now you can use it with AiiDA."

    def computer_configure(self, *args):
        """
        Configure the authentication information for a given computer
        """
        print >> sys.stderr, "Not implemented yet..."
        sys.exit(1)    

    def computer_delete(self, *args):
        """
        Configure the authentication information for a given computer
        
        Does not delete the computer if there are calculations that are using
        it.
        """
        print >> sys.stderr, "Not implemented yet..."
        sys.exit(1)    


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
    