from sqlalchemy import inspect as sa_inspect
import threading, Queue, multiprocessing, time
import inspect, hashlib, pickle, json
from sqlalchemy.orm import sessionmaker, aliased, scoped_session
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm.util import object_state
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from functools import wraps
from subtypes import *


########################  WORK FUNCTIONS #################################
def workit_factory(code_type=Code, wrapped=True):
    """
    This is a wrapper generator: it takes as decorator argument one of the DB types defined in the model,
    and returns a wrapper that will create a calc instance of the correct type. This is not necessary
    but useful to make queries more efficient.

    :param: code_type = one of the DB code classes defined in the model
    wrapped = if False, do not wrap the function with DB operations. This option
    allows the user to run bare work functions without relying on an underlying DB.
    :return: a wrapper
    """
    # I changed this to check if it's a subclass and not an instance, because I guess
    # we pass the class directly to the wrapper generator (AG)
    if not issubclass(code_type, Code):
         raise Exception("Workfunction decorator must take a Code class as argument")

    else:
        def workit(func):
            """
            First level wrapper that takes care of creating the necessary links,
            plus stores objects in the database accordingly. The wrapper tries
            to take care of DB transactions so that the user doesn't have to worry
            about them

            :param: func = user defined work function
            :return: wrapped work function
            """
            def wrapper(caller=None, code_name=None, *args, **kwargs):
                """

                :param caller: master calc that caller this work function
                :param code_name: optional argument that allows the user to specify
                an external code instance by its unique name (already in DB). If not specified, the wrapper will assume
                it's an internal python function: it will then look it up in the database (using code hash) and, if not present,
                will create a new instance. We keep track of function with the same name but
                different source code (because of updates, changes, formatting, etc...) by
                incrementing version of the code name.
                :param args: should not be used really to keep the API standard, since these have no labels.
                :param kwargs: dict of data objects used as inputs for the work function
                :return: results of the user-defined work function
                """

                if args:
                    raise Exception("Unlabeled positional args not allowed")

                #create a database session for this thread
                session = Session()

                #There
                if caller:
                    # check if caller is in detached state. Caller should always live in a different thread.
                    # TODO consider removing this check
                    if isinstance(caller, Calc):
                        if sa_inspect(caller).session == 0:
                            raise Exception("Caller attached to this thread")
                        else:
                            # need to create thread-local copy, since there may be multiple slaves simultaneously changing it
                            caller = session.merge(caller)
                    else:
                        raise Exception("Not a workfunction calc caller")

                # check if the function is a registered code object, only on the first call. If yes, get the code object,
                # and if not then register it. If already registered and synced with db, get the code object.
                # uncommenting this for the moment (AG)
                #if 'db_code_id' in func.__dict__.keys():
                #    # we query only for the required Code subclass (AG)
                #    func_code = session.query(code_type).get(func.func_code_id)
                # if the code_name is specified, retrieve the code instance from database.
                # the name MUST be unique otherwise things would be messy
                if code_name:
                    # error if code has not been registered, or if multiple codes with the same name
                    # have been registered. We require codes to be uniquely identified by their name
                    code_inst = session.query(code_type).filter(code_type.name==code_name).one()
                    # each code is associated to one and only computer. Binaries compiled on different computers
                    # will be registered as dfferent code instances. For external codes, the user must take care
                    # to associate them to the correct computer instance in the database before using them
                    comp_inst = session.query(Computer).filter(Computer.id==code_inst.computer_id).one()
                # if name not provided, assume it's a standard python function
                else:
                    code_inst = code_register(session, func, code_type)
                    try:
                        # if the function was previously registered, retrieve the computer associated to it
                        comp_inst = session.query(Computer).filter(Computer.id==code_inst.computer_id).one()
                    except:
                        # in this case function is a python function, hence assume we run it on local machine
                        # create computer instance trying to load info from json config file
                        # if info not found, use some default values/None
                        # TODO clean up here
                        with open(config_path, 'r') as config_file:
                            config = json.load(config_file)

                        comp_content = {}
                        comp_content['os'] = config['config'].get('computer_os')
                        comp_content['ncpus'] = config['config'].get('computer_cores')
                        comp_name = config['config'].get('computer_name', 'local_machine')
                        # reuse existing computer instance if already in the database
                        comp_inst, new_comp = get_or_create(session, Computer,
                            name=comp_name, content=comp_content)
                        # link computer to code
                        code_inst.computer = comp_inst

                # links will be automatically added in the commit
                session.add(code_inst)
                session.commit()

                # associate code to function
                func.func_code_id = code_inst.id

                # check if inputs are valid. If they are new, register them as caller's output.
                #inputs = kwargs

                # check if all kwargs are valid data objects. Empty list of inputs is ok.
                # By the time the wfunc is called, data objects must be already in the db, but should be detached.
                # If inputs are transient, the only possibility is that the caller calc created them from scratch.

                # check inputs are valid DB Data objects
                # also check they are in detached state
                for key, value in kwargs.iteritems():
                    if isinstance(value, Data):
                        if sa_inspect(value).session == 0:
                            raise Exception("Input attached")
                        #value = session.merge(value)
                    # only DB objects can be used as inputs for a workfunction
                    elif isinstance(value, threading.Thread):
                            raise Exception("Remember to pull results from queue")
                    else:
                        raise Exception("Not valid data inputs")

                # we need to check if inputs are newly made or existing, and if newly made and there is a possibility to
                # reuse a calc, then they should not be persisted. If the inputs are new and have the same hash, skip.

                # To each Code subclass is associated a particular Calc subclass
                # Here we ensure consistency using a defined Code-Calc mapping (AG)
                q_calc = session.query(code_calc_map[code_type]).\
                    filter(code_calc_map[code_type].code_id == code_inst.id).\
                    filter(code_calc_map[code_type].state=="Finished")

                # look if a calculation with exactly the same input is already
                # present in the database
                # first select calculations having the required inputs
                hashes = []
                for key, value in kwargs.iteritems():
                    q_calc = q_calc.filter(code_calc_map[code_type].inputs.\
                    any(Data.hash==value.hash))
                    hashes.append(value.hash)
                # now remove calcs that have extra inputs on top of the required ones
                q_calc = q_calc.filter(~code_calc_map[code_type].inputs.any(~Data.hash.in_(hashes)))
                # there can be several of these, because we may reuse
                # computed results multiple times
                similar_calc = q_calc.first()

                # only finished calculations producing final data can be reused
                if similar_calc and allow_restarts and similar_calc.state == 'Finished':
                    # TODO check if code slaves have changed
                    code_check(func, session)
                    # same or identical data were already used as input to the same code
                    # print info about the user so we know who executed it
                    print 'Reusing {} computed by {} with old args {}'.format(code_inst, similar_calc.user, kwargs)
                    this_calc = similar_calc
                    # connect previous results to calc
                    result_copy = {}
                    for key, value in enumerate(similar_calc.outputs):
                        result_copy[str(key+1)] = session.merge(value)
                    if caller:
                        this_calc.masters.append(caller)
                    session.commit()
                    #session.close()
                else:
                    # nothing to reuse based on content search, we have to compute
                    # create a calc and pass it as first arg, so that callee knows who called
                    # the calc class is determined by the mapping, i.e. by the code class used
                    # as argument for the wrapper generator
                    this_calc = code_calc_map[code_type](code=code_inst, state="Created",
                        name=func.__name__)

                    # create or retrieve user: user details are taken from config json file
                    # if no details found use default values/None
                    with open(config_path, 'r') as config_file:
                        config = json.load(config_file)

                    user_content = {}
                    user_content['affiliation'] = config['config'].get('user_affiliation')
                    user_content['e-mail'] = config['config'].get('user_e-mail')
                    user_name = config['config'].get('user_name', 'unknown')
                    # reuse existing user instance if already in the database
                    user_inst, new_user = get_or_create(session, User,
                        name=user_name, content=user_content)
                    # link calc to user
                    this_calc.user = user_inst

                    kwargs_copy = {}
                    for key, value in kwargs.iteritems():
                        # create a thread-local copy since multiple funcs may operate on it
                        value_copy = session.merge(value)
                        this_calc.inputs.append(value_copy)
                        # we don't have parent any more, hence check for givers (AG)
                        if caller and not value_copy.givers.first():
                            value_copy.givers.append(caller)
                            #print value_copy
                        kwargs_copy[key] = value_copy

                    # all inputs are also added by ref
                    session.add(this_calc)
                    this_calc.state = "Started"
                    if caller:
                        this_calc.masters.append(caller)

                    print '{}: computing {} with args {}'.format(user_inst, code_inst, kwargs_copy)
                    session.commit()
                    #session.close()

                    #if the session is open during the execution, user has access to inputs
                    # TODO figure out why leaving session open creates problems in threads
                    # this is the main trick to make work function self-aware
                    # at this stage the code name is defaulted to None, hence the code info can
                    # be used by the wrapper but not directly by the wrapped function. We may
                    # consider to use the code name in this call as well, so we have access to
                    # the code instance from within the function body.
                    result = func(this_calc, **kwargs_copy)

                    #session = Session()
                    this_calc = session.merge(this_calc)
                    result_copy = {}
                    if result:
                        # check results are in the correct format
                        if not isinstance(result, dict):
                            raise Exception("Outputs should be dicts with Data object values")
                        for key, value in result.iteritems():
                            if isinstance(value, Data):
                                if sa_inspect(value).session == 0:
                                    raise Exception("Result attached")
                                value_copy = session.merge(value)
                                # if no parent yet, then it is a fresh output of this calc.
                                # so we don't allow for the same data to have multiple
                                # parents
                                if not value_copy.givers.first():
                                    this_calc.outputs.append(value_copy)
                                #print value.id, value, value.parent
                                #print value_copy.id, value_copy, value_copy.parent
                                result_copy[key] = value_copy
                            else:
                                raise Exception("Not valid data outputs")
                    this_calc.state = "Finished"

                    session.commit()
                    #session.close()
                    # if session is not closed before results are returned, user has access to results
                return result_copy

            # attributes to keep track of the original function (not wrapped)
            # and the code class associated to it
            wrapper._original = func
            wrapper._dbtype = code_type

            if wrapped == True:
                return wrapper
            else:
                return func

        return workit


