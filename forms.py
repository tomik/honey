
import urllib
import json

from flaskext.wtf import Form, HiddenField, IntegerField, PasswordField, TextField, TextAreaField, validators
from werkzeug import check_password_hash

from db import get_user, get_game

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
    # hidden field
    game_id = HiddenField("GameId", [validators.Required()])
    # hidden field
    # path is encoded in JSON format as [[branch node], [branch node]]
    path_json = HiddenField("Path", [validators.Required()])

    def __init__(self, *a, **k):
        Form.__init__(self, *a, **k)
        self.path = None
        self.game = None

    def validate(self):
        if not Form.validate(self):
            return False
        try:
            self.path = json.loads(self.path_json.data)
        except ValueError:
            # TODO logging
            self.comment.errors.append("Server upload error")
            return False
        self.game = get_game(self.game_id.data)
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
        user = get_user(self.username.data)
        if user is not None:
            self.username.errors.append("Username exists")
            return False
        return True

class LoginForm(Form):
    """Form for login with registered username."""
    username = TextField("Username", [validators.Required()])
    password = PasswordField("Password", [validators.Required()])

    def validate(self):
        if not Form.validate(self):
            return False
        user = get_user(self.username.data)
        if user is None:
            self.username.errors = ("Unknown username",)
            return False
        if not check_password_hash(user["passwd"], self.password.data):
            self.password.errors = ("Invalid password",)
            return False
        return True
