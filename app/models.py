# -*- coding: utf-8 -*-
import os

# 导入数据库ORM
from . import login_manager
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

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
    # 邮箱，禁止重复，添加索引
    email = db.Column(db.String(64), unique=True, index=True)
    # unique 设置列值不允许重复; index 为该列创建索引，以便提升查询效率
    username = db.Column(db.String(64), unique=True, index=True)
    # 密码hash值
    password_hash = db.Column(db.String(128))

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_passowrd(self, password):
        return check_password_hash(self.password_hash, password)



@login_manager.user_loader
def load_user(user_id):
    '''当前是加载用户的回调函数， 如果能找到用户，则返回用户对象，否则返回None'''
    return User.query.get(int(user_id))
