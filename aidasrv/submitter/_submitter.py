def submit_calc(calc_id):
    """Submits a calculation with given ID in the database.
    
    The calculation with all related ForeignKeys and M2M fields
    (as dependencies) must be already correctly set in the database.

    Args:
        calc_id: ID of the calculation in the local database

    Returns:
        ...
    """
    ## TODO: create new table with submitted jobs and unique fields to be
    ## sure that we are submitting the job only once. Possibly with a second
    ## field saying that we entered the submit_calc, or that we actually
    ## submitted it.

    ## Clear directories, if present (past submission failed), and create 
    ## empty new ones.
    ## Folder structure:
    ## AidaRepository/Jobs/Localjobid/
    ##                               /in
    ##                               /out
    ##                               /attachments
    ## DELETE ONLY /in and /out, NOT attachments!!
    ## Define a function (or more than one) to return the different local and
    ## remote locations!

    ## Validate input
    ## (also includes validation of parameter dependencies from parents
    
    ## identify the plugin script (+ version etc.)

    ## Create input file using the correct plugin.
    ## Expected behavior: 
    ## Write files in ./in directory
    ## provide back:
    ## * list of files to retrieve
    ## * the command line parameters
    ## * stdin file or None (or a string: No, better to write in a file and
    ##   use that as stdin, it remains in the repository)
    ## * stdout file or None
    ## * stderr file or None
    ## * pre-exec and post-exec commands?
    
    ## Load the 'signaling' library depending on the current AIDA version.
    ## This in particular provides the signaling strings, to be used later.

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

