# -*- coding: utf-8 -*-
import os
from werkzeug.security import generate_password_hash, check_password_hash
'''
# 用户模型必须实现 82页：表8-1 所需要的四个方法，如下：
# is_authenticated 如果用户已登录，则返回True，否则返回False
# is_active 如果允许用户登录，则返回True，否则返回False
# is_anonymous 对普通用户必须返回False
# get_id 必须返回用户的唯一标示符，使用unicode 编码字符串
可以使用 Flask-Login 提供的UserMixin类，就自动拥有以上四种方法了
'''
from flask_login import UserMixin

# 下面这个包 itsdangerous 用于生成确认令牌
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

from . import db, login_manager


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

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # primary_key 设置为主键
    id = db.Column(db.Integer, primary_key=True)
    # 邮箱，禁止重复，添加索引
    email = db.Column(db.String(64), unique=True, index=True)
    # unique 设置列值不允许重复; index 为该列创建索引，以便提升查询效率
    username = db.Column(db.String(64), unique=True, index=True)
    # 密码hash值
    password_hash = db.Column(db.String(128))

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # 用于用户确认验证
    confirmed = db.Column(db.Boolean, default=False)


    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        # 生成一个用户令牌，有效期默认为1小时
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id})

    def confirm(self, token):
        # 验证用户令牌，如果验证通过，则设置 confirmed 属性为True
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        '''
        密码 邮件 重置时生成用户 token
        '''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset':self.id})

    def reset_password(self, token, new_password):
        '''
        重置密码，重置前验证token
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('reset') !=self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        '''
        获取邮件重置时的 token
        '''
        s=Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email':self.id, 'new_email': new_email})

    def change_email(self, token):
        '''
        重置密码，重置前验证token
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('change_email') !=self.id:
            return False

        new_email = data.get('new_email')
        if new_email is None:
            return False

        if self.query.filter_by(email=new_email).first() is not None:
            # 新邮件在 用户列表中应当不存在，否则返回False
            return False

        self.email = new_email
        db.session.add(self)
        return True

@login_manager.user_loader
def load_user(user_id):
    '''当前是加载用户的回调函数， 如果能找到用户，则返回用户对象，否则返回None'''
    return User.query.get(int(user_id))
