# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask_wtf import Form
from wtforms import StringField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Email

reload(sys)
sys.setdefaultencoding("utf-8")

class LoginForm(Form):
    # email 字段验证：必填验证，长度范围1-64， 邮件格式验证
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])

    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')