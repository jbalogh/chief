from wtforms import Form, TextField, PasswordField, validators

import settings


class DeployForm(Form):
    ref = TextField('git ref', [validators.Required()])
    password = PasswordField('secret', [validators.Required()])
    who = TextField('identify yourself', [validators.Required()])
