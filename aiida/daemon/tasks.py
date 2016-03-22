
"""
Works only with sqlalchemy, not django 
(though in principle it should, some setting issue)


runs with celery worker -A tasks -l INFO --beat

my CONFFILE for supervisord:


[unix_http_server]
file=/home/kahle/temp/log/supervisord.sock   ; (the path to the socket file)

[supervisord]
logfile=/home/kahle/temp/log/supervisord.log
logfile_maxbytes=10MB
logfile_backups=2
loglevel=info
pidfile=/home/kahle/temp/log/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:////home/kahle//temp/log/supervisord.sock

; ==================================
;  celery worker supervisor example
; ==================================

[program:celery]
; Set full path to celery program if using virtualenv
command=celery worker -A manage --loglevel=INFO --beat
directory=/home/kahle/git/aiida_scripts
user=kahle
numprocs=1
stdout_logfile=/home/kahle/temp/log/aiida_daemon.log
stderr_logfile=/home/kahle/temp/log/aiida_daemon.log
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; When resorting to send SIGKILL to the program to terminate it
; send SIGKILL to its whole process group instead,
; taking care of its children as well.
killasgroup=true

; Set Celery priority higher than default (999)
; so, if rabbitmq is supervised, it will start first.
priority=1000



"""

from celery import Celery
from celery.task import periodic_task

from datetime import timedelta

from aiida.backends import settings
from aiida.backends.utils import load_dbenv
load_dbenv(process="daemon")



from aiida.common.setup import get_profile_config
from aiida.common.exceptions import ConfigurationError


#~ from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO

from aiida.daemon.timestamps import set_daemon_timestamp




DAEMON_INTERVALS_SUBMIT = 30
DAEMON_INTERVALS_RETRIEVE = 30
DAEMON_INTERVALS_UPDATE = 30
DAEMON_INTERVALS_WFSTEP = 30


config = get_profile_config(settings.AIIDADB_PROFILE)

engine = config["AIIDADB_ENGINE"]

# defining the broker.
# So far I am using SA for that, but we should totally 
# think about using redis or rabbitmq, which is now possibly
# since now it is decoupled from a backend
# one would simply substitute the broker with whatever the user wants...

if engine == "sqlite3":
    broker = (
        "sqla+sqlite:///{AIIDADB_NAME}"
        ).format(**config)
elif engine.startswith("postgre"):
    broker = (
        "sqla+postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
        "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}"
        ).format(**config)
else: 
    raise ConfigurationError("Unknown DB engine: {}".format(
            engine))


app = Celery('tasks', broker=broker)

# the tasks as taken from the djsite.db.tasks, same tasks and same functionalities
# will now of course fail because set_daemon_timestep has not be implementd for SA

@periodic_task(
        run_every=timedelta(
                seconds=config.get(
                        "DAEMON_INTERVALS_SUBMIT",
                        DAEMON_INTERVALS_SUBMIT
                )
        )
)
def submitter():
    from aiida.daemon.execmanager import submit_jobs
    print "aiida.daemon.tasks.submitter:  Checking for calculations to submit"
    set_daemon_timestamp(task_name='submitter', when='start')
    submit_jobs()
    set_daemon_timestamp(task_name='submitter', when='stop')


@periodic_task(
        run_every=timedelta(
                seconds=config.get(
                        "DAEMON_INTERVALS_UPDATE",
                        DAEMON_INTERVALS_UPDATE
                )
        )
)
def updater():
    from aiida.daemon.execmanager import update_jobs
    print "aiida.daemon.tasks.update:  Checking for calculations to update"
    set_daemon_timestamp(task_name='updater', when='start')
    update_jobs()
    set_daemon_timestamp(task_name='updater', when='stop')


@periodic_task(
        run_every=timedelta(
                seconds=config.get(
                        "DAEMON_INTERVALS_RETRIEVE",
                        DAEMON_INTERVALS_RETRIEVE
                )
        )
)
def retriever():
    from aiida.daemon.execmanager import retrieve_jobs
    print "aiida.daemon.tasks.retrieve:  Checking for calculations to retrieve"
    set_daemon_timestamp(task_name='retriever', when='start')
    retrieve_jobs()
    set_daemon_timestamp(task_name='retriever', when='stop')


#~ @periodic_task(
        #~ run_every=timedelta(
                #~ seconds=config.get(
                        #~ "DAEMON_INTERVALS_WFSTEP",
                        #~ DAEMON_INTERVALS_WFSTEP
                #~ )
        #~ )
#~ )
#~ def workflow_stepper():
    #~ from aiida.daemon.workflowmanager import daemon_main_loop
    #~ print "aiida.daemon.tasks.workflowmanager:  Checking for workflows to manage"
    #~ set_daemon_timestamp(task_name='workflow', when='start')
    #~ daemon_main_loop()
    #~ set_daemon_timestamp(task_name='workflow', when='stop')
