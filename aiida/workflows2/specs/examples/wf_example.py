# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

def wf_check_input(*tuples):
    for arg, type in tuples:
        if not isinstance(arg,type):
            raise Exception("Argument %s is not of type %s" % (arg,type))

    return


@threadit
@workit_factory(code_type=Combine)
def create_PP_set(_calc, code_name=None, **db_PPs):
    """
    This function takes as input a dict of PseudoPot objects, and creates
    a PPSubset object which contains the PseudoPots. Extra links are created
    so that the user can access to the PseudoPots directly from the set. (AG)
    :param: dict of PP DB objects, the code_name allows the user to specify
    an existing code in the database to be linked to this calc by the wrapper.
    """

    uuid_list = []
    chemsys = []

    for el, PP in db_PPs.iteritems():
        # keep track of the UUIDs of the input PPs
        uuid_list.append(str(PP.uuid))
        # check argument types
        wf_check_input((PP, PseudoPot))
        # sanity check to ensure we have a PP consistent with the
        # elements we want
        if el != PP.content['element']:
            raise Exception("Discrepancy between element and PP")
        chemsys.append(el)

    # ensure we have at most one PP for a given element
    if len(chemsys) != len(set(chemsys)):
        raise Exception("Multiple PPs found for the same element")

    name = '_'.join(sorted(chemsys)) + '.pp_set'
    content = {'species': ','.join(sorted(chemsys)), 'PP_uuids': ','.join(sorted(uuid_list))}

    # create new PPSubset; since this is a work function, the existence
    # of a similar PPSubset will be taken care of by the wrapper itself
    # no need to use get or create here
    PP_set = PPSubset(name=name, content=content)

    # create extra links so that we can access the PPs directly from
    # the PP set without having to go through the CombineCalc.
    # These links are not set automatically by the wrapper, hence they
    # must be explicitly set by the user
    PP_set.roots.extend(db_PPs.values())

    return {'ppsubset': PP_set}


@threadit
@workit_factory(code_type=QEplugin)
def import_structures_from_QE_run(_calc, code_name=None, **qeoutputs):
    """
    This function upload Struc objects to the database,
    from a dict of QEOutput Data instances
    :param: a dict of QEOutput Data instances
    :return: a dict of the Struc objects added, {struc_name: Struc DB object}
    """

    cif_list = []

    for key, value in qeoutputs.iteritems():
        # check we are using output of a QE run as input
        wf_check_input((value, QEOutput))

        cif_name = str(value.name.replace('out', 'cif'))
        at = Atoms(positions=value.content['pos_fin'], cell=value.content['cell_fin'])
        at.set_chemical_symbols([str(el) for el in value.content['species']])

        # write to CIF file
        io.write(cif_name, at, format='cif')

        cif_list.append(cif_name)

    struc_list = import_structures_to_db(*cif_list)

    return struc_list


@threadit
@workit_factory(code_type=Manipulator)
def manipulate_struc(_calc, code_name=None, struc=None, transformation=None):
    """
    This function allows to generate a new structure by manipulating
    an already existing one. Manipulation includes randomizing atomic
    positions, apply a strain tensor, build supercells and so on.
    :param: a Struc to manipulate to generate a new one
    :return: dict with newly generated Struc
    """

    wf_check_input((struc, Struc), (transformation, ManipulateStruc))

    cif_name = str(struc.name.replace('out', ''))

    at = Atoms(positions=struc.content['positions'], cell=struc.content['cell'])
    at.set_chemical_symbols([str(el) for el in struc.content['species']])

    supercell_size = transformation.content.get('supercell',[1,1,1])

    at.repeat(supercell_size)

    cif_name += '_supercell_%s' % '_'.join([str(x) for x in supercell_size])

    if 'rattle' in transformation.content:
        stdev = transformation.content['rattle'][0]
        seed = transformation.content['rattle'][1]
        at.rattle(stdev=stdev, seed=seed)
        cif_name += '_rattled_%.5f' % stdev

    strain_tensor = transformation.content.get('strain', [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]])

    at.set_cell(np.dot(np.array(strain_tensor)+np.identity(3), at.cell), scale_atoms=True)

    if np.array_equal(np.array(strain_tensor), np.zeros(3)) == False:
        cif_name += '_strained_%s' % str(strain_tensor)

    cif_name += '.cif'

    io.write(cif_name, at, format='cif')

    struc_list = import_structures_to_db(cif_name)

    return struc_list


