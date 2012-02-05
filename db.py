
# db objects:
#
# db.games:
# { "author": "username", "date": "2011-02-17",
#   "nodes": [{"FF": 4, "PB": "black", "PW", "white"}, {"W": "aa", "C": "hi gg"},
#              {"B": "bb", "variants": [{"W": "dd"}]}, {"W": "cc"}]}
#
# db.comments:
# {"author": user_id, "date": "2011-02-17", "game": gameID
#  "text": "This move is wrong"}    
#
# db.users:
# {"username": "slpwnd", "email": "slpwnd@gmail.com", "passwd": "hashed passwd"}
#

import sgf
from core import app

def create_game(sgf, user):
    """Parses and validates sgf and stores a game in the database."""
    try:
        game = sgf.parseSgf(sgf)
    except sgf.SgfParseError:
        return False
    games = app.db.games
    games.insert(game)

def get_games(ordering, reversed=False):
    """
    Fetches all the games bases on given ordering.

    @ordering one of the following:
        "datetime" "activity" "player_strength" "popularity" "first_name" "second_name"
    @return games iterator
    """
    raise NotImplementedError

def get_games_for_user(user, ordering, reversed=False):
    """Same as get_games for a single user."""
    raise NotImplementedError

def get_user(username):
    """Returns password hash fetched from the db."""
    return app.db.users.find_one({"username": username})

def create_user(username, email, passwd_hash):
    """Creates user in the db."""
    app.db.users.insert({"username": username, "email": email, "passwd": passwd_hash})

