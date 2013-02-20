"""
This module will contain functions similar to those of os.path or urllib
to get parts of a protocol that will be used internally.

The protocols can be things like:
computer://computername/path [to decide whether absolute or relative to the
    aida_managed folder; to access remote files/folders]
local://abspath [for access to files in the local disk]
repository://relpath [with relative path in the local repository]
...
"""