@threadit
@workit_factory(code_type=QEplugin)
def create_QEInput_file(_calc, code_name=None, struc=None, qeinp=None, ppsubset=None):
    """
    This function takes as input a dict of DB objects (one Struc, one QEInput, one PP set)
    and creates a QE Input file object which contains the full qe file.
    :param: dict with Struc obejct, PPSubset object, QEInput object; ,
    the code_name allows the user to specify an existing code in the
    database to be linked to this calc by the wrapper.
    :return: dict with the FileData instance created
    """

    wf_check_input((struc, Struc), (qeinp, QEInput), (ppsubset, PPSubset))

    #...cut a lot of code here...

    content = {}
    content['filepath'] = work_dir + "/%s.in" % title
    content['filecontent'] = ss
    content['uuids'] =  ','.join(sorted(uuid_list))

    # create input file for QE calculation
    # if running locally, create the file
    # in the path specified
    if run_on_hal == False:
        fn = open(work_dir + "/%s.in" % title, 'w')
        fn.write(ss)
        fn.close()
    # if running remotely, we need to copy the file to the cluster
    elif run_on_hal == True:
        # create the file locally first in the working directory
        fn = open(os.getcwd()+"/%s.in" % title, 'w')
        fn.write(ss)
        fn.close()
        # create directory on cluster if it doesn't exist yet
        print "Creating directory on cluster...."
        # username and hostname taken from config.json
        create_dir(hal_username, hal_host, 'remote', work_dir)
        print "Done"
        # copy file to cluster
        print "Copying QE input file to cluster...."
        copy_file(hal_username, hal_host, 'local', os.getcwd(), work_dir, "%s.in" % title)
        print "Done"

    fileinp = FileData(name=title+'_input', content=content)

    return {'fileinp': fileinp}


@threadit
@workit_factory(code_type=QEplugin)
def run_QE_calc(_calc, code_name=None, fileinp=None):
    """
    This function takes as input a QE input file DB object: it runs the calculation
    (locally or remotely), then returns a FileData object containing information
    about the output file generated by the calculation. The parsing of the file
    will be done by a separate routine in order to allow for different parsers to
    be used.
    :param: dict with FileData object; the code_name allows the user to specify
    an existing code in the database to be linked to this calc by the wrapper.
    :return: dict with the FileData instance created
    """

    wf_check_input((fileinp, FileData))

    uuid_list = [str(fileinp.uuid)]

    # full path of the raw input file (local or remote)
    filepath = fileinp.content['filepath']
    # extract the filename from full path
    filename = filepath.split('/')[-1]
    # extract seed and working directory from filepath
    seed = filepath.replace('.in', '')
    cwd = '/'.join(seed.split('/')[:-1])

    # ...snip... code

    # create saga job
    container, js = run_job_saga(hal_username,'', 'local', executable,
            inputs = [filepath], name = None, project = None, queue = None,
            wall_time_limit = None, total_cpu_count = None, spmd_variation = None,
            workdir = [cwd], outputs = [seed+'.out'], errors = [seed+'.err'])

    # run the saga job
    container.run()

    # get jobs id
    job_id_list = [job.id for job in container.jobs]

    # store jobs id into content of the calc object in database
    # this is important to leave a handle
    s = Session()
    self_copy = s.merge(self)
    # in case the content field is empty
    if not self_copy.content:
        self_copy.content = {}
    self_copy.content['jobs_id'] = job_id_list
    flag_modified(self_copy, "content")
    s.commit()

    # test: periodically check number of jobs running
    while any([x in running_states for x in container.get_states()]):
        running_jobs = [y for y in container.jobs if y.get_state() in running_states]
        print "Number of running jobs: %d" % len(running_jobs)

        time.sleep(11)

    res_list = []

    # when jobs are finished, get states of the jobs
    # this is important in order to determine if the
    # output will be in a Final or Partial state
    for state in container.get_states():
        if state == saga.job.DONE:
            res_list.append("Finished")
        elif state == saga.job.FAILED:
            res_list.append("Failed")
        elif state == saga.job.CANCELED:
            res_list.append("Canceled")

    print res_list

    content = {}
    content['filepath'] = seed+'.out'
    # currently assuming one job per saga task
    # convention: job finished -> data is final
    # otherwise data is partial
    # validity will be checked automatically by methods invoked by wrapper
    if res_list[0] == "Finished":
        state = "Final"
    else:
        state = "Partial"

    title = seed.split('/')[-1]
    # save FileData object to database; no need to check for duplicates since
    # the wrapper will take care of fast-forwarding if calculation with the same
    # inputs is found in the database
    fileout = FileData(name=title+'_output', state=state, content=content)

    # if calculation is performed on the cluster, copy the file back to local directory
    if run_on_hal == True:
        print "Copying output file from cluster...."
        copy_file(hal_username, hal_host, 'remote', os.getcwd(), cwd, filename.replace('.in', '.out'))
        print "Done"

    return {title: fileout}


