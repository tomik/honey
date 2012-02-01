
from flaskext.wtf import Form, PasswordField, TextField, validators


class SignupForm(Form):
    username = TextField("Username", [validators.Required()])
    password = PasswordField("Password", [validators.Required(),
        validators.EqualTo("confirm", message="Passwords must match.")])
    confirm = PasswordField("Confirm Password", [validators.Required()])
    # TODO email field ?
    email = TextField("email", [validators.Required()])

class LoginForm(Form):
    username = TextField("Username", [validators.Required()])
    password = PasswordField("Password", [validators.Required()])

