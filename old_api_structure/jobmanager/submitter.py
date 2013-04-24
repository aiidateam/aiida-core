from __future__ import print_function
import shutil
import sys
import os
import os.path
from aida.codeplugins import create_calc_input
from aida.repository.utils.files import SandboxFolder

def submit_calc(calc):
    """Submits a given calculation (given as a Calc Django object) of
    the database.
    
    The calculation with all related ForeignKeys and M2M fields
    (as dependencies) must be already correctly set in the database.

    Args:
        calc_id: ID of the calculation in the local database

    Returns:
        ...

    Raises:
        OSError: if it is not able to delete a previous dir, 
    """
    ## TODO: create new table with submitted jobs and unique fields to be
    ## sure that we are submitting the job only once. Possibly with a second
    ## field saying that we entered the submit_calc, or that we actually
    ## submitted it.
    # TODO: FIX THIS!

    ## Folder structure:
    ## AidaRepository/calculations/UUID/
    ##                                 /inputs/
    ##                                 /outputs/
    ##                                 /... (e.g. files with the inputs etc.)
    ## For increased safety, I ask the plugin to write in a Sandbox Folder
    with SandboxFolder() as sandbox:
        ## identify the plugin script (+ version etc.)
        ## Validate input
        ## (also includes validation of parameter dependencies from parents).
        ## See if the above should be done in a separate step, or by the plugin
        ## itself.
        ## Create input file using the correct plugin.
        ## Expected behavior: 
        ## Write files in ./in directory
        ## TODO: evaluate if it is better to return a dictionary in case we
        ## discover that we need to pass more data
        ## To see if this interface is the best one or not (i.e., if we want
        ## to give full access to the input_folder to the input plugin)
        retdict = create_calc_input(calc=calc,
            input_folder=sandbox)

        inputs_folder = calc.get_repo_inputs_folder()
        # For the moment, if the folder exists, I just print a warning and
        # delete the folder (by means of the 'overwrite=True' flag)!!
        if inputs_folder.exists():
            print('The folder {} already exists! I DELETE IT.'.format(
                    input_folder.abspath),file=sys.stderr)
        inputs_folder.replace_with_folder(sandbox.abspath, move=True,
                                         overwrite=True)

    ## Load the 'signaling' library depending on the current AIDA version.
    ## This in particular provides the signaling strings, to be used later.
    from aida.jobmanager.signaling.signals import get_running_signal
    from aida.jobmanager.signaling.signals import get_finished_signal

    ## identify the scheduler script
    ## Call the scheduler script.
    ## Expected behavior:
    ## Write new files in ./in directory
    ##   In particular, it will use the parameters provided by the input plugin
    ##   and the signaling plugin above and also:
    ##   * walltime, number of nodes, ... from calc
    ##   * computer-dependent module load
    ##   * code-dependent module load (which are also implicitly
    ##     computer-dependent)
    ##   * the running/finished signals
    ##   * creates the mpirun + execname + cmdline params + stdin/out/err
    ##     redirection
    
    ## Call the packaging library to prepare a tar.gz

    ## Call the computercommunication library (typically using ssh) to
    ## 1. copy and unpack the tar.gz in a suitable location on the cluster
    ##    (location described in computer; substitute )
    ## 2. Store the new 'queued' status [must be done here, before actually
    ##    queuing, so that if the calculation returns immediately, we don't
    ##    overwrite with 'queued' the 'running' or 'finished' status signaled
    ##    back.
    ## 3. submit the calculation, using the command provided by the scheduler
    ## 4. retrieve the calculation ID using an helper function from the 
    ##    scheduler lib
    ## 5. store in the DB, somewhere (there should be a suitable field I 
    ##    believe) the jobid.
    ## 6. If there was an error in any of the above steps, set the status to
    ##    (finished or) failed.

    pass

