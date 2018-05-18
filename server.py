#!flask/bin/python

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

from flask import Flask, jsonify, abort, make_response, url_for
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth
import logging
import hashlib
import db
import http

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(user, password):
    """
    Verifies a user/password combintation by SHA2-512 hashing the supplied password and comparing
    against the value stored in the backend DB.
    :param user: user name (e.g. tim)
    :param password: password (e.g. swordfish123)
    :return: True if matches, else False
    """
    logging.debug("verify_password passed user='{}' ; password='{}'".format(user, password))
    dbhash = db.GetHashedPassword(user)
    if dbhash:
        newhash = hashlib.sha512()
        newhash.update(password.encode())
        return newhash.hexdigest().upper() == dbhash.upper()
    return False



@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), http.HTTPStatus.FORBIDDEN.value)

#---servers-------------------------------------------------------------------------------------------

server_fields = {
    'tag':     fields.String,
    'sid':     fields.Integer,
    'stockid': fields.Integer,
    'comment': fields.String,
    'uri':     fields.Url('server')
}

class ServerListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tag',    type=str, required=True, help='No service tag provided', location='json')
        self.reqparse.add_argument('sid',    type=int, required=True, help='No service ID provided', location='json')
        self.reqparse.add_argument('stockid',type=int, required=True, help='No stock ID provided', location='json')
        self.reqparse.add_argument('comment',type=str, location='json')
        super(ServerListAPI, self).__init__()

    def get(self):
        logging.debug("Getting server list...")
        return {'server': [marshal(server, server_fields) for server in db.GetServers()]}

    def post(self):
        args = self.reqparse.parse_args()
        server = {
            'tag': args['tag'],
            'sid': args['sid'],
            'stockid': args['stockid'],
            'comment': args['comment']
        }
        updated = db.CreateServer(server)
        logging.debug("Got {}".format(updated))
        if 'id' in updated:
            return {'server': marshal(updated, server_fields)}, http.HTTPStatus.CREATED.value
        else:
            abort(http.HTTPStatus.CONFLICT.value)

class ServerAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tag', type=str, location='json')
        self.reqparse.add_argument('sid', type=int, location='json')
        self.reqparse.add_argument('stockid', type=int, location='json')
        self.reqparse.add_argument('comment',type=str, location='json')
        super(ServerAPI, self).__init__()

    def get(self, id):
        server = db.GetServer(id)
        if server:
            return {'server': marshal(server, server_fields)}
        else:
            abort(404)

    def delete(self, id):
        if db.DeleteServer(id):
            return '', http.HTTPStatus.OK.value
        else:
            abort(http.HTTPStatus.NOT_FOUND.value)

    def put(self, id):
        server = db.GetServer(id)
        if not server:
            abort(http.HTTPStatus.NOT_FOUND.value)
        args = self.reqparse.parse_args()
        for k, v in args.items():
            if k not in ['tag', 'id'] and v:
                server[k] = v
        db.UpdateServer(id, server)
        return {'server': marshal(server, server_fields)}


api.add_resource(ServerListAPI, '/inventory/api/v1/servers', endpoint='servers')
api.add_resource(ServerAPI, '/inventory/api/v1/server/<int:id>', endpoint='server')



if __name__ == '__main__':
    app.run(debug=True)
