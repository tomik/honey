import urllib
import json
from functools import wraps

from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug import  generate_password_hash

import db
import forms
from core import app
from pagination import Pagination

def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if session.get("user", None) is not None: 
            return f(*a, **k)
        else:
            flash("You need to login to do that.")
            return redirect(url_for("login"))
    return wrapper

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = forms.SignupForm()
    if form.validate_on_submit():
        user = db.create_user(form.username.data, form.email.data,
                generate_password_hash(form.password.data))
        session["user"] = user
        flash("You have signed up sucessfully.")
        return redirect(url_for("main"))
    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        session["user"] = form.user
        flash("You were logged in.")
        return redirect(url_for("main"))
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You were logged out")
    return redirect(url_for("main"))

@app.route("/page/<int:page>")
@app.route("/", defaults={"page": 1})
def main(page):
    per_page = app.config["games_per_page"]
    game_from, game_to = (page - 1) * per_page, page * per_page
    game_cursor = db.get_games()
    games = list(db.get_games()[game_from:game_to])
    for game in games:
        db.annotate(game)
    pagination = Pagination(per_page, page, game_cursor.count(), "main")
    return render_template("index.html", games=games, pagination=pagination)

@app.route("/upload_game", methods=["GET", "POST"])
@login_required
def upload_game():
    """Loads game from url/file, stores in the DB and displays. Requires login."""
    form = forms.SgfUploadForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        if form.sgf:
            user = session["user"]
            game_id = db.create_game(user["_id"], form.sgf)
            if not game_id:
                return render_template("upload_game.html", form=form)
            return redirect(url_for("view_game", game_id=game_id))
        else:
            abort(500)
    return render_template("upload_game.html", form=form)

@app.route("/post_comment", methods=["POST"])
@login_required
def post_comment():
    """Posts comment for given game and path. Requires login. Can be called via AJAX."""
    form = forms.CommentForm(request.form)
    if form.validate_on_submit():
        user = session["user"]
        db.create_comment(user["_id"], form.game_id.data, form.short_path, form.comment.data)
        game = form.game
        patched_game = db.patch_game_with_variant(game, form.full_path)
        db.update_game(patched_game)
    return redirect(url_for("view_game", game_id=form.game_id.data))

# TODO how to handle not-uploaded games?
@app.route("/new_game")
def new_game():
    """Start a new game."""
    return render_template("view_game.html", input_sgf=None)

# TODO handle not-uploaded games?
@app.route("/lg/<lg_game_id>")
def lg_game(lg_game_id):
    """Views lg game for analysis only."""
    f = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % lg_game_id)
    return render_template("view_game.html", 
        lg_id=lg_game_id, input_sgf=f.readlines())

@app.route("/view_game/<game_id>")
def view_game(game_id):
    """Views existing game based on internal game id."""
    game = db.get_game(game_id)
    if not game:
        abort(404) 
    comments=list(db.get_comments_for_game(game_id))
    for comment in comments:
        db.annotate(comment)
    return render_template("view_game.html",
        game_id=game_id,
        comments=comments,
        comment_paths=[(str(c["_id"]), c["path"]) for c in comments],
        form=forms.CommentForm(),
        input_sgf=json.dumps(game["nodes"]))

@app.route("/faq")
def faq():
    """Show FAQ."""
    return render_template("faq.html")

if __name__ == "__main__":
    app.debug = True
    app.run()

