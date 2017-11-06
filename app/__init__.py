# -*- coding: utf-8 -*-
__author__ = 'vincent'

from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown

from config import config

# 实例化一个LoginManager实例
login_manager = LoginManager()
# 设置登录的 会话保护，session_protection 可选值：None 不保护, basic 基本级别, strong 强级别
# 当 session_protection 设置为 strong 时 FLask-Login 会记录客户端IP地址和浏览器的用户代理信息，如果发现异动就登出用户
login_manager.session_protection = 'strong'
# 设置登录页面的端点
login_manager.login_view = 'auth.login'

pagedown = PageDown()
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # app 初始化 pagedown
    pagedown.init_app(app)
    # app 初始化 bootstrap
    bootstrap.init_app(app)
    # app 初始化 mail
    mail.init_app(app)
    # app 初始化 moment
    moment.init_app(app)
    # app 初始化 db
    db.init_app(app)
    # app 初始化 login_manager
    login_manager.init_app(app)

    # 注册蓝本 main
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # 注册蓝本 auth
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # 附加路由和自定义页面
    return app