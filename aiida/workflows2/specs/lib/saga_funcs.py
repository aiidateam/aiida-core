
import saga, os, subprocess, pipes

# we use a single job service per type
# this is recommended anyway in the saga
# documentation, since a job service can handle
# multiple tasks, and creating a job service is usually
# a (relatively) costly operation. Currently we need
# this because we must be able to get the job service
# associated to a given calc. While the jobs id can be
# stored as strings, job services must be passed as
# objects, and this is problematic since we cannot
# store them as columns. The use of a single job
# service per task type is a workaround for this.
saga_session = None
js_ssh = None
js_sge = None
js_local = None

# get active ssh session (if exists), otherwise
# create a new one
def get_session(username):
    global saga_session
    if saga_session is None:
        # specify the protocol
        ctx = saga.Context("ssh")
        ctx.user_id = username
        saga_session = saga.Session()
        saga_session.add_context(ctx)

    return saga_session

# get active job service of a given type (if exists),
# otherwise create a new one
def get_js(username, host, js_type):
    global js_ssh
    global js_sge
    global js_local

    # used for shell scripts run on a remote computer
    if js_type == "ssh":
        if ((js_ssh is None) or (js_ssh.valid == False)):
            s = get_session(username)
            js_ssh = saga.job.Service("ssh://%s" % host, session=s)

        return js_ssh

    # used for jobs run using a SGE scheduler (i.e., HAL)
    elif js_type == "sge":
        if ((js_sge is None) or (js_sge.valid == False)):
            s = get_session(username)
            js_sge = saga.job.Service("sge+ssh://%s" % host, session=s)

        return js_sge

    # used for jobs run on a local machine: this includes
    # all possible shell script run from terminal
    elif js_type == "local":
        if ((js_local is None) or (js_local.valid == False)):
            js_local = saga.job.Service("fork://localhost")

        return js_local

    else:
        raise Exception("Job Service type not recognized")

def create_dir(username, host, type, dir_path):
    """
    This function checks if a directory already exists. If not, it creates
    it: works both for local and remote directories.
    :param: username and hostname in case of remote directory.
    Type can be either 'local' or 'remote'. dir_path is the full path
    of the directory.
    """
    # check if directory already exists
    def exists_dir(type):
        if type == 'local':
            return os.path.isdir(dir_path)
        elif type == 'remote':
            proc = subprocess.Popen(['ssh', '%s@%s' % (username, host),
                'test -d %s' % pipes.quote(dir_path)])
            proc.wait()
            return proc.returncode == 0
        else:
            raise Exception('Environment type not recognized')

    if type=='local':
        if exists_dir(type) == False:
            os.makedirs(dir_path)

        return

    elif type=='remote':
        try:
            s = get_session(username)
            basedir = saga.filesystem.Directory("sftp://"+host+"/", session=s)

            if exists_dir(type) == False:
                if dir_path.startswith('/'):
                    dir_path = dir_path[1:]
                basedir.make_dir(dir_path)

            basedir.close()

            return

        except saga.SagaException, ex:
            print "An exception occurred: (%s) %s " % (ex.type, (str(ex)))
            print " \n *** Backtrace:\n %s" % ex.traceback
            return

def copy_file(username, host, source, localdir, remotedir, filename):
    """
    This function copies a file between a local and remote destinations.
    :param: username and hostname of the remote cluster, source can be
    either 'local' or 'remote' and specifies where the file is copied from.
    localdir and remotedir are the full paths of the 2 directories, while
    filename is the name of the file (and not the path)
    """

    # allow short-hand for current directory
    if localdir == './' or localdir == '.':
        localdir = os.getcwd()

    try:
        s = get_session(username)

        workdir = saga.filesystem.Directory("sftp://"+host+remotedir, session=s)

        if source == 'remote':
            file_path = "sftp://"+host+remotedir + '/' + filename
        elif source == 'local':
            file_path = "file://localhost" + localdir + '/' + filename
        else:
            raise Exception("Source option not recognized")

        file_saga = saga.filesystem.File(file_path, session=s)

        if source == 'remote':
            workdir.copy(file_saga.get_url(), "file://localhost" + localdir)
        elif source == 'local':
            file_saga.copy(workdir.get_url())
        else:
            raise Exception("Source option not recognized")

        file_saga.close()
        workdir.close()

        return

    except saga.SagaException, ex:
        print "An exception occurred: (%s) %s " % (ex.type, (str(ex)))
        print " \n *** Backtrace:\n %s" % ex.traceback
        return


# general function for a saga job
def run_job_saga(username, host, js_type, executable,
    inputs = [], name = None, project = None, queue = None,
    wall_time_limit = None, total_cpu_count = None, spmd_variation = None,
    workdir = [], outputs = [], errors = []):

    try:
        # the job service to use depends on the task
        js = get_js(username, host, js_type)
        # a container is simply a tool to group
        # different saga jobs together, and analyse
        # their status as a whole. Here more for
        # flexibility, probably the current schema
        # favours one job per work function
        container = saga.job.Container()
        res_list = []

        for i in range(len(inputs)):
            # this contains all the info about the saga job
            jd = saga.job.Description()
            # -N flag for SGE script: job name
            jd.name = name
            # -P flag for SGE script: project name
            jd.project = project
            # -q flag for SGE script: queue
            jd.queue = queue
            # -l flag for SGE script: wall time in minutes
            jd.wall_time_limit = wall_time_limit
            # number of cores to be used
            jd.total_cpu_count = total_cpu_count
            # -pe flag for SGE script, i.e. openmpi
            jd.spmd_variation = spmd_variation
            # -cwd flag for SGE script: working directory
            jd.working_directory = workdir[i] if len(workdir) > 0 else './'
            # command to be executed, usually in the shell
            jd.executable = executable
            # input for the executable (i.e. input filename)
            jd.arguments = [inputs[i]] if len(inputs) > 0 else ['']
            # where the ouput will be stored
            jd.output = outputs[i] if len(outputs) > 0 else 'saga.out'
            # where the error will be stored
            jd.error = errors[i] if len(errors) > 0 else 'saga.err'
            # create job instance from job description
            job = js.create_job(jd)
            # add job to container
            container.add(job)

        return container, js

    except saga.SagaException, ex:
        print "An exception occurred: (%s) %s " % (ex.type, (str(ex)))
        print " \n *** Backtrace:\n %s" % ex.traceback
        return ["Exception"]
