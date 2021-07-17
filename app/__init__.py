from flask import Flask
from flask_restful import Api
from flask_pymongo import PyMongo
# from app.api.user import User
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

app = Flask(__name__)
app.config['MONGO_URI'] = DATABASE_URL
mongo_client = PyMongo(app)
db = mongo_client.db
# db_name = 'yahtzee'
# db = mongo_client['yahtzee']

@app.route('/')
def get():
    collection = db['user']
    cursor = collection.find({})
    for document in cursor:
        print(document)
    # list(db.collection.find({}))
    return 'yay!'


# api = Api(app)
# api.add_resource(User, '/user')

if __name__ == '__main__':
    app.run(debug=True)
