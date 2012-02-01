import urllib

from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug import  generate_password_hash

from forms import LoginForm, SignupForm
from db import get_user, create_user
from core import app

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        create_user(form.username.data, form.email.data,
                generate_password_hash(form.password.data))
        session["username"] = form.username.data
        flash("You have signed up sucessfully.")
        return redirect(url_for("main"))
    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session["username"] = form.username.data
        flash("You were logged in")
        return redirect(url_for("main"))
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You were logged out")
    return redirect(url_for("main"))

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
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % lg_game_id)
    return render_template("view_game.html", 
        lg_id=lg_game_id, input_sgf=f.readlines())

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

