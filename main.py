import urllib

from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("honey.html", hello_world = "Hello World!", input_sgf="")

@app.route("/lg/<game_id>")
def show_game(game_id):
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % game_id)
    return render_template("honey.html", hello_world = "Hello World!", input_sgf=f.readlines())

if __name__ == "__main__":
    app.debug = True
    app.run()
