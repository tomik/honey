
import urllib
import random

def setup():
    """
    Setup simple fixtures.

    Creates couple of games, users, comments and variants for manual testing.
    Requires db server to be running.
    """
    import db
    from core import app
    from werkzeug import generate_password_hash

    # clear the database
    db.reset()
    # setup users
    users = ["user1", "user2", "user3"]
    for user in users:
        db.create_user(user, "%s@gmail.com" % user, generate_password_hash(user))
    # setup lg games
    hex_lg_games = ["1401966", "1401967", "1401968", "1401969", "1401970", "1401971", "1401972", "1401973", "1401974", "1401975", "1401976", "1401977", "1401978", "1401979", "1401980", "1401981", "1401982", "1401983", "1401984", "1401985", "1401986", "1401987", "1401988", "1401989", "1401990", "1401991", "1401992", "1401993", "1401994", "1401995", "1401996", "1401997", "1401998", "1401999", "1402000", "1402001"]
    go_lg_games = ["1384554", "1384555", "1384556", "1384557", "1384558", "1384559", "1384560", "1384561", "1384562", "1384563", "1384564", "1384565", "1384566", "1384567", "1384568", "1384569", "1384570", "1384571", "1384572", "1384573", "1384574", "1384575", "1384576", "1384577", "1384578", "1384579", "1384580", "1384581", "1384582", "1384583", "1384584", "1384585", "1384586", "1384587", "1384588", "1384567"]
    for id in hex_lg_games[:3]:
        print("Creating lg game %s" % id)
        sgf = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % id).read()
        user_id = random.choice(list(db.get_users()))["_id"]
        game = db.create_game(user_id, sgf)
    for id in go_lg_games[:3]:
        print("Creating lg game %s" % id)
        sgf = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.sgf" % id).read()
        user_id = random.choice(list(db.get_users()))["_id"]
        game = db.create_game(user_id, sgf)
