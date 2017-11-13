# -*- coding: utf-8 -*-
__author__ = 'vincent'

import unittest
import time
import re
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

from datetime import datetime

class APITestCase(unittest.TestCase):

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
        # self.client = self.app.test_client(use_cookies=True)
        # 因 API 的测试无需浏览器支持，所以此处可以去掉 参数 use_cookies
        self.client = self.app.test_client()

    def tearDown(self):
        '''
        这是测试完成之后会自动运行的方法，本方法将删除 程序上下文和数据库
        '''
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def get_api_headers(self, username, password):
        '''获取 api header'''
        return {
            'Authorization' : 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')
            ).decode('utf-8'),
            'Accept' : 'application/json',
            'Content-Type' : 'application/json'
        }


    def test_404(self):
        '''测试404错误'''
        response = self.client.get(
            '/wrong/url',
            headers=self.get_api_headers('email', 'password')
        )
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'not found')

    def test_no_auth(self):
        '''测试 未登录下调用 api.get_posts'''
        response = self.client.get(url_for('api.get_posts'), content_type='application/json')
        self.assertTrue(response.status_code == 200)

    def test_bad_auth(self):
        '''测试 无效auth'''
        # 添加一个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        # 验证密码错误的请求
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john@example.com', 'dog')
        )
        self.assertTrue(response.status_code == 401)

    def test_token_auth(self):
        '''测试 api token'''
        # 添加一个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        # 获取一个api token --- 错误情况下
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('bad-token', '')
        )
        self.assertTrue(response.status_code == 401)

        # 获取一个api token
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']
        
        # 验证token
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers(token, '')
        )
        print response.__dict__
        self.assertTrue(response.status_code == 200)



    def test_anonymous(self):
        '''测试 匿名用户 调用 api.get_posts'''
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('', '')
        )
        self.assertTrue(response.status_code == 200)

    def test_unconfirmed_account(self):
        ''''''
        # 获取用户角色对象
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        # 添加一个 用户
        u = User(
            email='john@example.com',
            password='cat',
            confirmed=False,
            role=r
        )
        db.session.add(u)
        db.session.commit()

        # 未认证的用户 无法通过 api.get_posts
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertTrue(response.status_code == 403)


    def test_post(self):
        # 获取用户角色对象
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        # 添加一个 用户
        u = User(
            email='john@example.com',
            password='cat',
            confirmed=True,
            role=r
        )
        db.session.add(u)
        db.session.commit()

        # 写一个空的博客
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body' : ''
            })
        )
        self.assertTrue(response.status_code == 400)

        # 写一个非空博客
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body' : '这是一个测试的非空博客 *Blog*'
            })
        )
        self.assertTrue(response.status_code == 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # 获取新创建的博客信息
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url)
        self.assertTrue(json_response['body'] == '这是一个测试的非空博客 *Blog*')
        self.assertTrue(json_response['body_html'] == '<p>这是一个测试的非空博客 <em>Blog</em></p>')
        json_post = json_response

        # 从当前用户获取博文
        response = self.client.get(
            url_for('api.get_user_posts', id=u.id),
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertTrue(json_response.get('count', 0) == 1)
        self.assertTrue(json_response['posts'][0] == json_post)

        # 从当前用户的关注这中获取博文
        response = self.client.get(
            url_for('api.get_user_followed_posts', id=u.id),
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        print "BBBBB"
        print json_response
        print "CCCCC"
        self.assertIsNotNone(json_response.get('posts'))
        self.assertTrue(json_response.get('count', 0) == 1)
        self.assertTrue(json_response['post'][0] == json_post)

        # 编辑博文
        response = self.client.put(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body' : 'updated body'
            })
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url)
        self.assertTrue(json_response['body'] == 'updated body')
        self.assertTrue(json_response['body_html'] == '<p>updated body</p>')


    def test_users(self):
        '''测试用户接口'''
        # 添加两个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', username='john', password='cat', confirmed=True, role=r)
        u2 = User(email='susan@example.com', username='susan', password='dog', confirmed=True, role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        # 获取用户
        response = self.client.get(
            url_for('api.get_user', id=u1.id),
            headers=self.get_api_headers('susan@example.com', 'dog'),
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'john')

        response = self.client.get(
            url_for('api.get_user', id=u2.id),
            headers=self.get_api_headers('susan@example.com', 'dog'),
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'susan')

    def test_comment(self):
        '''测试评论接口'''
        # 添加两个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', username='john', password='cat', confirmed=True, role=r)
        u2 = User(email='susan@example.com', username='susan', password='dog', confirmed=True, role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        # 给 u1 添加一篇博文
        post = Post(body='body of the post', author=u1)
        db.session.add(post)
        db.session.commit()

        # 发表一个评论
        response = self.client.post(
            url_for('api.new_post_comment', id=post.id),
            headers=self.get_api_headers('susan@example.com', 'dog'),
            data=json.dumps({'body':'Good [post](http://example.com)!'})
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        url = json_response.get('Location')
        self.assertIsNotNone(url)
        self.assertTrue(json_response['body'] == 'Good [post](http://example.com)!' )
        self.assertTrue(re.sub('<.*?>', '', json_response['body_html']) == 'Good post!')

        # 获取这个新增加的评论
        response = self.client.post(
            url,
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url )
        self.assertTrue(json_response['body'] == 'Good [post](http://example.com)!' )

        # 添加作者评论
        comment = Comment(body='Thank you!', author=u1, post=post)
        db.session.add(comment)
        db.session.commit()

        # 从这篇博文中获取 评论
        response = self.client.post(
            url_for('api.get_post_comments', id=post.id),
            headers=self.get_api_headers('susan@example.com', 'dog')
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('comments'))
        self.assertTrue(json_response.get('count', 0) == 2)

        # 获取所有的评论
        response = self.client.post(
            url_for('api.get_comments', id=post.id),
            headers=self.get_api_headers('susan@example.com', 'dog')
        )
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('comments'))
        self.assertTrue(json_response.get('count', 0) == 2)