# this function looks in the database if a similar object already exists:
# if yes, return that object, otherwise create it from scratch
# useful to check for example if a PseudoPotential has already been
# inserted into the database, without having unnecessary duplicates
def get_or_create(session, model, **kwargs):
    # here we lock the database in order to avoid possible concurrent queries
    # when same types of objects are retrieved/created in concurrent
    # threads / processes
    instance = session.query(model).with_for_update(read=True, of=model).\
        filter_by(**kwargs).first()
    if instance:
        return instance, False

    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance, True

# mapping between code and calc class. This is required in order
# for the wrapper to be able to create a calc of the right class,
# according to code class passed as argument to the wrapper
# generator
code_calc_map = {Code: Calc, QEplugin: QECalc, Combine: CombineCalc,
    QEparser: ParserCalc, Manipulator: ManipulateCalc, Filter: FilterCalc,
    HullAnalysis: HullCalc, StabilityWorkflow: StabilityCalc}

# create a Session for the top-level execution
# TODO check if this is needed
#session = Session()
#print session

# create a Session
#session = Session()

# initialize global variable for thread count
# useful to keep track of what thread is doing what,
# mainly for testing purposes
count = 0

# if True, check if a similar calculation (i.e. same class, same inputs,ecc...)
# has already been performed and stored in the database. If yes,
# fast-forward to the result. Useful to restart workflows and reuse
# already computed objects
allow_restarts = True

