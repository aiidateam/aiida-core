from sqlalchemy import Column, Integer, String, Boolean
from aiida.restapi.database.initdb import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer)
    is_enabled = Column(Boolean(), nullable=False, default=False)
    email = Column(String(255), nullable=False, primary_key=True)
    password = Column(String(255), nullable=False, default='')

    # Extra model fields
    first_name = Column(String(50), nullable=False, default='')
    last_name  = Column(String(50), nullable=False, default='')
    institute  = Column(String(50), nullable=False, default='')
    authenticated = Column(Boolean, default=False)

    def __repr__(self):
        return '<User %r %r>' % (self.first_name, self.last_name)

    def is_enabled(self):
        """True, as all users are active."""
        return self.is_enabled

    def get_email(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

