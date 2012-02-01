
from flaskext.wtf import Form, PasswordField, TextField, validators
from werkzeug import check_password_hash

from db import get_user

class SignupForm(Form):
    username = TextField("Username", [validators.Required()])
    password = PasswordField("Password", [validators.Required()])
    email = TextField("email", [validators.Required()])

    def validate(self):
        print(self)
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
