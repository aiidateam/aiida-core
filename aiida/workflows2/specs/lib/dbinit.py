from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, aliased, scoped_session
from model_def import *
#from test.nodes.node_model_def import *
import json, os

# this is the path to the configuration file in json format
# assume it is in the same folder as dbinit.py
config_path = os.path.dirname(os.path.realpath(__file__)) + '/config.json'

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# the json contains a dict config with keys for
# database name, username and password, plus
# username and host name for remote cluster like HAL
db_username = config['config']['user_db']
db_password = config['config']['user_pw']
db_name = config['config']['db_name']
hal_host = config['config']['hal_host']
hal_username = config['config']['hal_username']

engine = create_engine("postgresql://%s:%s@localhost:5432/%s" % (db_username, db_password, db_name),
    echo=False, pool_size=20, max_overflow=100)

# we need a scoped session to take care of multithreaded session management
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# create tables in the DB if not already there
Base.metadata.create_all(engine)
