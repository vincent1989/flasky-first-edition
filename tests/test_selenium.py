# -*- coding: utf-8 -*-
__author__ = 'vincent'

import unittest
import time
import re
import threading
import json
from base64 import b64encode
from flask import url_for
from app import create_app, db
from app.models import User
from app.models import Role
from app.models import Post
from app.models import Comment
from app.models import Follow
from app.models import Permission
from app.models import AnonymousUser
from selenium import webdriver

from datetime import datetime
import traceback

class SeleniumTestCase(unittest.TestCase):
    client = None

    '''
    说明：
    setUpClass() 和 tearDownClass() 类方法分别在这个类中的全部测试运行前／后执行
    setUp() 和 tearDown() 方法则是在每个测试运行前／后执行
    '''


    @classmethod
    def setUpClass(cls):
        '''
        该方法创建一个测试环境，类似与运行中的环境
        '''
        # 启动Google 浏览器
        options = webdriver.ChromeOptions()
        options.add_argument('/Users/vincent/Downloads/chromedriver')
        # options.add_argument('headless')
        try:
            cls.client = webdriver.Chrome('/Users/vincent/Downloads/chromedriver', chrome_options=options)

        except:
            print traceback.format_exc()
            pass

        if  cls.client:
            # 使用测试配置创建一个程序
            cls.app = create_app('testing')
            # 激活上下文
            cls.app_context = cls.app.app_context()
            # 推送程序上下文
            cls.app_context.push()

            # 禁止日志，保持输出简洁
            import logging
            logger = logging.getLogger('Werkzeng')
            # logger.setLevel('ERROR')

            # 创建一个全新的数据库, 并添加一些虚拟数据
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Post.generate_fake(10)

            # 添加管理员
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(
                email='john@example.com',
                username='john',
                password='cat',
                role=admin_role,
                confirmed=True
            )
            db.session.add(admin)
            db.session.commit()

            # 在一个线程中启动 Flask 服务
            threading.Thread(target=cls.app.run, kwargs={'debug': False}).start()

            time.sleep(2)


    @classmethod
    def tearDownClass(cls):
        '''
        这是测试完成之后会自动运行的方法，本方法将删除 程序上下文和数据库
        '''
        if cls.client:
            # 关闭 Flask 服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            # 销毁数据库
            db.drop_all()
            db.session.remove()
            # 删除程序上下文
            cls.app_context.pop()



    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass


    def test_admin_home_page(self):

        # 测试主页
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello,\sStranger', self.client.page_source))

        # 测试主页登录页面
        self.client.find_element_by_link_text('登录').click()
        self.assertIn('<h1>Login</h1>', self.client.page_source)

        # 登录
        self.client.find_element_by_name('email').send_keys('john@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('Hello,\sjohn', self.client.page_source))

        # 导航到用户的配置主页
        self.client.find_element_by_link_text('Profile').click()
        print self.client.page_source
        self.assertIn('<h1>john!</h1>', self.client.page_source)
