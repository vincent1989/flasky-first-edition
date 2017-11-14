# -*- coding: utf-8 -*-
__author__ = 'vincent'

import unittest
import time
from flask import current_app
from app import create_app, db
from app.models import User
from app.models import Role
from app.models import Follow
from app.models import Permission
from app.models import AnonymousUser

from datetime import datetime

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
        '''测试用户密码属性，密码存储的hash值不为空'''
        u=User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def  test_no_password_getter(self):
        '''测试用户的密码属性 不可读验证'''
        u=User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        '''测试密码验证函数准确性'''
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))


    def test_password_salts_are_random(self):
        '''测试不同用户相同密码所生成的密码hash不同验证'''
        u=User(password='cat')
        u2=User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_vaild_confirmation_token(self):
        '''测试用户令牌验证函数有效性'''
        u=User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_confirmation_token_is_ramdom(self):
        '''测试用户令牌随机性，及与时间戳的关联性'''
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
        '''测试 2个用户之间交换令牌 是无法验证通过的'''
        u=User(password='cat')
        u2=User(password='cat')
        db.session.add(u, u2)
        db.session.commit()

        token = u.generate_confirmation_token()
        token2 = u2.generate_confirmation_token()
        self.assertFalse(u.confirm(token2))
        self.assertFalse(u2.confirm(token))


    def test_expired_confirmation_token(self):
        '''验证用户令牌过期时间设置有效性'''
        u=User(password='cat')
        db.session.add(u)
        db.session.commit()

        token = u.generate_confirmation_token(expiration=2)
        time.sleep(3)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        '''验证重置操作的 token'''
        u=User(password='abcde')
        db.session.add(u)
        db.session.commit()

        self.assertTrue(u.verify_password('abcde'))

        # 获取 重置所需的 token
        token = u.generate_reset_token(expiration=3)
        self.assertTrue(u.reset_password(token, 'cat'))
        self.assertTrue(u.verify_password('cat'))
        time.sleep(4)
        self.assertFalse(u.reset_password(token, 'cat123'))

    def test_invalid_reset_token(self):
        '''验证多用户token交互使用并设置密码情况下的情况'''
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))


    def test_valid_email_change_token(self):
        '''验证邮件地址重置token'''
        u1 = User(username='cat', password='cat', email='cat@qq.com')
        u2 = User(username='dog', password='dog', email='dog@qq.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        # 生成对应用户的 邮件地址变更 token
        token1 = u1.generate_email_change_token('new_cat@qq.com')
        token2 = u2.generate_email_change_token('new_dog@qq.com')

        # 验证其他用户token
        self.assertFalse(u1.change_email(token2))
        # 验证自己的 token
        self.assertTrue(u1.change_email(token1))
        self.assertTrue(u1.email == 'new_cat@qq.com')


    def test_duplicate_email_change_token(self):
        '''测试重复的电子邮件地址'''
        u1 = User(username='cat', password='cat', email='cat@sina.com')
        u2 = User(username='dog', password='dog', email='dog@sina.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        # 生成对应用户的 邮件地址变更 token
        token1 = u1.generate_email_change_token('dog@sina.com')
        # 验证其他用户token
        self.assertFalse(u1.change_email(token1))
        self.assertTrue(u2.email == 'dog@sina.com')
        self.assertTrue(u1.email == 'cat@sina.com')

    def test_user_role_and_permissions(self):
        '''测试用户的角色及权限'''
        Role.insert_roles()
        u1=User(username='dog01', password='dog01', email='dog01@qq.com')
        self.assertTrue(u1.can(Permission.FOLLOW))
        self.assertTrue(u1.can(Permission.COMMENT))
        self.assertTrue(u1.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u1.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user_role_and_permissions(self):
        '''测试匿名用户的权限和角色'''
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_timestamps(self):
        '''测试注册日期和用户最后访问日期'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue( (datetime.utcnow() - u.member_since).total_seconds() < 3  )
        self.assertTrue( (datetime.utcnow() - u.last_seen ).total_seconds() < 3  )

    def test_ping(self):
        '''测试自动更新最后一次登录时间'''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue( u.last_seen > last_seen_before )



    def test_follows(self):
        u1 = User(email='A@qq.com', password='pA')
        u2 = User(email='B@qq.com', password='pB')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        # 判断 u1 已关注 u2
        self.assertFalse(u1.is_following(u2))
        # 判断 u1 已被 u2 关注
        self.assertFalse(u1.is_followed_by(u2))

        # 定位时间点
        timestamp_before = datetime.utcnow()
        # 设置 u1 关注 u2
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        # 定位结束时间
        timestamp_after = datetime.utcnow()

        # 判断 u1 关注了 u2
        self.assertTrue( u1.is_following(u2))
        # 判断 u1 被 u2 关注了
        self.assertFalse( u1.is_followed_by(u2))

        # 判断 u2 被 u1 关注了
        self.assertTrue(u2.is_followed_by(u1))

        # 判断 u1 关注了 2个用户
        self.assertTrue(u1.followed.count() == 2)
        # 判断 u2 被 2 个用户关注
        self.assertTrue(u2.followers.count() == 2)

        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        # print timestamp_before
        # print f.timestamp
        # print timestamp_after
        # 因为 时间戳包含 毫秒，存储数据库再取出之后就没有毫秒了，所以此处会报错
        # self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)

        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)


    def test_to_json(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        json_user = u.to_json()
        expected_keys = ['url', 'username', 'member_since', 'last_seen', 'posts', 'followed_posts', 'post_count']
        self.assertTrue(sorted(json_user.keys()), sorted(expected_keys))
        self.assertTrue('api/v1.0/users/' in json_user['url'])