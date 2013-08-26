class VerdiCommand(object):
    """
    This command has no documentation yet.
    """
    @classmethod
    def get_command_name(cls):
        """
        Return the name of the verdi command associated to this
        class. By default, the lower-case version of the class name.
        """
        return cls.__name__.lower()
    
    def run(self,*args):
        """
        Method executed when the command is called from the command line.
        """
        import sys
        
        print >> sys.stderr, "This command has not been implemented yet"

    def complete(self, subargs_idx, subargs):
        """
        Method called when the user asks for the bash completion.
        Print a list of valid keywords.
        Returning without printing will use standard bash completion.
        
        subargs_idx: the index of the subargs where the TAB key was pressed
            (0 is the first element of subargs)
        subargs: a list of subarguments to this command
        """
        return
