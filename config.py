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
    # SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮件服务相关
    # 邮件标题 的 前缀
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    # 邮件发送者名称
    FLASKY_MAIL_SENDER = os.environ.get('FLASKY_MAIL_SENDER')
    # 管理员邮箱
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.mxhichina.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('DEV_MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('DEV_MAIL_PASSWORD')
    # 数据库URL
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    # 数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
    # 数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development' : DevelopmentConfig,
    'testing' : TestingConfig,
    'production':ProductionConfig,

    'default' : DevelopmentConfig
}