# specify threading option with a string
# probably a good idea to store default
# threading options in separate files
# current options:
# celery, py-threading, py-multiprocs
allow_threads = ''

# load the module containing the celery tasks
# the tasks must follow the convention of
# being named as work_function_name + '_task'
if allow_threads == 'celery':
    import scratch.celery_tasks


def code_register(session, func, code_type):
    """
    Given a function, locate its db record or create it.
    This function is essentially used only for python functions, since the use of
    external codes like Quantum Espresso, requires the user to explicitly create
    the code instance in the database before using it in a workflow. The user
    in that case must specify exactly which instance to associate to the calc. This is
    required to give the user freedom to choose which QE version to run a calculation
    with. Furthermore, the user can further differentiate between different builds of the
    same binary (libraries, compilers, ecc...) useful in development stages.
    :param func: The input workfunction to be registered or located
    :return: SA code object for this wfunc
    """
    source = inspect.getsource(func)
    path = inspect.getfile(func)
    #sourcehash = hashlib.sha224(str(source)).hexdigest()
    #cereal = pickle.dumps(func)
    name = func.__name__
    content = {'source': source, 'path': path}
    func_hash = hashlib.sha224(str(content)).hexdigest()
    # first filter DB code instances having function name in the name, and order them
    # from most to least recent
    query_code = session.query(code_type).filter(code_type.name.contains(name)).\
        order_by(desc(code_type.time))
    # then look if we have already a code with same source and location
    new_query_code = query_code.filter(code_type.hash==func_hash)
    # if we find it, simply retrieve it from the database
    if new_query_code.all():
        # make sure we have unique codes identified by unique names and source content
        code_inst = new_query_code.one()
        code_is_new = False
    # if not, create new instance with the source, the name is given by func_name + incremental version
    else:
        # if there are no previous versions of this code func
        if not query_code.all():
            last_version = 0
        else:
            # convention: the version number is stored after the last underscore
            # in the name of the DB code instance: example -> my_func__whatever____235
            # the most recent result in the previous query is the code function with the
            # largest version number currently in the database
            # here we take care of the possibility of codes associated to a given python function,
            # that are present in the database but do not have a version number associated to it
            # in the production database this should not be allowed to happen
            try:
                last_version = int(query_code.all()[0].name.split('_')[-1])
            except:
                last_version = 0
        # increment version number and store it in the name of the DB code object
        code_name = name + '_%d' % (last_version+1)
        # create code instance with right name and content
        # hash will be done automatically in __init__ method
        code_inst = code_type(name=code_name, content=content)
        code_is_new = True
    return code_inst


