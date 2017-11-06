# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from datetime import datetime
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import abort
from flask import flash
from flask import request
from flask import current_app
from flask_login import login_required
from flask_login import current_user

from . import main
from .forms import NameForm
from .forms import EditProfileForm
from .forms import EditProfileAdminForm
from .forms import PostForm

from .. import db
from ..models import User
from ..models import Role
from ..models import Post
from ..decorators import Permission
from ..decorators import admin_required


reload(sys)
sys.setdefaultencoding("utf-8")

@main.route('/', methods=['GET', 'POST'])
def index():
    form=PostForm()
    # 判断有没有博文的编辑权限
    if (current_user.can(Permission.WRITE_ARTICLES)
        and form.validate_on_submit()):
        # current_user 的 _get_current_object() 方法是有 Flask-Login提供的，它包含真正的用户对象
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    # 注意：为显示某页中的数据，需要把all()方法替换为Flask-SQLAlchemy 提供的 paginate()方法，
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page,  # 表示页数
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], # 表示每页展示的记录数量
        error_out=False  # 当请求页数超出范围之后，如果error_out=True,则返回404错误，否则返回一个空列表
    )
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)



@main.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
    '''用户资料页面'''
    # 获取用户
    user = User.query.filter_by(username=username).first_or_404()
    # 获取页号
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, # 页码
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],  # 每页的显示数量
        error_out=False  # 超出页码范围之后返回空列表
    )
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''用户级别的-资料编辑'''
    form = EditProfileForm()
    if form.validate_on_submit():
        # 如果表单验证通过则，进行更新操作
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('您的资料已更新！')
        return redirect(url_for('.user', username=current_user.username))

    form.name.data = current_user.name
    form.location  = current_user.location
    form.about_me  = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    '''管理员级别-资料编辑'''
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email    = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role     = Role.query.get(form.role.data)
        user.name     = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('当前用户配置已更新完毕！')
        return redirect(url_for('.user', username=user.username))

    form.email.data     = user.email
    form.username.data  = user.username
    form.confirmed.data = user.confirmed
    form.role.data      = user.role.id
    form.name.data      = user.name
    form.location.data  = user.location
    form.about_me.data  = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
