"""
File to be executed by IPython in order to register the line magic %aiida

This file can be put into the startup folder in order to have the line
magic available at startup.
The start up folder is usually at ``.ipython/profile_default/startup/``
"""


if __name__ == "__main__":

    try:
        import aiida
    except ImportError:
        pass
    else:
        import IPython
        from aiida.common.ipython.ipython_magics import load_ipython_extension

        # Get the current Ipython session
        ipython = IPython.get_ipython()

        # Register the line magic
        load_ipython_extension(ipython)
