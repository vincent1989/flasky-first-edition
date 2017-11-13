# -*- coding: utf-8 -*-

__author__ = 'vincent'

import os

# 获取当前目录
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 密匙相关
    SECRET_KEY = os.environ.get('TEST_SECRET_KEY') or 'hard to guess string'

    # DB 相关
    # 开启自动提交
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # 避免内存开销太大，所以禁止此项
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 邮件服务相关
    MAIL_SERVER = 'smtp.mxhichina.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('DEV_MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('DEV_MAIL_PASSWORD')
    # 邮件标题 的 前缀
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    # 邮件发送者名称
    FLASKY_MAIL_SENDER = os.environ.get('FLASKY_MAIL_SENDER')
    # 管理员邮箱
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    # 分页中，每页默认现实的条目数量
    FLASKY_POSTS_PER_PAGE = 20

    # 每页的 关注着 数量
    FLASKY_FOLLOWERS_PER_PAGE = 50
    # 每页的 评论信息 数量
    FLASKY_COMMENTS_PER_PAGE = 30
    #
    FLASKY_SLOW_DB_QUERY_TIME = 0.5


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    # 数据库URL
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    # 测试客户端可以使用 post() 方法发送包含表单数据的 POST请求，不过提交表单时会有一个小麻烦。
    # Flask-WTF生成的表单中包含一个隐藏字段，其内容就是CSRF令牌，需要和表单中的数据一起提交。
    # 为了复现这个功能，测试必须请求包含表单的页面，然后解析响应返回的HTML代码并提取令牌，这样才能把令牌和表单中的数据一起发送。
    # 为了避免在测试中处理 CSRF 令牌操作，可以通过在 测试的配置文件中禁用CSRF保护功能，设置 WTF_CSRF_ENABLE = False
    WTF_CSRF_ENABLED = False
    # 数据库URL
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
    # 数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')





config = {
    'development' : DevelopmentConfig,
    'testing' : TestingConfig,
    'production':ProductionConfig,

    'default' : DevelopmentConfig
}

