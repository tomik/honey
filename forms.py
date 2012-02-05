
import urllib

from flaskext.wtf import IntegerField, Form, PasswordField, TextField, validators
from werkzeug import check_password_hash

from db import get_user

class SgfUploadForm(Form):
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
        if self.url.data:
            try:
                self.sgf = urllib.urlopen(self.url.data)
            except IOError:
                self.url.errors = ("Invalid url.",)
                return False
        elif self.file.data:
            pass
        elif self.lg.data:
            self.lg_id = self.lg.data
        else:
            self.url.errors = ("One of the fields must be filled.",)
            return False
        return True

class SignupForm(Form):
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
