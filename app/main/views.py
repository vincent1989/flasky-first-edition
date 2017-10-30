# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from datetime import datetime
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for


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
        print form.name.data
        user = User.query.filter_by(username=form.name.data).first()
        print user
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

