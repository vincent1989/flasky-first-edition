# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask import g
from flask import jsonify
from flask import request
from flask import url_for
from flask import current_app

from ..models import Post
from ..models import User
from . import api

reload(sys)
sys.setdefaultencoding("utf-8")

@api.route('/users/<int:id>')
def get_user(id):
    '''获取指定用户操作'''
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    '''获取指定用户的博客列表'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', id=id, page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', id=id, page=page+1, _external=True)
    return jsonify({
        'posts' :[post.to_json() for post in posts],
        'prev' : prev,
        'next' : next,
        'count' : pagination.total
    })

@api.route('/users/<int:id>/timeline/')
def get_user_followed_posts(id):
    '''一个用户所关注用户发布的文章'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', id=id, page=page-1, _external=True)

    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', id=id, page=page+1, _external=True)

    return jsonify({
        'posts' : [post.to_json() for post in posts],
        'prev' : prev,
        'next' : next,
        'count' : pagination.total
    })
