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

# Local server state
class GameState():
    usernames = set()
    high_score_map = [] # Map from username to their high score. We use a map instead of an object list since it is easier to to perform lookups. 
    current_score_map = []
    user_with_turn = ""
    game_transcript = []
    chat_messages = []
    has_game_started = False
    error_message = ""

    def to_json(self):
        return json.dumps(
            {
                "usernames": list(self.usernames), # set is not serializable to json, so we convert it to list
                "high_score_map": self.high_score_map,
                "current_score_map": self.current_score_map,
                "user_with_turn": self.user_with_turn,
                "game_transcript": self.game_transcript,
                "chat_messages": self.chat_messages,
                "has_game_started": self.has_game_started,
                "error_message": self.error_message
            }
        )

game_state = GameState()

# ODM FOR MONGO
class User(db.Document):
    username = db.StringField()
    high_score = db.StringField()
    def to_json(self):
        return {"username": self.username,
                "high_score": self.high_score}


# ROUTES
@app.route('/user', methods=['GET'])
def get_user():
    req_username = request.args.get('username')
    user = User.objects(username=req_username)

    if req_username not in game_state.usernames:
        game_state.usernames.add(req_username)
    else:
        error_msg = f"{req_username} is already logged in. "
        print(error_msg)
        game_state.error_message = error_msg
        return get_game_state()

    if not user:
        new_user = User(
            username=req_username,
            high_score="0"
        )
        new_user.save()
        return jsonify(new_user.to_json())
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
        return jsonify({'Do': 'Something'}) # todo error handling
    else:
        candidate = body_dict['newScore']
        current = user[0]['high_score']
        if candidate > current:
            resp = {"message": f"New high score! {candidate} beats {current}"}
            user.update(high_score=candidate)
        else:
            resp = {"message": f"{candidate} doesn't beat your current high score of {current}. Try again!"}
    return jsonify(resp)


# RUN SERVER
if __name__ == '__main__':
    app.run(debug=True)


# ############## SOCKETIO FOR FUTURE ###############
from flask_socketio import SocketIO, send, emit

socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('join')
def handle_joined(user):
    print(f"{user} joined the game")
    game_state.chat_messages.append(f"{user} joined the game. ")
    emit('broadcast_game_state', get_game_state(), broadcast=True)

def get_game_state():
    return game_state.to_json()

if __name__ == '__main__':
	socketio.run(app, port=5000)