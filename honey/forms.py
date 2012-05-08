
import urllib
import json
import re

from flaskext.wtf import Form, HiddenField, FileField, FloatField, IntegerField, PasswordField, TextField, TextAreaField, validators
from werkzeug import check_password_hash

import db

class SgfUploadForm(Form):
    """Form for uploading sgf games. Uploaded games are stored in the database."""
    url = TextField("Url")
    file = FileField("File")

    def __init__(self, *a, **k):
        Form.__init__(self, *a, **k)
        self.sgf = None

    def validate(self):
        if not Form.validate(self):
            return False
        f_sgf = None
        if self.url.data:
            try:
                f_sgf = urllib.urlopen(self.url.data)
            except IOError:
                self.url.errors = ("Invalid url.",)
                return False
        elif self.file.data:
            f_sgf = self.file.data
            if not f_sgf.filename.endswith("sgf"):
                self.url.errors = ("Invalid file extension. Expected .sgf file.",)
                return False
        else:
            self.url.errors = ("One of the fields must be filled.",)
            return False
        assert(f_sgf)
        self.sgf = f_sgf.read()
        return True

class GameEditForm(Form):
    """Form for editing game metainformation (players, result, etc.)."""
    result = TextField("Result", [validators.Required()])
    event = TextField("Event")

    def update_game(self, game):
        game.event = self.event.data
        game.result = self.result.data
        db.update_game(game)

    @staticmethod
    def form_factory(game_type):
        return {"hex": HexGameEditForm,
                "go" : GoGameEditForm}[game_type]

class GoGameEditForm(GameEditForm):
    """Form for editing game metainformation (players, result, etc.)."""
    black = TextField("Black", [validators.Required()])
    white = TextField("White", [validators.Required()])
    komi = FloatField("Komi")
    handicap = IntegerField("Handicap")
    black_rank = TextField("Black Rank")
    white_rank = TextField("White Rank")

    def update_game(self, game):
        game.player1 = self.black.data
        game.player2 = self.white.data
        if self.komi.data is not None:
            game.komi = self.komi.data
        if self.handicap.data is not None:
            game.handicap = self.handicap.data
        if self.black_rank is not None:
            game.player1_rank = self.black_rank.data
        if self.white_rank is not None:
            game.player2_rank = self.white_rank.data
        super(GoGameEditForm, self).update_game(game)

class HexGameEditForm(GameEditForm):
    """Form for editing game metainformation (players, result, etc.)."""
    red = TextField("Red", [validators.Required()])
    blue = TextField("Blue", [validators.Required()])

    def update_game(self, game):
        game.player1 = self.red.data
        game.player2 = self.blue.data
        super(HexGameEditForm, self).update_game(game)

class CommentForm(Form):
    """
    Form for commenting upon moves in the game.

    Comment is always attached to current variation in the game.
    Comments allow markup for navigations within game.
    """
    comment = TextAreaField("Comment", [validators.Required()])
    # following fields are hidden
    # path is encoded in JSON format as [[branch node], [branch node]]
    short_path_json = HiddenField("Short Path", [validators.Required()])

    def __init__(self, *a, **k):
        Form.__init__(self, *a, **k)
        self.short_path = None

    def validate(self):
        if not Form.validate(self):
            return False
        try:
            self.short_path = json.loads(self.short_path_json.data)
        except ValueError:
            # TODO logging
            self.comment.errors.append("Server upload error")
            return False
        # sanity check for short path
        for elem in self.short_path:
            if type(elem) != list or len(elem) != 2:
                self.comment.errors.append("Server upload error")
                return False
        return True

class SignupForm(Form):
    """Form for new user registration."""
    username = TextField("Username", [validators.Required()])
    password = PasswordField("Password", [validators.Required()])
    email = TextField("Email", [validators.Required()])

    def validate(self):
        if not Form.validate(self):
            return False
        user = db.get_user_by_username(self.username.data)
        if user is not None:
            self.username.errors.append("Username exists")
            return False
        return True

class LoginForm(Form):
    """Form for login with registered username."""
    username = TextField("Username", [validators.Required()])
    password = PasswordField("Password", [validators.Required()])

    def __init__(self, *a, **k):
        Form.__init__(self, *a, **k)
        self.user = None

    def validate(self):
        if not Form.validate(self):
            return False
        self.user = db.get_user_by_username(self.username.data)
        if self.user is None:
            self.username.errors = ("Unknown username",)
            return False
        if not check_password_hash(self.user.passwd, self.password.data):
            self.password.errors = ("Invalid password",)
            return False
        return True
