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
from flask_login import login_required
from flask_login import current_user



from . import main
from .forms import NameForm
from .forms import EditProfileForm
from .forms import EditProfileAdminForm

from .. import db
from ..models import User
from ..models import Role
from ..decorators import admin_required


reload(sys)
sys.setdefaultencoding("utf-8")

@main.route('/', methods=['GET', 'POST'])
def index():
    form=NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is not None:
            session['name'] = form.name.data
            return redirect(url_for('.index',
                                    current_time=datetime.utcnow(),
                                    know=True,
                                    name=user.username))

    return render_template('index.html',
                               form=form,
                               name=session.get('name'),
                               know=session.get('know', False),
                               current_time=datetime.utcnow())


@main.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
    '''用户资料页面'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)


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