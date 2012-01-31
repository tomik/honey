
from flask import Flask

app = Flask(__name__)
app.config["db_host"] = "localhost"
app.config["db_port"] = 27017
app.config["db_name"] = "honey"


