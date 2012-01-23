import urllib

from flask import Flask, request, redirect, url_for, render_template, abort
app = Flask(__name__)

@app.route("/")
def new_game():
    return render_template("index.html", input_sgf="")

@app.route("/load_game", methods=["POST"])
def load_game():
    try:
        url = request.form["url"]
        if url:
            try:
                f = urllib.urlopen(url)
            except IOError:
                return render_template("index.html", load_error="incorrect url")
            return render_template("view_game.html", input_sgf=f.readlines())
    except KeyError:
        pass
    try:
        lg_id = request.form["lg_id"]
        if lg_id:
            return redirect("/lg/" + lg_id) 
    except KeyError:
        pass
    return render_template("index.html", load_error="please fill one of the fields below")

@app.route("/lg/<game_id>")
def lg_game(game_id):
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % game_id)
    return render_template("view_game.html", 
        lg_id=game_id, input_sgf=f.readlines())

@app.route("/sgf", methods=["POST"])
def sgf_download():
    return request.form["sgf"]

if __name__ == "__main__":
    app.debug = True
    app.run()
