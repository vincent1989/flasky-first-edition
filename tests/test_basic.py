# -*- coding: utf-8 -*-
__author__ = 'vincent'

import unittest
from flask import current_app
from app import create_app, db

class BasicsTestCase(unittest.TestCase):
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

    def tearDown(self):
        '''
        这是测试完成之后会自动运行的方法，本方法将删除 程序上下文和数据库
        '''
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        '''
        确保程序实例存在
        '''
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        '''
        确保程序在测试配置中运行
        '''
        self.assertTrue(current_app.config['TESTING'])