def code_check(session, mywf):
    """
    Check for code changes. For now assume codes are immutable, othewise renamed after every change
    For a calc that is reused or restarted with a given set of inputs, we need to check if all the callees/slaves
    that the calc invoked, are still valid. The common issue is that the user will change some slave python wfuncs,
    but not the top-level code, so the simple hash of master source will not detect the change. Here we need to descend
    through the entire tree of calls and check the code hashes. Since we do not know the master wfunc logic, the only
    safe thing to do is to rerun the whole calc that is about to be reused. It is safe to reuse only the calcs down the
    call line from the corruption.

    :param session:
    :param mywf:
    :return:
    """
    pass

def extract_uuid_from_db(*args, **kwargs):
    """
    This function takes care of converting DB objects to their respective UUIDs. The function
    checks if the objects are already in the database. If not, the objects are added to the database
    and the UUIDs are retrieved. I wrote this function with the original purpose of allowing
    threading with celery: it can probably be adapt to other uses if necessary (AG)

    :param args: arguments of wrapped work function
    :param kwargs: keyword arguments of the wrapped work function
    :return: UUIDs associated to the arguments and keyword arguments (DB objects)
    """
    uuid_args = []
    uuid_kwargs = {}
    session = Session()
    for i in args:
        if i.uuid is not None:
            arg_uuid = i.uuid
        else:
            session.add(i)
            session.commit()
            arg_uuid = i.uuid

        uuid_args.append(arg_uuid)

    for key, value in kwargs.iteritems():
        if value.uuid is not None:
            value_uuid = value.uuid
        else:
            session.add(value)
            session.commit()
            value_uuid = value.uuid

        uuid_kwargs[key] = value_uuid

    session.close()

    return uuid_args, uuid_kwargs

