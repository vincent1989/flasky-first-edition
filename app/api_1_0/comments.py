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
from ..models import Comment
from ..models import Permission
from .decorators import permission_required
from .. import db
from . import api

reload(sys)
sys.setdefaultencoding("utf-8")

@api.route('/comments/')
def get_comments():
    '''获取所有评论'''
    page = request.args.get('page', 1, type=1)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1, _external=True)

    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1, _external=True)

    return jsonify({
        'comments' : [comment.to_json() for comment in comments],
        'prev' : prev,
        'next' : next,
        'count' : pagination.total
    })


@api.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api.route('/posts/<int:id>/comments/')
def get_post_comments(id):
    '''获取指定博文中的所有评论'''
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,
        per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1, _external=True)

    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1, _external=True)

    return jsonify({
        'comments' : [comment.to_json() for comment in comments],
        'prev' : prev,
        'next' : next,
        'count' : pagination.total
    })


@api.route('/posts/<int:id>/comments', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.comment()
    return jsonify({comment.to_json()}), 201, {'Location': url_for('api.get_comment', id=comment.id, _external=True)}


