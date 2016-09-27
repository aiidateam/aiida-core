from sqlalchemy import Column, Integer, String, Boolean
from aiida.restapi.database.initdb import Base
from passlib.apps import custom_app_context as pwd_context
from passlib.apps import custom_app_context as pwd_context
from aiida.restapi.common.config import SECRET_KEY
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

class McloudUser(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    is_enabled = Column(Boolean(), nullable=False, default=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False, default='')
    password_hash = Column(String(128), nullable=False, default=False)

    # Extra model fields
    first_name = Column(String(50), nullable=False, default='')
    last_name  = Column(String(50), nullable=False, default='')
    institute  = Column(String(50), nullable=False, default='')
    authenticated = Column(Boolean, default=False)

    def __repr__(self):
        return '<McloudUser %r %r>' % (self.first_name, self.last_name)

    def is_enabled(self):
        """True, as all users are active."""
        return self.is_enabled

    def get_email(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=3600):
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'email': self.email})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = McloudUser.query.filter_by(email = data['email']).first()
        return user

