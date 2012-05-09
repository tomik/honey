import urllib
import urlparse
import json
from functools import wraps
from datetime import datetime

from flask import abort, flash, jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug import  generate_password_hash

import db
import forms
import sgf
from core import app
from pagination import Pagination

@app.template_filter()
def now(format):
    return datetime.now().strftime(format)

@app.template_filter()
def form_has_errors(form):
    for field in form._fields.values():
        if field.errors:
            return True
    return form.errors

@app.template_filter()
def game_type_to_label(game_type):
    return game_type.capitalize()

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
    games_cursor = db.get_games(ordering="date")
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
    form = forms.SgfUploadForm()
    # this must be done explicitly
    # because for some reason request.files is not picked up by the wtf form
    if request.method == "POST" and "file" in request.files:
        form.file.data = request.files["file"]
    if request.method == "POST" and form.validate_on_submit():
        if form.sgf:
            username = session["username"]
            user = db.get_user_by_username(username)
            if not user:
                abort(500)
            game, err = db.create_game(user._id, form.sgf, request.game_type)
            if not game:
                # attach the error to the form
                if form.url.data:
                    form.url.errors = (err,)
                elif form.file.data:
                    form.file.errors = (err,)
                return render_template("upload_game.html", menu_toggle_upload=True, form=form)
            return redirect(url_for("view_game", game_id=game._id))
        else:
            abort(500)
    return render_template("upload_game.html", menu_toggle_upload=True, form=form)

@app.route("/edit_game/<game_id>", methods=["POST"])
@login_required
def edit_game(game_id):
    """Edit game meta information."""
    game = db.get_game(game_id)
    if not game:
        abort(404)
    user = db.get_user_by_username(session["username"])
    if not user:
        abort(500)
    # protection
    if not game.is_owner(user):
        app.logger.warning("Unauthorized game edit: user(%s) game(%s)" % (user.username, game._id))
        abort(500)
    form = forms.GameEditForm.form_factory(game.type)(request.form)
    if form.validate_on_submit():
        form.update_game(game)
        return redirect(url_for("view_game", game_id=game._id))
    return _view_game(game._id, [], game_edit_form=form)

@app.route("/create_game")
@login_required
def create_game():
    """Creates new game and lets the user edit it."""
    user = db.get_user_by_username(session["username"])
    game = db.create_new_game(user._id, request.game_type)
    return redirect(url_for("view_game", game_id = game._id))

@app.route("/post_comment/<game_id>", methods=["POST"])
@login_required
def post_comment(game_id):
    """Posts comment for given game and path. Requires login. Called via ajax."""
    game = db.get_game(game_id)
    if not game:
        abort(404)
    form = forms.CommentForm(request.form)
    if form.validate_on_submit():
        username = session["username"]
        user = db.get_user_by_username(username)
        if not user:
            app.logger.warning("comment without user")
            abort(500)
        comment = db.create_comment(user._id, game_id, form.short_path, form.comment.data)
        db.annotate(comment)
        can_delete_comment = comment.is_owner(user)
        comment_template = app.jinja_env.from_string(
            """
            {%% from 'macros.html' import render_comment_in_game %%} {{ render_comment_in_game(comment, %s) }}
            """ % can_delete_comment)
        return jsonify(err=None, comment_id = str(comment["_id"]), comment_path=comment["path"], comment_html = comment_template.render(comment=comment))
    return jsonify(err="Invalid comment.")

@app.route("/delete_comment", methods=["POST"])
@login_required
def delete_comment():
    """Deletes comment identified by id in post data. Requires login. Called via ajax."""
    username = session["username"]
    user = db.get_user_by_username(username)
    if not user:
        app.logger.warning("comment without user")
        abort(500)
    comment_id = request.form.get("comment_id", None)
    comment = db.get_comment(comment_id)
    if not comment:
        app.logger.warning("no comment for given id %s" % comment_id)
        abort(500)
    can_delete_comment = comment.is_owner(user)
    if not can_delete_comment:
        app.logger.warning("User %s tried to delete comment %s without permissions." % (user["_id"], comment["_id"]))
        abort(500)
    db.delete_comment(comment_id)
    return jsonify(err=None, comment_id = comment_id)

@app.route("/post_update/<game_id>", methods=["POST"])
@login_required
def post_update(game_id):
    """Posts game tree updates for given game. Requires login. Called via ajax."""
    game = db.get_game(game_id)
    if not game:
        abort(404)
    username = session["username"]
    user = db.get_user_by_username(username)
    try:
        update_data = json.loads(request.form.get("update_data"))
    except:
        return jsonify(err="Invalid encoding.")
    if not db.sync_game_update(game, update_data, user):
        return jsonify(err="You don't have permission to perform this action.")
    return jsonify(err=None)

@app.route("/view_sgf/<game_id>")
def view_sgf(game_id):
    """Views sgf for game identified by game_id"""
    game = db.get_game(game_id)
    if not game:
        abort(404)
    annotated_comments = [db.annotate(c) for c in db.get_comments_for_game(game_id)]
    # this changes the game itself
    # but that is fine since we don't intend to save it
    game = db.patch_game_with_comments(game, annotated_comments)
    response = make_response(sgf.makeSgf([game.export()]))
    response.headers["Content-type"] = "text/plain"
    return response

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

@app.route("/view_player/<player_id>")
def view_player(player_id):
    """
    Views existing player based on his id.

    Pagination is provided in query string via keys games_page.
    """
    player = db.get_player(player_id)
    if not player:
        abort(404)
    queries = dict(urlparse.parse_qsl(request.query_string))
    games_page = int(queries.get("games_page", 1))
    # paginate games
    games_per_page = app.config["games_per_page_in_player_view"]
    games_from, games_to = (games_page - 1) * games_per_page, games_page * games_per_page
    games_cursor = db.get_games_for_player(player._id)
    num_all_games = games_cursor.count()
    games = list(games_cursor)[games_from:games_to]
    games_pagination = Pagination(games_per_page, games_page, num_all_games,
            lambda page: url_for("view_player", player_id=player_id, games_page=page))
    for game in games:
        db.annotate(game)
    return render_template("view_player.html",
        player=player,
        games=games,
        games_pagination=games_pagination)

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
        game_edit_form = forms.GameEditForm.form_factory(game.type)()
    print game.nodes
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

