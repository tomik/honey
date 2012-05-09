
from flask import Flask
import mongokit
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = "'\x16\xae\x100^H\xc8\x18\xe6\x11\x7f\x12B]\xa7"
app.config["CSRF_ENABLED"] = False
# paging
app.config["games_per_page"] = 10
app.config["games_per_page_in_user_view"] = 5
app.config["games_per_page_in_player_view"] = 5
app.config["comments_per_page_in_user_view"] = 10
# db
app.config["db_host"] = "localhost"
app.config["db_port"] = 27017
app.config["db_name"] = "honey"
app.conn = mongokit.Connection(app.config["db_host"], app.config["db_port"])
app.db_conn = app.conn[app.config["db_name"]]
# logging
# TODO disabled
handler = RotatingFileHandler("honey.log")
app.logger.addHandler(handler)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(pathname)s %(lineno)d: %(message)s'))

def annotate_request_with_game_type():
    from flask import request
    # fixed for now - will be based on url resolution later
    request.game_type = "go"

app.before_request(annotate_request_with_game_type)
