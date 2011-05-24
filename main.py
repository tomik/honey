import urllib

from flask import Flask, request, render_template, abort
app = Flask(__name__)

@app.route("/")
def new_game():
    return render_template("honey.html", input_sgf="")

@app.route("/lg/<game_id>")
def lg_game(game_id):
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % game_id)
    return render_template("honey.html", 
        lg_id=game_id, input_sgf=f.readlines())

@app.route("/sgf", methods=["POST"])
def sgf_download():
    if request.method == "POST":
        return request.form["sgf"]
    abort(404)

if __name__ == "__main__":
    app.debug = True
    app.run()
