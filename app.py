from flask import Flask 
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('join')
def handle_joined(user):
    print(f"{user} joined the game")
    emit('join_success', f"{user} has joined the chat!", broadcast=True)

# @socketio.on('message')
# def handle_chat(msg):
#     print(msg)
#     send(msg, broadcast=True)

if __name__ == '__main__':
	socketio.run(app, port=5000)