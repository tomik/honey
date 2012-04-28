
# Simple abstraction of common db tasks.

# Under the hood MongoKit is used and therefore all the returned objects (i.e. via get_game, get_comment)
# are actually MongoKit classes. The rest of the application knows nothing about MongoKit or even MongoDB.

import datetime
import re

from bson.objectid import ObjectId
import sgf
import mongokit

from core import app

# helpers
db_games = app.db_conn.go_games
db_comments = app.db_conn.go_comments
db_users = app.db_conn.users

@app.conn.register
class Game(mongokit.Document):
    use_dot_notation = True
    structure = {
            "user_id": ObjectId,
            "date": datetime.datetime,
            # type of the game, valid values are "hex", "go", None (unknown)
            "type": str,
            # parsed nodes from sgf
            # first node is the root with game meta information
            # example: [{"FF": 4, "PB": "black", "PW", "white"}, {"W": "aa", "C": "hi gg"},
            #   [[{"B": "bb"}], [{"B": "dd"}]}, {"W": "cc"}]]]
            "nodes": list,
            }

    # sgf GM to game type mapping
    GAME_TYPES = {1: "go", 11: "hex"}

    def resolve_type(self):
        """
        Tries to guess what the game type is. If it can resolve the game type it will set it as well.

        @return True if game type can be resolved. Otherwise False.
        """
        assert(not self.type)
        # GM is the main source of game type information
        if "GM" in self.nodes[0]:
            try:
                self.type = self.GAME_TYPES[int(self.nodes[0]["GM"])]
                return True
            except KeyError:
                pass
        # little golem games can be guessed from the tournament name
        if self.is_from_little_golem():
            for game_type in self.GAME_TYPES.values():
                if re.match(r"^%s[0-9\.]" % game_type, self.event):
                    self.type = game_type
                    return True
        return False

    def save(self):
        # hack, for some reason type is unicode here
        self.type = str(self.type)
        super(Game, self).save()

    @property
    def source(self):
        return self.nodes[0].get("SO", None)

    @property
    def size(self):
        return self.nodes[0].get("SZ", None)

    @property
    def result(self):
        return self.nodes[0].get("RE", "?")

    @result.setter
    def result(self, value):
        self.nodes[0]["RE"] = value

    @property
    def player1(self):
        return self.nodes[0].get("PB", "player1")

    @player1.setter
    def player1(self, value):
        self.nodes[0]["PB"] = value

    @property
    def player2(self):
        return self.nodes[0].get("PW", "player2")

    @player2.setter
    def player2(self, value):
        self.nodes[0]["PW"] = value

    @property
    def event(self):
        return self.nodes[0].get("EV", "?")

    @event.setter
    def event(self, value):
        self.nodes[0]["EV"] = value

    @property
    def komi(self):
        return self.nodes[0].get("KM", None)

    @komi.setter
    def komi(self, value):
        self.nodes[0]["KM"] = value

    def is_owner(self, user):
        return user._id == self.user_id

    def is_from_little_golem(self):
        return self.source == "http://www.littlegolem.com"


@app.conn.register
class Comment(mongokit.Document):
    use_dot_notation = True
    structure = {
            "user_id": ObjectId,
            "game_id": ObjectId,
            "date": datetime.datetime,
            # short path to the node where comment applies in form [(branch, node-in-branch), ...]
            # example: [(0, 7), (1, 5), (1, 2)]
            "path": list,
            "text": unicode,
            }


@app.conn.register
class User(mongokit.Document):
    use_dot_notation = True
    structure = {
            "username": unicode,
            "email": unicode,
            "passwd": str,
            "joined_date": datetime.datetime,
            }


def reset():
    """
    Resets all the date in all the collections.

    Only for dev purpose.
    """
    db_games.remove()
    db_users.remove()
    db_comments.remove()

def annotate(obj, recursive=False):
    """
    Transforms mongodb ids into objects.
    """
    if "user_id" in obj:
        obj["user"] = db_users.User.find_one({"_id": ObjectId(obj["user_id"])})
        if recursive:
            annotate(obj["user"], recursive=True)
    if "game_id" in obj:
        obj["game"] = db_games.Game.find_one({"_id": ObjectId(obj["game_id"])})
        if recursive:
            annotate(obj["user"], recursive=True)
    return obj

def get_users():
    """
    Fetches all the users based on given ordering.

    @return users iterator
    """
    return db_users.User.find()

def get_user(user_id):
    """Returns user for given id."""
    return db_users.User.find_one({"_id": ObjectId(user_id)})

def get_user_by_username(username):
    """Returns user for given username."""
    return db_users.User.find_one({"username": username})

def create_user(username, email, passwd_hash):
    """Creates user in the db."""
    user = db_users.User()
    user.username = unicode(username)
    user.email = unicode(email)
    user.passwd = passwd_hash
    user.joined_date = datetime.datetime.now()
    user.save()
    return user

