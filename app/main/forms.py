# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask import render_template
from . import main

# 注意 书中介绍使用下面这行导入包，但是实际运行过程中发现该包已经更换了名字，更换成FlaskForm,特此说明
# from flask.ext.wtf import Form
from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from flask_pagedown.fields import PageDownField
# 下面这一行的包处于将废弃的状态
# from wtforms.validators import Required
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Email
from wtforms.validators import Regexp
from wtforms.validators import ValidationError

from ..models import Role
from ..models import User

reload(sys)
sys.setdefaultencoding("utf-8")

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    # 注意，验证函数 DataRequired() 可以验证数据不为空
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    '''用户级别的-资料编辑表单'''
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('保存')


class EditProfileAdminForm(FlaskForm):
    '''管理员级别-资料编辑表单'''

    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64), Regexp(
        '^[a-zA-Z][a-zA-Z0-9_.]*$',
        0,
        '用户名必须已字母开头，只能包含大小写字母，数字，下划线或点号'
    )])
    confirmed = BooleanField('Confirmed')
    # SelectField 实例必须在 choices 属性中设置各选项，选项必须时一个元组组成的列表，
    # 各元组必须包含两个元素：选项的标识符 和 显示在控件中的文本字符串
    # 本例中 元组中的标识符是 角色ID，角色名
    # 另外 coerce=int 是为了保证SelectField的data 值为整数
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('保存')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        '''验证有效性'''
        if (field.data != self.user.email
            and User.query.filter_by(email=field.data).first()):
            raise ValidationError('邮件已被注册！')

    def validate_username(self, field):
        '''验证用户名有效性'''
        if (field.data != self.user.username
            and User.query.filter_by(username=field.data).first()):
            raise ValidationError('用户名已被注册！')

class PostForm(FlaskForm):
    '''帖子内容提交表单'''
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    '''帖子的评论提交表单'''
    body = StringField('输入您的评论', validators=[DataRequired()])
    submit = SubmitField('提交')
