#!flask/bin/python

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

from flask import Flask, jsonify, abort, make_response
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
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web',
        'done': False
    }
]

server_fields = {
    'tag': fields.String,
    'sid': fields.Integer,
    'stockid': fields.Integer,
    'uri': fields.Url('server')
}

class ServerListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tag', type=str, required=True, help='No service tag provided', location='json')
        self.reqparse.add_argument('sid', type=int, required=True, help='No service ID provided', location='json')
        self.reqparse.add_argument('stockid', type=int, help='No service ID provided', location='json')
        super(ServerListAPI, self).__init__()

    def get(self):
        logging.debug("Getting server list...")
        return {'server': [marshal(server, server_fields) for server in db.GetServers()]}

    def post(self):
        args = self.reqparse.parse_args()
        server = {
            'tag': args['tag'],
            'sid': args['sid'],
            'stockid': args['stockid']
        }
        updated = db.CreateServer(server)
        logging.debug("Got {}".format(updated))
        if 'id' in updated:
            return {'server': marshal(updated, server_fields)}, http.HTTPStatus.CREATED.value
        else:
            abort(http.HTTPStatus.CONFLICT.value)

task_fields = {
    'title': fields.String,
    'description': fields.String,
    'done': fields.Boolean,
    'uri': fields.Url('task')
}

class ServerAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tag', type=str, location='json')
        self.reqparse.add_argument('sid', type=int, location='json')
        self.reqparse.add_argument('stockid', type=int, location='json')
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



class TaskListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                   help='No task title provided',
                                   location='json')
        self.reqparse.add_argument('description', type=str, default="",
                                   location='json')
        super(TaskListAPI, self).__init__()

    def get(self):
        return {'tasks': [marshal(task, task_fields) for task in tasks]}

    def post(self):
        args = self.reqparse.parse_args()
        task = {
            'id': tasks[-1]['id'] + 1,
            'title': args['title'],
            'description': args['description'],
            'done': False
        }
        tasks.append(task)
        return {'task': marshal(task, task_fields)}, 201


class TaskAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(TaskAPI, self).__init__()

    def get(self, id):
        task = [task for task in tasks if task['id'] == id]
        if len(task) == 0:
            abort(404)
        return {'task': marshal(task[0], task_fields)}

    def put(self, id):
        task = [task for task in tasks if task['id'] == id]
        if len(task) == 0:
            abort(404)
        task = task[0]
        args = self.reqparse.parse_args()
        for k, v in args.items():
            if v is not None:
                task[k] = v
        return {'task': marshal(task, task_fields)}

    def delete(self, id):
        task = [task for task in tasks if task['id'] == id]
        if len(task) == 0:
            abort(404)
        tasks.remove(task[0])
        return {'result': True}


api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<int:id>', endpoint='task')
api.add_resource(ServerListAPI, '/inventory/api/v1/servers', endpoint='servers')
api.add_resource(ServerAPI, '/inventory/api/v1/server/<int:id>', endpoint='server')

if __name__ == '__main__':
    app.run(debug=True)
