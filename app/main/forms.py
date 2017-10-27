# -*- coding: utf-8 -*-
__author__ = 'vincent'

from flask import render_template
from . import main

# 注意 书中介绍使用下面这行导入包，但是实际运行过程中发现该包已经更换了名字，更换成FlaskForm,特此说明
# from flask.ext.wtf import Form
from flask.ext.wtf import FlaskForm

from wtforms import StringField, SubmitField
# 下面这一行的包处于将废弃的状态
# from wtforms.validators import Required
from wtforms.validators import DataRequired

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    # 注意，验证函数 DataRequired() 可以验证数据不为空
    submit = SubmitField('Submit')