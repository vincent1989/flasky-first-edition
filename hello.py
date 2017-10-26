# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import abort
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

from datetime import datetime

app = Flask(__name__)
# 注意 'SECRET_KEY'这个配置值是一个加密密匙，上线时时不能直接写在代码中的，应当写入外部环境变量中
app.config['SECRET_KEY'] = 'hard to guess string'
# 通过命令行方式管理 app
manager = Manager(app)
# 添加 Bootstrap
bootstrap = Bootstrap(app)

# 添加 Moment
moment = Moment(app)


class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    # 注意，验证函数 Required() 可以验证数据不为空
    submit = SubmitField('Submit')




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name!=form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        return redirect(url_for('index', current_time=datetime.utcnow()))
    return render_template('index.html', current_time=datetime.utcnow(), form=form, name=session.get('name'))

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)




if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()