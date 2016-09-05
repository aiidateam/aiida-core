from urllib import unquote
from flask import request, jsonify, url_for, g
from flask_restful import Resource

from flask.ext.httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


class McloudUsersResource(Resource):

    def __init__(self):
        self.trans = None

    def get(self, **kwargs):

        from aiida.restapi.database.models import McloudUser
        from aiida.restapi.database.schemas import McloudUserSchema

        user_schema = McloudUserSchema(many=True)
        users = McloudUser.query.all()
        return user_schema.dump(users).data

class McloudUserResource(Resource):

    def __init__(self):
        self.trans = None

    def get(self, pk=None):

        from aiida.restapi.database.models import McloudUser
        from aiida.restapi.database.schemas import McloudUserSchema

        if pk is None:
            return (jsonify({'error': 'pass an id'})) 

        user = McloudUser.query.get(pk)
        if not user:
            return jsonify({'message':  "user with pk=" + str(pk) +" is not exist"})

        user_schema = McloudUserSchema()
        return user_schema.dump(user).data

    def post(self, **kwargs):
        return self.new_user(request)

    def new_user(self, request):

        from aiida.restapi.database.models import McloudUser
        from aiida.restapi.database.schemas import McloudUserSchema
        from aiida.restapi.database.initdb import mcloud_db_session

        first_name = request.json.get('first_name')
        last_name = request.json.get('last_name')
        email = request.json.get('email')
        institute = request.json.get('institute')
        password = request.json.get('password')
        if email is None or password is None:
            return jsonify({ 'errpr': 'email/password is none!'})
            abort(400) # missing arguments

        if McloudUser.query.filter_by(email = email).first() is not None:
            return jsonify({ 'username': email + " already exist"})
        user = McloudUser( first_name=first_name,
                            last_name=last_name,
                            email=email,
                            institute=institute)
        user.hash_password(password)
        mcloud_db_session.add(user)
        mcloud_db_session.commit()

        user_schema = McloudUserSchema()
        return user_schema.dump(user).data
        return jsonify({ 'message': user.email + " added in db"})

class McloudTokenResource(Resource):

    def __init__(self):
        self.trans = None

    @auth.login_required
    def post(self):
        token = g.user.generate_auth_token()
        return jsonify({ 'token': token.decode('ascii') })
