# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
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
    name = None
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data=''
    return render_template('index.html', current_time=datetime.utcnow(), form=form, name=name)

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)




if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()