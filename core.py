
from flask import Flask

app = Flask(__name__)
app.secret_key = "'\x16\xae\x100^H\xc8\x18\xe6\x11\x7f\x12B]\xa7"
app.config["db_host"] = "localhost"
app.config["db_port"] = 27017
app.config["db_name"] = "honey"

