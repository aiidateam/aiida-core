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
            return (jsonify({'response': 'pass user id'}))

        user = McloudUser.query.get(pk)
        if not user:
            return jsonify({'response':  "user with pk=" + str(pk) +" is not exist"})

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
	    response = jsonify({ 'response': "email/password is empty!"})
            response.status_code = 400
            return response

        if McloudUser.query.filter_by(email = email).first() is not None:
	    response = jsonify({ 'response': email + " is already registered!"})
            response.status_code = 400
            return response

        user = McloudUser( first_name=first_name,
                            last_name=last_name,
                            email=email,
                            institute=institute)
        user.hash_password(password)
        mcloud_db_session.add(user)
        mcloud_db_session.commit()

        user_schema = McloudUserSchema()
        response = jsonify({ 'response': user_schema.dump(user).data})
        response.status_code = 200
        return response

class McloudTokenResource(Resource):

    def __init__(self):
        self.trans = None

    @auth.login_required
    def post(self):
        token = g.user.generate_auth_token()
        return jsonify({ 'response': token.decode('ascii') })

    def get(self):
	email = "guest@mcloud.com"
	from aiida.restapi.database.models import McloudUser
	guest = McloudUser.query.filter_by(email = email).first()

	if guest:
            token = guest.generate_auth_token()
            return jsonify({ 'response': token.decode('ascii') })
	else:
	    response = jsonify({ 'response': " Guest Login Not Available!"})
            response.status_code = 400
            return response


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
            print " => Authentication failed for ", username_or_token, " Password : ", password
            return False
    g.user = user
    return True

@auth.error_handler
def auth_error():
    response = jsonify({ 'response': " Server Authentication Failed!"})
    response.status_code = 403
    return response
