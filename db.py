
# db objects:
#
# db.games:
# { "user_id": "12345",
#   "date": "2011-02-17",
#   "player1": "black",
#   "player2": "white",
#   "nodes": [{"FF": 4, "PB": "black", "PW", "white"}, {"W": "aa", "C": "hi gg"},
#              {"B": "bb", "variants": [{"W": "dd"}]}, {"W": "cc"}]}
#
# db.comments:
# {"author": user_id,
#  "date": "2011-02-17",
#  "game": gameID
#  #path to the node where comment applies in form [(branch, node-in-branch), ...]
#  "path": [(0, 7), (1, 5), (1, 2)]
#  "text": "This move is wrong"}    
#
# db.users:
# {"username": "slpwnd",
#  "email": "slpwnd@gmail.com",
#  "passwd": "hashed passwd"}
#

import datetime

from bson.objectid import ObjectId
import sgf

from core import app

def get_user(username):
    """Returns password hash fetched from the db."""
    return app.db.users.find_one({"username": username})

def create_user(username, email, passwd_hash):
    """Creates user in the db."""
    app.db.users.insert({"username": username, "email": email, "passwd": passwd_hash})

def create_game(user_id, sgf_str):
    """Parses and validates sgf and stores a game in the database."""
    try:
        sgf_coll = sgf.parseSgf(sgf_str)
    except sgf.SgfParseError, e:
        app.logger.warning("cannot parse sgf: error(%s) sgf(%s)" % (str(e), sgf_str))
        return False
    # TODO validate
    sgf_game = sgf_coll[0]
    game = {"user_id": user_id,
            "date": datetime.datetime.now(),
            "player1": sgf_game[0].get("PB", "?"),
            "player2": sgf_game[0].get("PW", "?"),
            "nodes": sgf_game}
    games = app.db.games
    return games.insert(game)

def get_game(id):
    """Fetches game for given id."""
    return app.db.games.find_one({"_id": ObjectId(id)})

def get_games(ordering=None, reversed=False):
    """
    Fetches all the games bases on given ordering.

    @ordering one of the following:
        "datetime" "activity" "player_strength" "popularity" "first_name" "second_name"
    @return games iterator
    """
    return app.db.games.find()

def get_games_for_user(user_id, ordering, reversed=False):
    """Same as get_games for a single user."""
    raise NotImplementedError

def create_comment(user_id, game_id, path, text):
    """Creates comment."""
    comment = {"text": text,
               "user_id": user_id,
               "game_id": game_id,
               "path": path}
    comments = app.db.comments
    return comments.insert(comment)

def get_comments_for_game(game_id):
    """Fetches comments for given game."""
    return app.db.comments.find({"game_id": game_id})

