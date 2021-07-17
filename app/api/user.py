import json
import flask
from flask_restful import Resource
from pymongo import MongoClient


class User(Resource):
    # __init__(self):

    def get(self):
        print('somethin')
        client = MongoClient()
        db = client.db
        users = db.user.find()
        return flask.jsonify([user for user in users])
        for user in users:
            print(user)
        print('hihihi')
        # todos = db.todos.find()
        # return flask.jsonify([todo for todo in todos])
