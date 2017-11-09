# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from datetime import datetime
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import abort
from flask import flash
from flask import request
from flask import make_response
from flask import current_app
from flask_login import login_required
from flask_login import current_user

from . import main
from .forms import NameForm
from .forms import EditProfileForm
from .forms import EditProfileAdminForm
from .forms import PostForm
from .forms import CommentForm

from .. import db
from ..models import User
from ..models import Role
from ..models import Post
from ..models import Comment
from ..models import Permission
from ..decorators import admin_required
from ..decorators import permission_required


reload(sys)
sys.setdefaultencoding("utf-8")

@main.route('/', methods=['GET', 'POST'])
def index():
    form=PostForm()
    # 判断有没有博文的编辑权限
    if (current_user.can(Permission.WRITE_ARTICLES)
        and form.validate_on_submit()):
        # current_user 的 _get_current_object() 方法是有 Flask-Login提供的，它包含真正的用户对象
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)

    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))

    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    # 注意：为显示某页中的数据，需要把all()方法替换为Flask-SQLAlchemy 提供的 paginate()方法，
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page,  # 表示页数
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], # 表示每页展示的记录数量
        error_out=False  # 当请求页数超出范围之后，如果error_out=True,则返回404错误，否则返回一个空列表
    )
    # print
    # print str(query.order_by(Post.timestamp.desc()))
    posts = pagination.items
    return render_template('index.html',
                           form=form,
                           posts=posts,
                           show_followed=show_followed,
                           pagination=pagination)


# 路由 show_all 和 show_followed 的解说：
# 因为指向这两个路由的链接添加在首页模版中，点击这两个链接之后会为 show_followedcookie 设定适当的值，
# 然后重定向到首页。cookie 只能在响应对象中设置，因此这两个路由不能依赖 Flask，要使用 make_response() 方法创建响应对象
# set_cookie() 函数的前两个参数分别是 cookie 中的键名和键值。可选参数 max_age 设置的是cookie的过期时间，单位为秒
# 如果不指定参数 max_cookie，那么浏览器关闭之后cookie就会过期，在本例子中设置的过期时间为30天

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp



@main.route('/user/<username>')
def user(username):
    '''用户资料页面'''
    # 获取用户
    user = User.query.filter_by(username=username).first_or_404()
    # 获取页号
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, # 页码
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],  # 每页的显示数量
        error_out=False  # 超出页码范围之后返回空列表
    )
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''用户级别的-资料编辑'''
    form = EditProfileForm()
    if form.validate_on_submit():
        # 如果表单验证通过则，进行更新操作
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('您的资料已更新！')
        return redirect(url_for('.user', username=current_user.username))

    form.name.data = current_user.name
    form.location  = current_user.location
    form.about_me  = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    '''管理员级别-资料编辑'''
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email    = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role     = Role.query.get(form.role.data)
        user.name     = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('当前用户配置已更新完毕！')
        return redirect(url_for('.user', username=user.username))

    form.email.data     = user.email
    form.username.data  = user.username
    form.confirmed.data = user.confirmed
    form.role.data      = user.role.id
    form.name.data      = user.name
    form.location.data  = user.location
    form.about_me.data  = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    '''实例化一个评论表单，并将其传入 post.html 模板，以便渲染'''
    # 根据 帖子的ID获取帖子的实例对象，如果不存在帖子，则直接返回404错误
    post = Post.query.get_or_404(id)
    # 实例化 评论提交表单
    form = CommentForm()
    # 如果表单中的所有数据都能够被对应的验证函数通过，则 validate_on_submit() 会返回True，否则返回False
    if form.validate_on_submit():
        # 注意添加评论时，评论的 author 值应不能设置为 current_user，因为这个变量是上下文代理对象。真正的User对象
        # 需要使用表达式 curretn_user._get_current_object() 获取
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('您的评论已提交')
        # 在url_for()中，通常通过设置 page=-1 来请求评论的最后一页，这样刚刚提交的评论才会出现在页面中
        return redirect(url_for('.post', id=post.id, page=-1))
    # 获取 请求参数中的page值，并设定默认值1 设置类型为 int
    page = request.args.get('page', 1, type=int)
    if page == -1:
        # 如果在请求中发现 page=-1,那么会在计算评论的总数量以及配置中每页显示的评论数量，从而获得真正应该显示的页数
        page = (post.comments.count() - 1) / current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    # 文章的评论列表通过 post。comments 一对多关系获取 按照时间顺序降序排列，再使用与博客文章相同的技术分页显示
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,
        per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('post.html',
                           posts=[post],
                           form=form,
                           comments=comments,
                           pagination=pagination)

@main.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    # 获取博文，如果博文不存在，则直接返回404错误
    post = Post.query.get_or_404(id)
    # 如果当前用户不是作者 且 也不是管理员，则直接返回 403错误
    if (current_user != post.author
        and not current_user.can(Permission.ADMINISTER)):
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('这个帖子已更新')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    '''执行 关注某一用户操作'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('您已关注了该用户')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('关注`{}`成功'.format(username))
    return redirect(url_for('.user', username=username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    '''执行 取消关注某一用户操作'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('您尚未关注该用户')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('取消关注`{}`成功'.format(username))
    return redirect(url_for('.user', username=username))

@main.route('/followers/<username>')
def followers(username):
    '''展示我关注的人'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page,
        per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    follows = [ {'user' : item.follower, 'timestamp' : item.timestamp} for item in pagination.items  ]

    return render_template(
        'followers.html',
        user=user,
        title='Followers of',
        endpoint='.followers',
        pagination=pagination,
        follows=follows
    )

@main.route('/followed-by/<username>')
def followed_by(username):
    '''展示 关注我的人'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page,
        per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    follows = [ {'user' : item.followed, 'timestamp' : item.timestamp} for item in pagination.items  ]

    return render_template(
        'followers.html',
        user=user,
        title='Followed by',
        endpoint='.followed_by',
        pagination=pagination,
        follows=follows
    )

