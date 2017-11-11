# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask import g
from flask import jsonify
from flask import request
from flask import abort
from flask import url_for
from flask import current_app

from ..models import Post
from ..models import Permission
from .. import db

from . import api

from .decorators import permission_required
from .errors import forbidden


reload(sys)
sys.setdefaultencoding("utf-8")


@api.route('/posts/')
def get_posts():
    '''获取指定页的博文操作'''
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        # 上一页
        prev = url_for('api.get_posts', page = page - 1, _external=True)
    next = None
    if pagination.has_next:
        # 下一页
        next = url_for('api.get_posts', page = page + 1, _external=True)

    return jsonify({
        'posts' : [post.to_json() for post in posts],
        'prev' : prev,
        'next' : next,
        'count' : pagination.total
    })


@api.route('/posts/<int:id>')
def get_post(id):
    '''获取指定博文操作'''
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())

@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    '''新增博文操作'''
    # 注意，外套的 permission_required 方法目的是确保 通过认证的用户具有写博客的权限
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    # 注意，当前模型写入数据库之后，会返回201状态码，并把Location首部的值设为刚创建的这个资源的URL
    # 为了便于客户端操作，响应的主题中包含了新建的资源，如此一来，客户端就无需在创建资源之后再立即发起一个GET请求以获取资源
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id, _external=True)}

@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    '''更新博文操作'''
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and not g.current_user.can(Permission.ADMINISTER):
        # 如果当前用户不是 博文的作者，且也没有管理员权限，那么抛出没有权限的错误
        return forbidden('没有足够的权限')

    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return jsonify(post.to_json())


