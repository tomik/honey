import urllib
from functools import wraps

from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug import  generate_password_hash

from forms import LoginForm, SignupForm, SgfUploadForm
from db import get_user, create_user
from core import app

def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if session.get("username", None) is not None: 
            return f(*a, **k)
        else:
            flash("You need to login to do that.")
            return redirect(url_for("login"))
    return wrapper

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
        flash("You were logged in.")
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

@app.route("/upload_game", methods=["GET", "POST"])
@login_required
def upload_game():
    """Loads game from url/file, stores in the DB and displays. Requires login."""
    form = SgfUploadForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        if form.sgf:
            return render_template("view_game.html", input_sgf=form.sgf.readlines())
        elif form.lg_id:
            return redirect("/lg/" + form.lg_id) 
        else:
            abort(500)
    return render_template("upload_game.html", form=form)

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

