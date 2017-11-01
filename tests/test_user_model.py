# -*- coding: utf-8 -*-
__author__ = 'vincent'

import unittest
import time
from flask import current_app
from app import create_app, db
from app.models import User

class UserModelTestCase(unittest.TestCase):

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


    def test_password_setter(self):
        '''
        测试，用户米密码设置不为空
        '''
        u=User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def  test_no_password_getter(self):
        '''
        测试 用户的密码属性 不可读验证
        :return:
        '''
        u=User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        '''
        验证 密码验证函数是否正确
        '''
        u = User(password='cat')
        self.assertTrue(u.verify_passowrd('cat'))
        self.assertFalse(u.verify_passowrd('dog'))


    def test_password_salts_are_random(self):
        '''
        验证不同用户，相同密码时，密码的hash是不同的
        '''
        u=User(password='cat')
        u2=User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_vaild_confirmation_token(self):
        '''
        测试用户令牌生成函数，验证2个令牌之间是否相同
        '''
        u=User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_confirmation_token_is_ramdom(self):
        '''
        测试用户令牌是随机的
        '''
        u=User(password='cat')
        db.session.add(u)
        db.session.commit()
        t1 = time.time()
        token1 = u.generate_confirmation_token()
        t2 = time.time()
        token2 = u.generate_confirmation_token()
        time.sleep(1)
        t3 = time.time()
        token3 = u.generate_confirmation_token()
        time.sleep(2)
        t4 = time.time()
        token4 = u.generate_confirmation_token()

        # 同一时间戳下，token 相同
        self.assertTrue(token1 == token2)
        # 间隔
        self.assertTrue(token2 != token3)
        self.assertTrue(token3 != token4)


    def test_invalid_confirmation_token(self):
        '''
        测试 2个用户之间交换令牌 是无法验证通过的
        '''
        u=User(password='cat')
        u2=User(password='cat')
        db.session.add(u, u2)
        db.session.commit()

        token = u.generate_confirmation_token()
        token2 = u2.generate_confirmation_token()
        self.assertFalse(u.confirm(token2))
        self.assertFalse(u2.confirm(token))


    def test_expired_confirmation_token(self):
        '''
        验证用户令牌过期时间
        '''
        u=User(password='cat')
        db.session.add(u)
        db.session.commit()

        token = u.generate_confirmation_token(expiration=2)
        time.sleep(3)
        self.assertFalse(u.confirm(token))
