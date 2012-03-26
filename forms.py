
import urllib
import json
import re

from flaskext.wtf import Form, HiddenField, IntegerField, PasswordField, TextField, TextAreaField, validators
from werkzeug import check_password_hash

import db

class SgfUploadForm(Form):
    """Form for uploading sgf games. Uploaded games are stored in the database."""
    url = TextField("Url")
    file = TextField("File")
    lg = TextField("LG game")

    def __init__(self, *a, **k):
        Form.__init__(self, *a, **k)
        self.sgf = None
        self.lg_id = None

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
            pass
        elif self.lg.data:
            try:
                f_sgf = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % self.lg.data)
            except IOError:
                self.url.errors = ("Invalid lg game id or server down.",)
                return False
        else:
            self.url.errors = ("One of the fields must be filled.",)
            return False
        assert(f_sgf)
        self.sgf = " ".join(f_sgf.readlines())
        return True

class CommentForm(Form):
    """
    Form for commenting upon moves in the game.

    Comment is always attached to current variation in the game.
    Comments allow markup for navigations within game.
    """
    comment = TextAreaField("Comment", [validators.Required()])
    # following fields are hidden
    game_id = HiddenField("GameId", [validators.Required()])
    # path is encoded in JSON format as [[branch node], [branch node]]
    short_path_json = HiddenField("Short Path", [validators.Required()])
    # path is encoded in JSON format as [{"W": "bb"}, {"B": "dd"}]
    full_path_json = HiddenField("Full Path", [validators.Required()])

    def __init__(self, *a, **k):
        Form.__init__(self, *a, **k)
        self.short_path = None
        self.full_path = None
        self.game = None

    def validate(self):
        if not Form.validate(self):
            return False
        try:
            self.short_path = json.loads(self.short_path_json.data)
            self.full_path = json.loads(self.full_path_json.data)
        except ValueError:
            # TODO logging
            self.comment.errors.append("Server upload error")
            return False
        # sanity check for short path
        for elem in self.short_path:
            if type(elem) != list or len(elem) != 2:
                self.comment.errors.append("Server upload error")
                return False
        # sanity check for full path
        for elem in self.full_path:
            if type(elem) != dict or \
               len(elem) != 1 or \
               elem.keys()[0] not in ["W", "B"] or \
               not re.match(r"[a-z][a-z]", elem.values()[0]):
                self.comment.errors.append("Server upload error")
                return False
        self.game = db.get_game(self.game_id.data)
        if not self.game:
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
