class VerdiCommand(object):
    """
    This command has no documentation yet.
    """
    @property
    def command_name(self):
        return self.__class__.__name__.lower()
    
    def run(*args):
        """
        Method executed when the command is called from the command line.
        """
        print >> sys.stderr, "This command has not been implemented yet"

    def complete(*subargs):
        """
        Method called when the user asks for the bash completion.
        Return a list of valid keywords.
        """
        return []
