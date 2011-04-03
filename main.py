import urllib

from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def new_game():
    return render_template("honey.html", input_sgf="")

@app.route("/lg/<game_id>")
def lg_game(game_id):
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % game_id)
    return render_template("honey.html", 
        lg_id=game_id, input_sgf=f.readlines())

if __name__ == "__main__":
    app.debug = True
    app.run()
