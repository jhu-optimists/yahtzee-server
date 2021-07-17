import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
import os

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'yahtzee',
    'host': os.environ.get('DATABASE_URL')
}
db = MongoEngine()
db.init_app(app)


class User(db.Document):
    username = db.StringField()
    high_score = db.StringField()
    def to_json(self):
        return {"username": self.name,
                "high_score": self.high_score}


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

if __name__ == '__main__':
    app.run(debug=True)
