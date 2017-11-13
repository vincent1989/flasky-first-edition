# -*- coding: utf-8 -*-
__author__ = 'vincent'

import unittest
import time
import re
from flask import current_app
from flask import url_for
from app import create_app, db
from app.models import User
from app.models import Role
from app.models import Follow
from app.models import Permission
from app.models import AnonymousUser

from datetime import datetime

class FlaskClientTestCase(unittest.TestCase):

    def setUp(self):
        '''
        该方法创建一个测试环境，类似与运行中的环境
        '''
        # 使用测试配置创建一个程序
        self.app = create_app('testing')
        # 激活上下文
        self.app_context = self.app.app_context()
        # 推送程序上下文
        self.app_context.push()
        # 创建一个全新的数据库
        db.create_all()
        Role.insert_roles()
        # 创建Flask测试客户端对象，在该对象上可调用方法向程序发起请求。
        # 如果测试客户端启用了 use_cookies 选项，那么这个客户端就能像浏览器一样接收和发送 cookie,因此能够使用依赖cookie的功能记住请求之间的上下文
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        '''
        这是测试完成之后会自动运行的方法，本方法将删除 程序上下文和数据库
        '''
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue('Stranger' in response.get_data(as_text=True))

    def test_register_and_login(self):
        # 注册新用户
        response = self.client.post(
            url_for('auth.register'),
            data={
                'email' : 'john@example.com',
                'username' : 'john',
                'password' : 'cat',
                'password2': 'cat'
            }
        )
        # /auth/register 路由有两种响应方式：
        # 1. 如果注册数据可用，会返回一个重定向，把用户转到登录页面
        # 2. 如果注册数据不可用的情况下, 返回的响应会再次渲染注册表单。 而且还包含适当的错误信息
        # 为了确认注册成功，测试会检测响应返回的状态吗是否为 302 ，这个代码表示重定向
        self.assertTrue(response.status_code == 302)

        # 使用新注册的帐号登录
        response = self.client.post(
            url_for('auth.login'),
            data={
                'email' : 'john@example.com',
                'password' : 'cat',
            },
            follow_redirects=True
        )
        # 注意发送post请求时，设置参数 follow_redirects=True，让客户端和浏览器一样，自动向重定向的URL发起GET请求。
        # 指定该参数之后，返回的不再是 302 状态吗而是请求重定向的URL 返回的响应。
        data = response.get_data(as_text=True)
        self.assertTrue(re.search(b'Hello, john', data))
        self.assertTrue(b'一个帐号确认邮件已发到您的邮箱，请前往确认' in data)

        # 发送确认令牌
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(b'您的邮箱验证成功，非常感谢' in data)


        # 退出
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(b'您已登出' in data)

