# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Email
from wtforms.validators import Regexp
from wtforms.validators import EqualTo

from ..models import User

reload(sys)
sys.setdefaultencoding("utf-8")


class ChangePasswordForm(FlaskForm):
    # 修改密码
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(), EqualTo('password2', message='密码必须匹配')])
    password2 = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class RegistrationForm(FlaskForm):
    # 注册
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    # Regexp(正则表达式，正则表达式的旗标，验证失败后的提示消息)  验证函数，确保输入的用户名只包含 字母数字和下划线
    username = StringField('Username', validators=[DataRequired(),
                                                   Length(1, 64),
                                                   Regexp('^[A-za-z][A-za-z0-9_.]*$',
                                                          0,
                                                          '用户名包含字母、数字、下划线、或点号')])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2', message='密码必须匹配')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮件已注册过')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('当前用户名已注册过')


    

class LoginForm(FlaskForm):
    # email 字段验证：必填验证，长度范围1-64， 邮件格式验证
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])

    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')