def extract_entry_from_db(uuid, type):
    """
    This function takes care of extracting an object from the database given its UUID.
    Written to convert output of a celery task back to actual DB objects. (AG)
    """
    session = Session()
    if type == 'data':
        q = session.query(Data).filter(Data.uuid==uuid)
    elif type == 'calc':
        q = session.query(Calc).filter(Calc.uuid==uuid)
    else:
        print "DB Type not recognized"
        return -3
    try:
        entry = q.one()
        session.close()
        return entry
    except MultipleResultsFound:
        print "Error: multiple entries found with same uuid"
        session.close()
        return -2
    except NoResultFound:
        print "Error: no entries found for this uuid"
        session.close()
        return -1

#########################  THREADING #########################

# customised class based on Thread python class
# it takes as argument a given wrapped function (with its
# args and kwargs), and execute it in a separate thread. The
# result is put into a queue, so it can be retrieved (also useful
# to enforce blocking, i.e. consequentiality)
class myThread (threading.Thread):
    def __init__(self, threadID, name, func, que, args, kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.threadID = threadID
        self.name = name
        # the wrapped workfunction to be executed
        self.func = func
        # args and kwargs of the workfunction
        self.args = args
        self.kwargs = kwargs
        # the queue where we put the result
        self.result = que
    # this method is executed when we start the Thread instance
    def run(self):
        print "Starting " + self.name
        self.result.put(self.func(*self.args, **self.kwargs))
        print "Exiting " + self.name

# similar to Threading, but using multiprocessing
class myProcess (multiprocessing.Process):
    def __init__(self, processID, name, func, que, args, kwargs):
        multiprocessing.Process.__init__(self)
        self.daemon = False
        self.processID = processID
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = que
    def run(self):
        print "Starting " + self.name
        self.result.put(self.func(*self.args, **self.kwargs))
        print "Exiting " + self.name

def threadit(func):
    """
    Threading decorator for asynchronous execution of work functions.
    The decorator performs different actions according to the threading
    option specified. Currently supports python threading, python multiprocessing,
    celery threading (AG)
    TODO: Consider updating this with 'concurrent.futures' module of Python 3.2+
    :param func: the work function
    :return: threading-wrapped work function
    """

    def threading_wrap(*args, **kwargs):
        """
        this is the function returned from the decorator, it fires off
        wrapped_func in a new thread and returns the thread object with
        the result queue attached
        """
        # global variable to keep track of the number of threads
        global count
        que = Queue.Queue()
        count += 1
        thread_obj = myThread(count, 'Thread-%d' % count, func=func, que=que,
            args=args, kwargs=kwargs)
        # this will execute the run method in the myThread class
        thread_obj.start()
        return {thread_obj.name: thread_obj}

    def multiprocs_wrap(*args, **kwargs):
        """
        this is the function returned from the decorator, it fires off
        wrapped_func in a new thread and returns the thread object with
        the result queue attached
        N.B.: with multiprocessing we need to introduce a database lock
        in order to avoid problems of concurrent accesses to the database.
        This issue is not present when using Threading (AG)
        """
        global count
        que = multiprocessing.Queue()
        count += 1
        process_obj = myProcess(count, 'Process-%d' % count, func=func, que=que,
            args=args, kwargs=kwargs)
        process_obj.start()
        return {process_obj.name:process_obj}

    def celery_wrap(*args, **kwargs):
        """
        Wrapper for celery threading. The DB objects are first converted to the respective
        UUIDs, that can be used as arguments for the Celery Task. The result of the celery
        task is a dict of UUIDs associated to the output of the work function.
        """
        # find the associated task in the celery task module
        task_name = func._original.__name__ + '_task'
        celery_task = getattr(scratch.celery_tasks, task_name)
        # need to convert to UUIDs to pass as arguments to the task
        copy_args, copy_kwargs = extract_uuid_from_db(*args, **kwargs)
        # this will usually be a dict of UUIDs
        res = celery_task.delay(*copy_args, **copy_kwargs)

        return {'celery_result': res}

    # return threaded version or standard one
    if allow_threads == "py-threading":
        # keep track of wrapped non-threaded function
        threading_wrap._original = func
        return threading_wrap
    elif allow_threads == "py-multiprocs":
        multiprocs_wrap._original = func
        return multiprocs_wrap
    elif allow_threads == "celery":
        # we need to call the first-level wrapped function
        # in the celery task, otherwise we would have an
        # infinite loop as a celery task calls a infinite series
        # of nested celery tasks
        celery_wrap._original = func
        return celery_wrap
    else:
        # do nothing if single-thread version is used
        return func


def w4(item, session=None):
    """
    wait for the result to be computed, blocking
    the optional session argument allows to put the
    result in a given session opened by the user
    :param: the item, i.e. the output to wait for
    :return: the actual output of the work function
    """
    if (allow_threads == "py-threading") or (allow_threads == 'py-multiprocs'):
        # Queue item is pulled and evaluated. This is blocking until the result is obtained
        # evaluate result = wait for process to finish
        for key, value in item.iteritems():
            if isinstance(value, threading.Thread) or isinstance(value, multiprocessing.Process):
                obj = value

        result = obj.result.get()
        # Indicate that a formerly enqueued task is complete
        if allow_threads == 'py-threading':
            # good idea to call task_done() on each finished Queue
            obj.result.task_done()
        elif allow_threads == 'py-multiprocs':
            obj.result.close()
        if session is not None:
            s = session
        else:
            s = Session()
        result_copy = {}
        for key, value in result.iteritems():
            result_copy[key] = s.merge(value)
        return result_copy
    elif allow_threads == "celery":
        # wait for the result to finish
        for key, value in item.iteritems():
            if key == 'celery_result':
                obj = value
        result = obj.get()
        db_result = {}
        # convert the UUIDs back to actual DB objects
        for key, value in result.iteritems():
            db_result[key] = extract_entry_from_db(value, 'data')
            if ((db_result[key] == -2) or (db_result[key] == -1)):
                print "DB entry not found!"
                return 1
        # return the actual DB objects
        if session is not None:
            s = session
        else:
            s = Session()
        db_result_copy = {}
        for key, value in db_result.iteritems():
            db_result_copy[key] = s.merge(value)
        return db_result_copy
    else:
        # do nothing if single-thread version is used
        result = item
        if session is not None:
            s = session
        else:
            s = Session()
        result_copy = {}
        for key, value in result.iteritems():
            result_copy[key] = s.merge(value)
        return result_copy


################# UTILS ##################
from contextlib import contextmanager

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

'''
# for scoped-session
"""@contextmanager
def get_db_session():
    try:
        yield session
    finally:
        session.remove()

with get_db_session():
    # do something"""
    # do something
    pass

'''

def sa_state(item):
    if sa_inspect(item).transient:
        return " Transient "
    if sa_inspect(item).pending:
        return " Pending "
    if sa_inspect(item).persistent:
        return " Persistent "
    if sa_inspect(item).detached:
        return " Detached "


#################### Junk #####################
