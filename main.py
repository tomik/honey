import urllib

from flask import request, redirect, url_for, render_template, abort
from core import app

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/load_game", methods=["POST"])
def load_game():
    """Loads game from url/file, stores in the DB and displays. Requires login."""
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
    except IOError:
        return render_template("index.html", load_error="invalid resource")
    try:
        lg_id = request.form["lg_id"]
        if lg_id:
            return redirect("/lg/" + lg_id) 
    except KeyError:
        pass
    return render_template("index.html", load_error="please fill one of the fields below")

@app.route("/new_game")
def new_game():
    return render_template("view_game.html", input_sgf=None)

@app.route("/lg/<lg_game_id>")
def lg_game(lg_game_id):
    """Views lg game for analysis only."""
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % game_id)
    return render_template("view_game.html", 
        lg_id=game_id, input_sgf=f.readlines())

@app.route("/view_game/<game_id>")
def view_game(game_id):
    """Views existing game based on internal game id."""
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % game_id)
    return render_template("view_game.html", 
        lg_id=game_id, input_sgf=f.readlines())

@app.route("/comment/<game_id>")
def post_comment():
    """Posts comment for a given game. Requires login."""
    raise NotImplementedError

if __name__ == "__main__":
    app.debug = True
    app.run()

