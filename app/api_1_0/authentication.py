# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask import g
from flask import jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User
from ..models import AnonymousUser

from .errors import forbidden
from .errors import unauthorized

from . import api

reload(sys)
sys.setdefaultencoding("utf-8")


auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(email_or_token, password):
    '''验证用户密码'''
    if email_or_token =='':
        # 没有邮件或密码阿德情况下默认设置为 匿名用户
        g.current_user = AnonymousUser
        return True

    if password == '':
        # 没有密码的情况下，需要验证 token 值，如果 token 验证通过，则返回对应用户，且设置 token_used 属性， 否则返回False
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    # 根据邮件名提取用户，如果用户不存在，则返回False
    user = User.query.filter_by(email=email_or_token).first()
    if not  user:
        return False
    # 如果用户存在，则设置用户，并验证用户密码
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.route('/token')
def get_token():
    '''获取token'''
    if g.current_user.is_anonymous or g.token_used:
        # 如果是匿名用户，或者是 token 方式访问，则拒绝相关操作
        return unauthorized('相关参数设置有误')
    return jsonify(
        {
            'token' : g.current_user.generate_auth_token(expiration=3600),
            'expiration' : 3600
        }
    )


# 通过如下方法，api 蓝本中所有路由都能进行自动认证。
# 而且作为附加认证，before_request 处理程序还会拒绝已通过认证，但没有确认账户的用户
@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


