
"""
Setup simple fixtures.      

Creates couple of games, users, comments and variants for manual testing.
"""

import urllib
import random

from werkzeug import generate_password_hash

import db
from core import app

def main():
    # clear the database
    app.db.games.remove()
    app.db.users.remove()
    app.db.comments.remove()
    # setup users
    users = ["user1", "user2", "user3"]
    for user in users:
        db.create_user(user, "%s@gmail.com" % user, generate_password_hash(user))
    # setup lg games
    lg_games = ["1401966", "1401967", "1401968", "1401969", "1401970", "1401971", "1401972", "1401973", "1401974", "1401975", "1401976", "1401977", "1401978", "1401979", "1401980", "1401981", "1401982", "1401983", "1401984", "1401985", "1401986", "1401987", "1401988", "1401989", "1401990", "1401991", "1401992", "1401993", "1401994", "1401995", "1401996", "1401997", "1401998", "1401999", "1402000", "1402001"]
    for id in lg_games:
        sgf = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % id).read()
        user_id = random.choice(list(app.db.users.find()))["_id"]
        game = db.create_game(user_id, sgf)

if __name__ == "__main__":
    main()

