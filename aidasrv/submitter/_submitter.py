import shutil
import sys
import os
import os.path
from aidalib.inputplugins import create_calc_input

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
    # For the moment, if the folder exists, I just stop with a 'random' exception
    # TODO: FIX THIS!
    if os.path.isdir(calc.get_local_dir()):
        raise OSError('The folder {} already exists!'.format(
                calc.get_local_dir()))

    ## Clear directories, if present (past submission failed), and create 
    ## empty new ones.
    ## Folder structure:
    ## AidaRepository/Jobs/Localjobid/
    ##                               /inputs
    ##                               /outputs
    ##                               /attachments
    ## DELETE ONLY /in and /out, NOT attachments!!
    ## Use the calc.get_local_indir() and similar functions

    # Using os.makedirs instead of os.mkdir, this will also create the
    # necessary parent dirs where needed
    for dir_to_del in [calc.get_local_indir(), calc.get_local_outdir()]:
        if os.path.isdir(dir_to_del):
            shutil.rmtree(dir_to_del)
        os.makedirs(dir_to_del)  

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
    (retrieve_output, cmdline_params, stdin, stdout, stderr,
     preexec, postexec) = create_calc_input(
        calc_id=calc.id,infile_dir=calc.get_local_indir())
    
    #print stdin, stdout, stderr

    ## Load the 'signaling' library depending on the current AIDA version.
    ## This in particular provides the signaling strings, to be used later.
    from aidasrv.signaling.signals import get_running_signal, get_finished_signal

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

