
from flask import Flask
import mongokit

app = Flask(__name__)
app.secret_key = "'\x16\xae\x100^H\xc8\x18\xe6\x11\x7f\x12B]\xa7"
app.config["CSRF_ENABLED"] = False
app.config["db_host"] = "localhost"
app.config["db_port"] = 27017
app.config["db_name"] = "honey"
app.config["games_per_page"] = 10
app.config["games_per_page_in_user_view"] = 5
app.config["comments_per_page_in_user_view"] = 10
app.conn = mongokit.Connection(app.config["db_host"], app.config["db_port"])
app.db_conn = app.conn[app.config["db_name"]]