@threadit
@workit_factory(code_type=QEparser)
def parsing_QE_output(_calc, code_name=None, struc=None, ppsubset=None,
    parser=None, observed=None):
    """
    This function takes as input a FileData object with the location of the output
    file generated by QE. It then parses the file and store the relevant info into a
    Data object. The use of the code_name allows to specify the parser to be used.
    Currently only parsing using espresso python module is allowed. (AG)
    :param: FileData object created by QE calc
    :return: dict with QEOutput object containing information about parsed QE output.
    TO-DO: implement different parsing options
    """

    wf_check_input((struc, Struc), (ppsubset, PPSubset), (parser, ParserParam),
        (observed, Observed))

    uuid_list = [str(struc.uuid), str(ppsubset.uuid), str(parser.uuid), str(observed.uuid)]

    # currently this is the only parsing option supported
    if parser.name != 'Espresso wrapper by Zhongnan Xu':
        raise Exception("{} not currently supported".format(parser))
    else:
        print "Analyzing QE output with {}".format(parser)

    title = observed.content['filepath'].split('/')[-1]

    if run_on_hal == False:
        seed = observed.content['filepath'].replace('.out','')
    # if calculation is run on cluster, the analysis is performed
    # on the local files that are stored in the current working
    # directory: the output file is copied from cluster at the end
    # of the QE calculation, before parsing takes place
    elif run_on_hal == True:
        seed = os.getcwd() + '/' + title

    content = {}
    dict_PPs = {}

    try:
        # using espresso module with some changes done by me
        # in order to initialise Espresso instance from filename
        e = Espresso(filename=seed)
        # True if calculation is finished
        content['calc_finished'] = e.calc_finished
        # True if calculation convergenced
        content['converged'] = e.converged
        # check for electronic convergence
        content['electronic_converged'] = e.electronic_converged
        content['total_energy'] = e.energy_free
        content['energy_atom'] = e.energy_free/e.int_params['nat']

        # ...snip....
    except:
        # default if file not found and/or other parsing problems
        content['calc_finished'] = False

    res = QEOutput(name=title, content=content)

    return {title: res}


