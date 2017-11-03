# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from datetime import datetime
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import abort



from . import main
from .forms import NameForm
from .. import db
from ..models import User

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
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    render_template('user.html', user=user)