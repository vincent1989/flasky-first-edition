# -*- coding: utf-8 -*-
import os
from threading import Thread
from flask import Flask
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import abort
from flask.ext.script import Manager
from flask.ext.script import Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail, Message

# 注意 书中介绍使用下面这行导入包，但是实际运行过程中发现该包已经更换了名字，更换成FlaskForm,特此说明
# from flask.ext.wtf import Form
from flask.ext.wtf import FlaskForm

from wtforms import StringField, SubmitField
# 下面这一行的包处于将废弃的状态
# from wtforms.validators import Required
from wtforms.validators import DataRequired

# 导入数据库ORM
from flask.ext.sqlalchemy import SQLAlchemy

from datetime import datetime

# 先配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# 注意 'SECRET_KEY'这个配置值是一个加密密匙，上线时时不能直接写在代码中的，应当写入外部环境变量中
app.config['SECRET_KEY'] = 'hard to guess string'
# 数据库相关配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# sqlalchemy_track_modifications增加了很大的开销，将由未来的默认禁用。将其设置为真或假以禁止此警告。“sqlalchemy_track_modifications增加了很大的开销，
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# 设置邮件服务
app.config['MAIL_SERVER'] = 'smtp.mxhichina.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('TEST_MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('TEST_MAIL_PASSWORD')
app.config['FLASKY_ADMIN'] = os.environ.get('TEST_FLASK_ADMIN')

app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
# app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <flasky@example.com>'
app.config['FLASKY_MAIL_SENDER'] = 'LWC<lwc@jiagouyun.com>'
mail = Mail(app)


db = SQLAlchemy(app)

# 添加 Bootstrap
bootstrap = Bootstrap(app)

# 添加 Moment
moment = Moment(app)

# 通过命令行方式管理 app
manager = Manager(app)

# 数据库迁移
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


def make_shell_context():
    # 注册程序，数据库实例以及模型，便于直接导入shell
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    '''
    注意，如果users 不添加 lazy='dynamic'，则执行 user_role.users 会直接执行隐藏的query 方法
    >>> from hello import Role, User
    >>> user_role=Role(name='User')
    >>> users=user_role.users
    >>> users
    >>> [<User u'susan'>, <User u'david'>]
    添加 lazy='dynamic' 之后，则user_role.users 就会返回一个尚未执行的查询语句，这样就能在其后面追加过滤条件了
    '''
    #
    # users = db.relationship('User', backref='role')
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    # primary_key 设置为主键
    id = db.Column(db.Integer, primary_key=True)
    # unique 设置列值不允许重复; index 为该列创建索引，以便提升查询效率
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    def __repr__(self):
        return '<User %r>' % self.username

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    # 注意，验证函数 DataRequired() 可以验证数据不为空
    submit = SubmitField('Submit')

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_mail(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


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
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['know'] = False
            if app.config['FLASKY_ADMIN']:
                send_mail(app.config['FLASKY_ADMIN'],
                          'New User',
                          'mail/new_user',
                          user=user)
        else:
            session['know'] = True
            # flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        form.name.data=''
        return redirect(url_for('index', current_time=datetime.utcnow()))

    return render_template('index.html',
                           current_time=datetime.utcnow(),
                           form=form,
                           name=session.get('name'),
                           know=session.get('know', False))

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)




if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()