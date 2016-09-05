from flask import g
from flask import request
from flask_marshmallow import Marshmallow

from aiida.restapi.api import app
ma = Marshmallow(app)

class McloudUserSchema(ma.ModelSchema):
    class Meta:
        from aiida.restapi.database.models import McloudUser
        model = McloudUser


from aiida.restapi.database.resources import auth

@auth.verify_password
def verify_password(username_or_token, password):
    from aiida.restapi.database.models import McloudUser

    username_or_token = request.json.get('email')
    password = request.json.get('password')

    # first try to authenticate by token
    user = McloudUser.verify_auth_token(username_or_token)

    if not user:
        # try to authenticate with username/password
        user = McloudUser.query.filter_by(email = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True
