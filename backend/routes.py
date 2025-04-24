from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def health():
    """return service health status"""
    return {"status": "OK"}


@app.route("/count", methods=["GET"])
def count():
    """return length of data"""
    count = db.songs.count_documents({})

    return {"count": count}, 200


@app.route("/song", methods=["GET"])
def songs():
    """return list of all songs"""
    cursor = db.songs.find({})
    list_of_songs = json_util.dumps(cursor)

    return jsonify({"songs": list_of_songs}), 200


@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """return a song by its id"""
    cursor = db.songs.find_one({"id": id})
    song = json_util.dumps(cursor)

    if song:
        return jsonify(song), 200
    else:
        return {"message": "song with id not found"}, 404


@app.route("/song", methods=["POST"])
def create_song():
    """create a song"""
    new_song = request.json

    cursor = db.songs.find_one({"id": new_song['id']})
    song_exists = json_util.dumps(cursor)
    
    if song_exists != 'null':
        return {"Message": f"song with id {new_song['id']} already present"}, 302

    db.songs.insert_one(new_song)
    cursor = db.songs.find_one({"id": new_song['id']})
    inserted_song_id = str(cursor.get('_id'))

    return {"inserted id": {"$oid:": inserted_song_id}}, 201
