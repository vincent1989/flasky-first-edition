# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys

from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import flash

'''
注意 Flask-Login 提供的 login_required 方法修饰器能够保护可以保护路由， 执行被修饰的方法时会先验证用户有没有登录。
'''
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from flask_login import current_user

from . import auth
from ..models import User
# 导入登录表单
from .forms import LoginForm
from .forms import RegistrationForm
from .forms import ChangePasswordForm
from .forms import PasswordResetForm
from .forms import PasswordResetRequestForm
from .forms import ChangeEmailForm
from .. import db
from ..email import send_mail


reload(sys)
sys.setdefaultencoding("utf-8")


@auth.before_app_request
def before_request():
    '''
    功能：在 before_app_request 处理程序中 过滤未确认的账户
    满足以下三个条件时，before_app_request 程序会拦截请求
    1. 用户已登录 （current_user.is_authenticated 返回 True）
    2. 用户账户还没有确认
    3. 请求的端点 （使用request.endpoint获取）不在认证蓝本中。
    访问认证路由要获取权限，因为这些路由的作用就是要用户确认账户或者执行其他账户相关操作

    如果请求满足以上三条，则会被重定向到 /auth/unconfirmed 路由，显示一个确认账户相关信息的页面
    '''
    if current_user.is_authenticated:
        # 如果用户已经登录，则更新用户的最后访问时间
        current_user.ping()

        if (not current_user.confirmed
            and request.endpoint
            and request.endpoint[:5] != 'auth.'
            and request.endpoint != 'static'):
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')



@auth.route('/confirm/<token>', methods=['GET', 'POST'])
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if current_user.confirm(token):
        flash('您的邮箱验证成功，非常感谢')
    else:
        flash('当前连接已失效，验证失败')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    '''
    为已登陆用户 重新发送账户确认邮件
    '''
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email,
              '确认您的账户',
              'auth/email/confirm',
              user=current_user,
              token=token)
    flash('一个新的账户确认邮件已发送到您的邮箱，请前往确认.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        # 获取用户令牌
        token = user.generate_confirmation_token()
        # 发送邮件
        send_mail(user.email, '请确认您的帐号', 'auth/email/confirm', user=user, token=token)
        flash('一个帐号确认邮件已发到您的邮箱，请前往确认')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 创建一个LoginForm对象
    form = LoginForm()
    # 当表单以POST方式传输时，form.validate_on_submit() 将验证表单数据
    if form.validate_on_submit():
        # 根据用户填写的邮箱名获取用户对象
        user = User.query.filter_by(email=form.email.data).first()
        # 用户对象不为空，且密码验证通过
        if user is not None and user.verify_password(form.password.data):
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


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    '''
    已登陆情况下，用户可以直接修改密码
    '''
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('您的密码修改成功')
            return redirect(url_for('main.index'))
        else:
            flash('密码无效')
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    '''
    未登录情况下的密码修改前，需要发送验证邮件
    '''
    if not current_user.is_anonymous:
        # 如果不是匿名用户, 则跳转至首页
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_mail(user.email,
                      '重设您的密码',
                      'auth/email/reset_password',
                      user=user,
                      token=token,
                      next=request.args.get('next'))
        flash('一个密码重置的邮件已发送到您的邮箱，请查收!')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        # 如果不是匿名用户, 则跳转至首页
        return redirect(url_for('main.index'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            # 未找到用户时，跳转至首页
            return redirect(url_for('main.index'))

        if user.reset_password(token, form.password.data):
            flash('您的密码修改成功')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    '''
    已登陆用户 发送密码修改的 token
    '''
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_mail(new_email,
                      '邮箱地址验证通知',
                      'auth/email/change_email',
                      user=current_user,
                      token=token)
            flash('一封邮箱地址验证邮件已发送到你的新邮箱中，请前往确认！')
            return redirect(url_for('main.index'))
        else:
            flash('无效的邮箱或密码')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    '''
    已登陆用户 密码修改
    '''
    if current_user.change_email(token):
        flash('您的邮件地址已更新')
    else:
        flash('无效的请求')
    return redirect(url_for('main.index'))


