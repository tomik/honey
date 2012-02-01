
# db objects:
#
# db.games:
# {"player1": "xxx", "player2", "yyy", "winner" : 0,
#  "moves": [
#       {"move": "j17", "color": 0, "comment": "beginning of the game", "marks": []},
#       {"move": "k12", "color": 1},
#       first variant
#       [{"move": "k13", "color": 0}],
#       second variant
#       [{"move": "k14", "color": 0}],
#       third  variant
#       [{"move": "k14", "color": 0}]]}
#
# db.comments:
# {"author": user_id, "date": "2011-02-17", "game": gameID
#  "text": "This move is wrong"}    
#
# db.users:
# {"username": "slpwnd", "email": "slpwnd@gmail.com", "passwd": "hashed passwd"}
#

import utils
from core import app

def create_game(sgf, user):
    """Parses and validates sgf and stores a game in the database."""
    try:
        game = utils.parseSgf(sgf)
    except utils.SgfParseError:
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