@threadit
@workit_factory(code_type=QEplugin)
def observeQE(_calc, code_name=None, fileinp=None):
    """
    This function is a prototype for an observer calc for QE. It periodically checks
    the calculation output and stops it if something goes wrong according to
    the logic set by the user.
    :param: dict with FileData object; the code_name allows the user to specify
    an existing code in the database to be linked to this calc by the wrapper.
    :return: dict with the Observed instance created
    """

    wf_check_input((fileinp, FileData))

    content = {}

    uuid_list = [str(fileinp.uuid)]

    filepath = fileinp.content['filepath']
    filecontent = fileinp.content['filecontent']

    out_file = filepath.replace('.in', '.out')

    number_of_tries = 0
    # the observer runs the QE calculation, and then periodically looks at it
    # try to submit the saga job a max number of times
    # different threads submitting saga jobs through the same channel
    # may lead to connection errors raised by saga
    while number_of_tries <= max_number_retries:
        try:
            res = run_QE_calc(_calc, code_name='Quantum Espresso 5.1.2 Mac OS X 10.9',
                fileinp=fileinp)
        except:
            number_of_tries += 1
            time.sleep(10)
            continue
        break

    if number_of_tries == max_number_retries:
        raise Exception("Saga job submission failed after %d attempts" % max_number_retries)

    # in threading, res is now a Thread object because we haven't blocked
    # with w4 yet, so we can access the output before the function actually
    # finishes the execution
    # ensures we don't check anymore if the thread finishes without problems
    for key, value in res.iteritems():
        if isinstance(value, threading.Thread) or isinstance(value, multiprocessing.Process):
            thread = value
        else:
            thread = None

    if thread is not None:
        while thread.is_alive():
            # necessary because we need first to wait for the output
            # file to be created, before examining it
            if os.path.isfile(out_file):
                fn = open(out_file, 'r')
                hh = fn.readlines()
                fn.close()
                # dummy prototype for checking: print last 10 lines
                # in production, call the function that does the required
                # checks on the file
                print "Last 10 output lines:\n%s" % "".join(hh[-10:])
                # assume one slave per observer
                slave = _calc.slaves[0]
                slave.kill_itself('gra2pal', '', 'local')
            else:
                print "Waiting for output file to be created....."
            time.sleep(30)

    # get the result only when the thread has finished/has been killed
    final_res = w4(res)

    content['uuids'] =  ','.join(sorted(uuid_list))
    content['filepath'] = out_file

    # TO-DO: maybe change state to Partial according to what happened to
    # the thread. We may have a flag to change the state accordingly
    observer_res = Observed(name='observed', state='Final', content=content)

    return {'observed': observer_res}


@threadit
@workit_factory(code_type=QEplugin)
def QE_workflow(_calc, code_name=None, struc=None,
    qeinp=None, ppsubset=None, parser=None):
    """
    Example of workflow to run an energy calculation in Quantum Espresso. (AG)
    :param: Struc, QEInput, PPSubset, Parser.
    :return: dict with QEOutput, i.e. parsed QE output file
    """

    wf_check_input((struc, Struc), (qeinp, QEInput), (ppsubset, PPSubset), (parser, ParserParam))

    res = w4(create_QEInput_file(_calc, struc=struc, qeinp=qeinp, ppsubset=ppsubset))

    # not observed version
    #out = w4(run_QE_calc(self, code_name='Quantum Espresso 5.1.2 Mac OS X 10.9',
    #            fileinp=fileinp))

    # version with observer
    qe_out = w4(observeQE(_calc, **res))

    observed = qe_out['observed']

    qe_out_parsed = w4(parsing_QE_output(_calc, 'Espresso wrapper by Zhongnan Xu',
        struc=struc, ppsubset=ppsubset, parser=parser, observed=observed))

    # setting up direct links for easier queries
    qe_out_parsed.values()[0].roots.extend([struc, qeinp, ppsubset, parser])

    return qe_out_parsed


# for testing the workflow
if __name__ == "__main__":

    s = Session()
    # retrieve entries that are already in the DB
    # we can have functions that generate this entries automatically
    struc = s.query(Struc).filter(Struc.content['formula'].cast(String) == 'Li3').\
        filter(Struc.name=='Li_C19_coarse_50Ry').first()
    qeinp = s.query(QEInput).filter(QEInput.validity != 'Bad').filter(QEInput.content['control','title'].\
        cast(String) == 'Li_C19_coarse_50Ry_scf').filter(QEInput.content['ions']!=None).first()
    pp = s.query(PseudoPot).filter(PseudoPot.content['element'].cast(String) == 'Li').first()
    parser = s.query(ParserParam).filter(ParserParam.name == 'Espresso wrapper by Zhongnan Xu').first()

    dict_pp = {'Li': pp}

    caller1 = Calc(name='PP set generator')

    res = w4(create_PP_set(caller1, **dict_pp))

    ppsubset = res['ppsubset']

    caller2 = Calc(name='QE_workflow')

    # call the workflow
    res = w4(QE_workflow(caller2, struc=struc, qeinp=qeinp, ppsubset=ppsubset, parser=parser))
    #res = w4(equation_of_state_workflow(caller2, struc=struc, ppsubset=ppsubset, parser=parser))

    s.close()

    # explicitly close the job service (should be closed
    # automatically by saga anyway)
    close_js(hal_username, '', 'local')