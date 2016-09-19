from flask import g
from flask import request
from flask_marshmallow import Marshmallow

from aiida.restapi.api import app
ma = Marshmallow(app)

class McloudUserSchema(ma.ModelSchema):
    class Meta:
        from aiida.restapi.database.models import McloudUser
        model = McloudUser