def create_game(user_id, sgf_str, expected_game_type=None):
    """Parses and validates sgf and stores a game in the database."""
    try:
        sgf_coll = sgf.parseSgf(sgf_str)
    except sgf.SgfParseError, e:
        app.logger.warning("cannot parse sgf: error(%s) sgf(%s)" % (str(e), sgf_str))
        return False, "cannot parse sgf"
    # TODO validate sgf
    # TODO allow upload of multiple games
    sgf_game = sgf_coll[0]
    game = db_games.Game()
    game.user_id = user_id
    game.date = datetime.datetime.now()
    game.nodes = sgf_game
    # fix the result for little golem format
    try:
        if game.nodes[0]["RE"] in ["B", "W"]:
           game.nodes[0]["RE"] = game.nodes[0]["RE"] + "+"
    except KeyError:
        pass
    if not game.resolve_type():
        return False, "Cannot parse game type."
    if expected_game_type and expected_game_type != game.type:
        return False, "Game type mismatch. Expected %s, got %s." % (expected_game_type, game.type)
    game.save()
    return game, None

def create_new_game(user_id, game_type):
    """Creates the new blank game without accompanying sgf."""
    game = db_games.Game()
    game.user_id = user_id
    game.date = datetime.datetime.now()
    game.nodes = []
    # root node
    game.nodes.append({})
    game.type = game_type
    game.save()
    return game

def update_game(game):
    """Updates game in the db."""
    game.save()
    return game

def get_game(id):
    """Fetches game for given id."""
    return db_games.Game.find_one({"_id": ObjectId(id)})

def order(coll, ordering=None, ascending=False):
    """
    Orders collection according to given ordering.

    @ordering one of the following:
        "date" "activity" "player_strength" "popularity" "first_name" "second_name"
    @ascending defines direction of ordering
    @return games iterator
    """
    if not ordering:
        return coll
    direction = ascending and 1 or -1
    mapping = {"date": "date"}
    order_pairs = [(mapping[ordering], direction)]
    return coll.sort(order_pairs)

def get_games(ordering=None, ascending=False):
    """
    Fetches all the games based on given ordering.

    """
    return order(db_games.Game.find(), ordering, ascending)

# TODO ordering and reversed
def get_games_for_user(user_id, ordering=None, ascending=False):
    """Same as get_games for a single user."""
    return order(db_games.Game.find({"user_id": user_id}, ordering, ascending))

def sync_game_update(game, update_data, user):
    """
    Syncing mechanism.

    Whenever someone adds/removes node(s) or add/removes/changes properties of nodes, this is called.
    Goes through update data and updates the game to match the update data.
    Makes sure that user is allowed to perform the sync otherwise throws an exception.
    """
    # TODO verify that the user has the right to perform the update
    new_nodes = update_data[:]
    new_nodes.insert(0, game.nodes[0])
    game.nodes = new_nodes
    game.save()
    return True

def patch_game_with_variant(game, full_path):
    """Adds variant to given game if it doesn't exist yet."""
    cursor = sgf.Cursor(game.nodes)
    for node_dict in full_path:
        for variant in xrange(cursor.get_variants_num()):
            if sgf.nodes_are_same_moves(node_dict, cursor.get_next(variant)):
                cursor.next(variant)
                break
        else:
            # create new node (creates new variant as well)
            cursor.add_node(node_dict)
            # and follow it
            cursor.next(cursor.get_variants_num() - 1)
    return game

def patch_game_with_comments(game, comments):
    """
    Adds all the comments to their corresponding nodes.

    Changes the game object in place.
    Expects comments to be annotated (with corresponding user objects).
    """
    for comment in comments:
        cursor = sgf.Cursor(game.nodes)
        for branch, jump in comment.path:
            for i in xrange(jump):
                cursor.next(branch)
                # we branch only once
                branch = 0
            node = cursor.get_node()
            if node:
                cmt = node.get("C", "")
                cmt += "On %s %s said:\n%s\n\n" % \
                        (comment.date.strftime("%Y-%m-%d %H:%M:%S"), comment.user.username, comment.text)
                node["C"] = cmt
    return game

def create_comment(user_id, game_id, path, text):
    """Creates comment."""
    # game_id goes through the form post and doesn't retain its type
    if type(game_id) != ObjectId:
        game_id = ObjectId(game_id)
    comment = db_comments.Comment()
    comment.text = text
    comment.date = datetime.datetime.now()
    comment.user_id = user_id
    comment.game_id = game_id
    comment.path = path
    comment.save()
    comment_id = comment._id
    return comment

def get_comment(id):
    """Fetches comment for given id."""
    return db_comments.Comment.find_one({"_id": ObjectId(id)})

def get_comments_for_game(game_id):
    """Fetches comments for given game."""
    return db_comments.Comment.find({"game_id": ObjectId(game_id)})

def get_comments_for_user(user_id):
    """Fetches all comments made by given user."""
    return db_comments.Comment.find({"user_id": ObjectId(user_id)})

