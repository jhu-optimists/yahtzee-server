import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
from flask_cors import CORS
import os
import ast
import copy

# CONFIG
app = Flask(__name__)
CORS(app,resources={r"/*":{"origins":"*"}})
app.config['MONGODB_SETTINGS'] = {
    'db': 'yahtzee',
    'host': os.environ.get('DATABASE_URL')
}
db = MongoEngine()
db.init_app(app)

# Local server state
class GameState():
    usernames = []
    current_score_map = {}
    user_scorecard_map = {}
    user_with_turn = ""
    transcript = []
    chat_messages = []
    has_game_started = False
    error_message = ""
    game_status_message = "Game has not started."
    dice_values = []
    dice_roll_count = 0
    has_game_ended = False
    winner=""
    final_scores=[]
    new_hall_record=False
    # refresh_allowed=True

    # Server-side only game state
    turn_idx = 0
    total_turn_count = 0

    def to_json(self):
        return json.dumps(
            {
                "usernames": list(self.usernames),
                "current_score_map": self.current_score_map,
                "user_scorecard_map": self.user_scorecard_map,
                "user_with_turn": self.user_with_turn,
                "transcript": self.transcript,
                "chat_messages": self.chat_messages,
                "has_game_started": self.has_game_started,
                "error_message": self.error_message,
                "game_status_message": self.game_status_message,
                "dice_values": self.dice_values,
                "dice_roll_count": self.dice_roll_count,
                "has_game_ended": self.has_game_ended,
                "winner": self.winner,
                "final_scores": self.final_scores,
                "new_hall_record": self.new_hall_record
            }
        )

game_state = GameState()

# ODM FOR MONGO
class User(db.Document):
    username = db.StringField()
    high_score = db.IntField()

class Hall(db.Document):
    key = db.StringField()
    records = db.ListField()

class Transcript(db.Document):
    logs = db.ListField()

@app.route('/user', methods=['GET'])
def get_user():
    req_username = request.args.get('username')
    user = User.objects(username=req_username)

    if req_username not in game_state.usernames:
        game_state.usernames.append(req_username)
        game_state.transcript.append(f"{req_username} has joined the game! ")
        game_state.user_scorecard_map[req_username] = {}
    else:
        error_msg = f"{req_username} is already logged in."
        # print(error_msg)
        game_state.error_message = error_msg
        return get_game_state()

    if game_state.has_game_started:
        error_msg = "Game has already started."
        # print(error_msg)
        game_state.error_message = error_msg
        return get_game_state()

    if not user:
        new_user = User(
            username=req_username,
            high_score=0
        )
        new_user.save()
        return jsonify(new_user.to_json())
    else:
        resp = {
            'username': user[0]['username'],
            'highScore': user[0]['high_score']
        }
        return jsonify(resp)

@app.route('/hall', methods=['GET'])
def get_hall():
    hall_of_fame = Hall.objects(key='all_records') # CHANGE BEFORE PUSHING
    resp = {
            'records': hall_of_fame[0]['records']
        }
    return jsonify(resp)
        
@app.route('/refresh', methods=['POST'])
def post_refresh(): 
    # if game_state.refresh_allowed:    # todo add optional refresh server toggle for button
    game_state.usernames = []
    game_state.current_score_map = {}
    game_state.user_scorecard_map = {}
    game_state.user_with_turn = ""
    game_state.transcript = []
    game_state.chat_messages = []
    game_state.has_game_started = False
    game_state.error_message = ""
    game_state.game_status_message = "Game has not started."
    game_state.dice_values = []
    game_state.dice_roll_count = 0
    game_state.has_game_ended = False
    game_state.winner=""
    game_state.final_scores=[]
    game_state.new_hall_record=False
    game_state.turn_idx = 0
    game_state.total_turn_count = 0
    #     game_state.refresh_allowed = not game_state.refresh_allowed
    #     return jsonify({'message': 'Server state refreshed'})
    # else:
    #     return jsonify({'error_message': 'Refresh browser to log in'})

# RUN SERVER
if __name__ == '__main__':
    app.run(debug=True)


# ############## SOCKETIO FOR FUTURE ###############
from flask_socketio import SocketIO, send, emit

socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('join')
def handle_joined():
    # print("handle_joined")
    emit('broadcast_game_state', get_game_state(), broadcast=True)

@socketio.on('get_user_with_current_turn')
def get_user_with_current_turn():
    # print("get_user_with_current_turn")
    game_state.user_with_turn = game_state.usernames[game_state.turn_idx]
    game_state.game_status_message = "Game in progress." + game_state.user_with_turn + " is up!"
    emit('broadcast_game_state', get_game_state(), broadcast=True)

@socketio.on('start_game')
def handle_start_game():
    # print("start_game")
    game_state.has_game_started = True
    game_state.user_with_turn = game_state.usernames[game_state.turn_idx]
    game_state.game_status_message = "Game in progress. " + game_state.user_with_turn + " is up!"
    game_state.transcript.append("Game in progress. " + game_state.user_with_turn + " is up!")
    emit('broadcast_game_state', get_game_state(), broadcast=True)

@socketio.on('chat_message')
def handle_chat_message(user, user_message):
    # print(f"{user} sent message {user_message}")
    game_state.chat_messages.append(f"{user}: {user_message}")
    emit('broadcast_game_state', get_game_state(), broadcast=True)

@socketio.on('end_turn')
def handle_end_turn(user, player_score, scorecard):
    # print("handle_end_turn")
    # print(f"{user} score {player_score}.")
    game_state.turn_idx = (game_state.turn_idx + 1) % len(game_state.usernames)
    game_state.user_with_turn = game_state.usernames[game_state.turn_idx]
    game_state.game_status_message = "Game is in progress. " + game_state.user_with_turn + " has the current turn."
    game_state.transcript.append(f"{user} completed their turn with a score of {player_score}. Now, {game_state.user_with_turn} is up!")
    game_state.current_score_map[user] = player_score
    game_state.dice_roll_count = 0
    game_state.user_scorecard_map[user] = scorecard
    game_state.total_turn_count += 1
    set_game_ended(game_state.total_turn_count)
    emit('broadcast_game_state', get_game_state(), broadcast=True)

@socketio.on('dice_values')
def handle_dice_values(dice_values):
    # print(f"Dice values {dice_values}.")
    game_state.dice_values = dice_values
    game_state.dice_roll_count += 1
    game_state.transcript.append(f"{game_state.user_with_turn} rolled {dice_values}")
    emit('broadcast_game_state', get_game_state(), broadcast=True)

def set_game_ended(total_turn_count):
    # print(f"Total turn count: {total_turn_count}.")
    if total_turn_count == len(game_state.usernames) * 13:
        game_state.has_game_ended = True
        set_game_results(game_state.current_score_map)
        update_high_scores(game_state.final_scores[0])
        game_state.transcript.append(f"Game ended with the following scores: {game_state.current_score_map}")
        game_state.transcript.append(f"{game_state.winner} won the game!")
        # update_logs(game_state.transcript)

def update_logs(t): #todo add transcript to db
    new_logs = Transcript(logs=t)
    new_logs.save()

def set_game_results(scores):
    sorted_scores = {k: v for k, v in reversed(sorted(scores.items(), key=lambda item: item[1]))}
    sorted_list = []
    for k, v in sorted_scores.items():
        sorted_list.append([k,v])
    game_state.final_scores = sorted_list
    game_state.winner = sorted_list[0][0]

def update_user_high(user, candidate):
    user = User.objects(username=user)
    current = user[0]['high_score']
    if candidate > current:
        user.update(high_score=candidate)

def update_hall_of_fame(user, candidate):
    hall_of_fame = Hall.objects(key='all_records')
    hall_recs = copy.deepcopy(hall_of_fame[0]['records'])

    for i in range(10):
        if candidate >= hall_recs[i][1]:
            hall_recs.insert(i, [user, candidate])
            new_hall = hall_recs[:10]
            hall_of_fame.update(records=new_hall)
            game_state.new_hall_record=True
            break
        
def update_high_scores(winning_rec):
    update_user_high(winning_rec[0], winning_rec[1])
    update_hall_of_fame(winning_rec[0], winning_rec[1])

def get_game_state():
    return game_state.to_json()

if __name__ == '__main__':
    socketio.run(app, port=5000)
