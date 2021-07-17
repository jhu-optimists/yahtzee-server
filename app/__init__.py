import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
from flask_cors import CORS
import os
import ast

# CONFIG
app = Flask(__name__)
CORS(app)
app.config['MONGODB_SETTINGS'] = {
    'db': 'yahtzee',
    'host': os.environ.get('DATABASE_URL')
}
db = MongoEngine()
db.init_app(app)


# ODM FOR MONGO
class User(db.Document):
    username = db.StringField()
    high_score = db.StringField()
    def to_json(self):
        return {"username": self.name,
                "high_score": self.high_score}


# ROUTES
@app.route('/user', methods=['GET'])
def get_user():
    username = request.args.get('username')
    user = User.objects(username=username)
    if not user:
        return jsonify({'Do': 'Something'}) # todo add user to db
    else:
        resp = {
            'username': user[0]['username'],
            'highScore': user[0]['high_score']
        }
        return jsonify(resp)

@app.route('/score', methods=['POST'])
def check_score():
    req_body = request.data.decode("UTF-8")
    body_dict = ast.literal_eval(req_body)
    resp = ''
    user = User.objects(username=body_dict['user'])
    if not user:
        return jsonify({'Do': 'Something'}) # todo add user to db
    else:
        candidate = body_dict['newScore']
        current = user[0]['high_score']
        if candidate > current:
            resp = {"message": f"New high score! {candidate} beats {current}"}
            # todo save new high score 
        else:
            resp = {"message": f"{candidate} doesn't beat your current high score of {current}. Try again!"}
    return jsonify(resp)


# RUN SERVER
if __name__ == '__main__':
    app.run(debug=True)


# ############## SOCKETIO FOR FUTURE ###############

# from flask_socketio import SocketIO, send, emit

# socketio = SocketIO(app, cors_allowed_origins='*')

# @socketio.on('join')
# def handle_joined(user):
#     print(f"{user} joined the game")
#     emit('join_success', f"{user} has joined the chat!", broadcast=True)

# # @socketio.on('message')
# # def handle_chat(msg):
# #     print(msg)
# #     send(msg, broadcast=True)

# if __name__ == '__main__':
# 	socketio.run(app, port=5000)