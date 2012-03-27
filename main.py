import urllib
import urlparse
import json
from functools import wraps
from datetime import datetime

from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug import  generate_password_hash

import db
import forms
import sgf
from core import app
from pagination import Pagination

@app.template_filter()
def now(format):
    return datetime.now().strftime(format)

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
    form = forms.SignupForm()
    if form.validate_on_submit():
        user = db.create_user(form.username.data, form.email.data,
                generate_password_hash(form.password.data))
        session["username"] = user.username
        flash("You have signed up sucessfully.")
        return redirect(url_for("main"))
    return render_template("signup.html", form=form, menu_toggle_signup=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        session["username"] = form.user.username
        flash("You were logged in.")
        return redirect(url_for("main"))
    return render_template("login.html", form=form, menu_toggle_login=True)

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You were logged out")
    return redirect(url_for("main"))

@app.route("/")
def main():
    """
    Views all games.

    Pagination is provided in query string via key page.
    """
    queries = dict(urlparse.parse_qsl(request.query_string))
    page = int(queries.get("page", 1))
    per_page = app.config["games_per_page"]
    game_from, game_to = (page - 1) * per_page, page * per_page
    games_cursor = db.get_games()
    num_all_games = games_cursor.count()
    games = list(games_cursor[game_from:game_to])
    for game in games:
        db.annotate(game)
    pagination = Pagination(per_page, page, num_all_games, lambda page: url_for("main", page=page))
    return render_template("index.html", menu_toggle_games=True, games=games, pagination=pagination)

@app.route("/upload_game", methods=["GET", "POST"])
@login_required
def upload_game():
    """Loads game from url/file, stores in the DB and displays. Requires login."""
    form = forms.SgfUploadForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        if form.sgf:
            username = session["username"]
            user = db.get_user_by_username(username)
            if not user:
                abort(500)
            game_id = db.create_game(user._id, form.sgf)
            if not game_id:
                return render_template("upload_game.html", menu_toggle_upload=True, form=form)
            return redirect(url_for("view_game", game_id=game_id))
        else:
            abort(500)
    return render_template("upload_game.html", menu_toggle_upload=True, form=form)

@app.route("/edit_game", methods=["POST"])
@login_required
def edit_game():
    """Edit game meta information."""
    form = forms.GameEditForm(request.form)
    if form.validate_on_submit():
        user = db.get_user_by_username(session["username"])
        if not user:
            abort(500)
        game = form.game
        game.player1 = form.player1.data
        game.player2 = form.player2.data
        game.event = form.event.data
        game.result = form.result.data
        db.update_game(game)
        return redirect(url_for("view_game", game_id=game._id))
    if not form.game_id.data:
        abort(500)
    return _view_game(form.game_id.data, [], game_edit_form=form)

@app.route("/post_comment", methods=["POST"])
@login_required
def post_comment():
    """Posts comment for given game and path. Requires login."""
    form = forms.CommentForm(request.form)
    if form.validate_on_submit():
        username = session["username"]
        user = db.get_user_by_username(username)
        if not user:
            app.logger.warning("comment without user")
            abort(500)
        comment = db.create_comment(user._id, form.game_id.data, form.short_path, form.comment.data)
        game = form.game
        patched_game = db.patch_game_with_variant(game, form.full_path)
        db.update_game(patched_game)
        return redirect(url_for("view_comment", comment_id=comment._id))
    if not form.game_id.data:
        app.logger.warning("comment without game_id")
        abort(500)
    return _view_game(form.game_id.data, [], comment_form=form)

@app.route("/view_sgf/<game_id>")
def view_sgf(game_id):
    """Views sgf for game identified by game_id"""
    game = db.get_game(game_id)
    if not game:
        abort(404)
    return sgf.makeSgf([game.nodes])

@app.route("/view_game/<game_id>")
def view_game(game_id):
    """Views existing game based on internal game id."""
    return _view_game(game_id, [])

@app.route("/view_comment/<comment_id>")
def view_comment(comment_id):
    """Views existing game on given comment."""
    comment = db.get_comment(comment_id)
    if not comment:
        abort(404)
    return _view_game(comment.game_id, comment.path)

@app.route("/view_user/<username>")
def view_user(username):
    """
    Views existing user based on his username.

    Pagination is provided in query string via keys games_page, comments_page.
    """
    user = db.get_user_by_username(username)
    if not user:
        abort(404)
    queries = dict(urlparse.parse_qsl(request.query_string))
    games_page = int(queries.get("games_page", 1))
    comments_page = int(queries.get("comments_page", 1))
    # paginate games
    games_per_page = app.config["games_per_page_in_user_view"]
    games_from, games_to = (games_page - 1) * games_per_page, games_page * games_per_page
    games_cursor = db.get_games_for_user(user._id)
    num_all_games = games_cursor.count()
    games = list(games_cursor)[games_from:games_to]
    games_pagination = Pagination(games_per_page, games_page, num_all_games,
            lambda page: url_for("view_user", username=username, games_page=page, comments_page=comments_page))
    for game in games:
        db.annotate(game)
    # paginate comments
    comments_per_page = app.config["comments_per_page_in_user_view"]
    comments_from, comments_to = (comments_page - 1) * comments_per_page, comments_page * comments_per_page
    comments_cursor = db.get_comments_for_user(user._id)
    num_all_comments = comments_cursor.count()
    comments = list(comments_cursor)[comments_from:comments_to]
    comments_pagination = Pagination(comments_per_page, comments_page, num_all_comments,
            lambda page: url_for("view_user", username=username, games_page=games_page, comments_page=page))
    for comment in comments:
        db.annotate(comment)
    return render_template("view_user.html",
        user=user,
        games=games,
        comments=comments,
        games_pagination=games_pagination,
        comments_pagination=comments_pagination)

def _view_game(game_id, init_path, game_edit_form=None, comment_form=None):
    """
    Views existing game on given (comment) path.

    When there are errors with comment for instance of this one can be passed in and errors displayed.
    """
    game = db.get_game(game_id)
    if not game:
        abort(404)
    # fetch games owner
    db.annotate(game)
    comments=list(db.get_comments_for_game(game_id))
    for comment in comments:
        db.annotate(comment)
    # forms
    if not comment_form:
        comment_form = forms.CommentForm()
    user = db.get_user_by_username(session.get("username", None))
    if user and game.is_owner(user) and not game_edit_form:
        game_edit_form = forms.GameEditForm()
    return render_template("view_game.html",
        game=game,
        init_path=init_path,
        comments=comments,
        comment_paths=[(str(c["_id"]), c["path"]) for c in comments],
        comment_form=comment_form,
        game_edit_form=game_edit_form)

@app.route("/faq")
def faq():
    """Show FAQ."""
    return render_template("faq.html", menu_toggle_faq=True)

if __name__ == "__main__":
    app.debug = True
    app.run()

