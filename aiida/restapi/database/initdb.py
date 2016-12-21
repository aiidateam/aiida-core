from aiida.restapi.common.config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True)
mcloud_db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = mcloud_db_session.query_property()

def setup_database():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from aiida.restapi.database.models import McloudUser

    Base.metadata.create_all(bind=engine)

    #create guest user
    email = "guest@mcloud.com"
    password = "guest123"
    first_name = "Guest"
    last_name = "Guest"
    institute = "Unknown"

    if McloudUser.query.filter_by(email = email).first() is None:
        user = McloudUser( first_name=first_name,
                            last_name=last_name,
                            email=email,
                            institute=institute)
        user.hash_password(password)
        mcloud_db_session.add(user)
        mcloud_db_session.commit()
