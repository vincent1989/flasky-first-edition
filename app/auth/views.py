# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys

from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import flash

from flask.ext.login import login_required
from flask.ext.login import login_user
from flask.ext.login import logout_user

from . import auth
from ..models import User
# 导入登录表单
from .forms import LoginForm


reload(sys)
sys.setdefaultencoding("utf-8")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 创建一个LoginForm对象
    form = LoginForm()
    # 当表单以POST方式传输时，form.validate_on_submit() 将验证表单数据
    if form.validate_on_submit():
        # 根据用户填写的邮箱名获取用户对象
        user = User.query.filter_by(email=form.email.data).first()
        # 用户对象不为空，且密码验证通过
        if user is not None and user.verify_passowrd(form.password.data):
            # login_user 标记用户已登录;
            # 如果remember 为Flase，则关闭浏览器之后，用户会话就会过期，下次用户访问时就需要重新登录
            # 如果remember 为True，则会在用户浏览器中写入一个长期的有效的cookit，使用这个cookit 可以复现用户回话
            login_user(user, remember=form.remember_me.data)
            # 登录成功后跳转有两种可能：
            # 1. 用户访问未授权的URL时会显示登录表单，Flask-Login会把原地址保存在 request.args 字典的 next 中，如果查询没有 next,则跳转到首页
            return redirect(request.args.get('next') or url_for('main.index'))
        # 如果没有用户，或者密码错误，则会给用户一个flash 并重新渲染登录表单，让用户重新登录
        # flash('Invalid username or password')
        flash('无效的用户名或密码')
    return render_template('auth/login.html', form=form)



@auth.route('/logout')
@login_required
def logout():
    # 删除并重设用户会话
    logout_user()
    # 提醒用户
    # flash('you have been logged out')
    flash('您已登出')
    # 重定向到首页
    return redirect(url_for('main.index'))



@auth.route('/secret')
@login_required
def secret():
    # 未登录的用户，将被 Flask-Login 拦截，然后显示本方法的提示，并把用户发往登录页面
    return 'Only authenticated users are allowed!'
