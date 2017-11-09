# -*- coding: utf-8 -*-
import os
import hashlib
import bleach
from markdown import markdown
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
'''
# 用户模型必须实现 82页：表8-1 所需要的四个方法，如下：
# is_authenticated 如果用户已登录，则返回True，否则返回False
# is_active 如果允许用户登录，则返回True，否则返回False
# is_anonymous 对普通用户必须返回False
# get_id 必须返回用户的唯一标示符，使用unicode 编码字符串
可以使用 Flask-Login 提供的UserMixin类，就自动拥有以上四种方法了
'''
from flask_login import UserMixin
from flask_login import AnonymousUserMixin

# 下面这个包 itsdangerous 用于生成确认令牌
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask import request

from . import db, login_manager

class Permission:
    '''权限常量'''
    # 权限 关注用户
    FOLLOW = 0x01
    # 权限 在他人的文章中发表评论
    COMMENT = 0x02
    # 写文章
    WRITE_ARTICLES = 0x04
    # 管理他人发表的评论
    MODERATE_COMMENTS = 0x08
    # 管理员权限
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    # permisions = db.Column(db.Integer)
    permissions = db.Column(db.Integer)
    '''
    注意，如果users 不添加 lazy='dynamic'，则执行 user_role.users 会直接执行隐藏的query 方法
    >>> from hello import Role, User
    >>> user_role=Role(name='User')
    >>> users=user_role.users
    >>> users
    >>> [<User u'susan'>, <User u'david'>]
    添加 lazy='dynamic' 之后，则user_role.users 就会返回一个尚未执行的查询语句，这样就能在其后面追加过滤条件了
    '''
    #
    # users = db.relationship('User', backref='role')
    users = db.relationship('User', backref='role', lazy='dynamic')
    # 上面一行代码中 db.relationship 中的参数 backref表示向User模型中添加一个role属性，从而定义反向属性。
    # 这一属性可以替代 role_id访问Role模型，此时获取的是Role对象，而不是role_id的值

    def __repr__(self):
        return '<Role %r>' % self.name


    @staticmethod
    def insert_roles():
        roles = {
            'User' : (Permission.FOLLOW |
                      Permission.COMMENT|
                      Permission.WRITE_ARTICLES, True),
            'Moderator' : (Permission.FOLLOW |
                           Permission.COMMENT|
                           Permission.WRITE_ARTICLES|
                           Permission.MODERATE_COMMENTS, False),
            'Administrator':(0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

class Follow(db.Model):
    '''关注关联表的模型'''
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # primary_key 设置为主键
    id = db.Column(db.Integer, primary_key=True)
    # 邮箱，禁止重复，添加索引
    email = db.Column(db.String(64), unique=True, index=True)
    # unique 设置列值不允许重复; index 为该列创建索引，以便提升查询效率
    username = db.Column(db.String(64), unique=True, index=True)
    # 密码hash值
    password_hash = db.Column(db.String(128))
    # 此处将 role_id 定义为外键，传递给db.ForeignKey 的参数 'roles.id' 表明：这列的值是roles表中，字段为id列的值
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 用于用户确认验证
    confirmed = db.Column(db.Boolean, default=False)
    # 用户真实姓名
    name = db.Column(db.String(64))
    # 所在地
    location = db.Column(db.String(64))
    # 自我介绍
    about_me = db.Column(db.Text())
    # 注册日期
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    # 最后访问日期
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    # 注意 datetime.utcnow 后面没有()，因为db.Column() 的default参数可以接收函数作为默认值。
    # 所以每次需要生成默认值时，db.Column()都会调用制定的函数，member_since只需要默认值即可

    # 存储用户邮件头像的hash值
    avatar_hash = db.Column(db.String(32))
    # 确定与另一张表Post的关联关系，并向Post表中插入反向引用关系属性 posts,这样post可以通过访问属性author来获取对象而不是author_id的值了
    posts = db.relationship('Post', backref='author', lazy='dynamic')


    # 对 followed／followers 的说明
    # 1. followed 和 followers 关系都被定义为单独的一对多关系
    # 2. 为了消除外键之间的歧义，定义关系时都必须使用可选参数 foreign_keys 指定的外键
    # 3. db.backref 参数并不是指定两个关系之间的引用，而是回引 Follow 模型。 回引中的 lazy 参数指定了 joined.
    # lazy=joined 这个模式，可以实现立即从联结查询中加载相关对象。例如，某个用户关注了100个用户，
    # 调用 user.followed.all() 后会返回一个列表，其中包含100个Follow实例。每一个实例的 follower 和 followed 回引属性都指向相应的用户
    # 如果设置 lazy=select，那么首次访问 follower 和 followed 时才会加载对应的用户。而且每个属性都需要一个单独的查询，
    # 这就意味着获取全部被关注用户时就需要增加100次额外的数据库查询
    # 4. cascade 级联设置，指参数配置在父对象上执行的操作对相对关系的影响. 说白了就是级联操作，删除一个父对象，则父对象对应的子对象也相应全部删除（关系表中）。

    # 被关注者
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    # 关注者
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return '<User %r>' % self.username

    def __init__(self, **kwargs):
        '''User类的构造函首先调用基类的构造函数，如果创建基类对象后还没有自定义角色，
        则根据注册邮件是否为管理员邮件来决定是否将其设为管理员或默认角色'''
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
            # 邮件头像hash值
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()



    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        # 生成一个用户令牌，有效期默认为1小时
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id})

    def confirm(self, token):
        # 验证用户令牌，如果验证通过，则设置 confirmed 属性为True
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        '''
        密码 邮件 重置时生成用户 token
        '''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset':self.id})

    def reset_password(self, token, new_password):
        '''
        重置密码，重置前验证token
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('reset') !=self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        '''
        获取邮件重置时的 token
        '''
        s=Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email':self.id, 'new_email': new_email})

    def change_email(self, token):
        '''
        重置密码，重置前验证token
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('change_email') !=self.id:
            return False

        new_email = data.get('new_email')
        if new_email is None:
            return False

        if self.query.filter_by(email=new_email).first() is not None:
            # 新邮件在 用户列表中应当不存在，否则返回False
            return False

        self.email = new_email
        # 更新邮件头像的hash值
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True


    def can(self, permissions):
        '''通过俺位计算判断给定权限位与用户实际权限位是否为符合, 即判断用户是否允许后续操作'''
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        '''判断是否为管理员'''
        return self.can(Permission.ADMINISTER)

    def ping(self):
        '''更新用户的最后一次访问时间'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)


    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'http://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'

        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url,
            hash=hash,
            size=size,
            default=default,
            rating=rating
        )

    def follow(self, user):
        '''添加关注'''
        if not self.is_following(user):
            # 创建 关注条目信息
            f = Follow(followed=user)
            # 从在我的被关注者列表中添加 该条目
            self.followed.append(f)

    def unfollow(self, user):
        '''取消关注'''
        # 从我的被关注者列表中 获取 被关注者
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            # 从我的被关注这列表中删除对应的实例
            self.followed.remove(f)


    def is_following(self, user):
        '''判断已关注某用户'''
        # 在 自己的已关注列表中，赛选出 被关注者的 user.id; 如果存在则表示已关注，如果未存在则表示没有关注
        # 然后根据 first() 的存在则返回实例，不存在则返回 None的特性去判断
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        '''判断已被某一个用户关注'''
        # 在 自己的被关注列表中，赛选出 关注我的用户ID，如果存在则表示已被该用户关注，如果未存在，则表示没有被该用户关注
        return self.followers.filter_by(follower_id=user.id).first() is not None


    @staticmethod
    def generate_fake(count=100):
        '''该方法用于生成大批量的虚拟信息'''
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

class AnonymousUser(AnonymousUserMixin):
    '''处于一致性考虑，专门定义此类实现 未登录用户的 can() 和 is_administrator() 方法。
    这个对象继承自Flask-Login中的AnonymousUserMixin类，并将其设置为用户未登录时 current_user的值
    这样程序就不用先检查用户是否登录，就能自动调用 current_user.can() 和 current_user.is_administrator()'''
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # 定义外键 author_id， 表明该列字段值是 users表中的 id 列的值
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # body的HTML格式数据
    body_html = db.Column(db.Text)


    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre',
                        'strong', 'ul', 'h1', 'h2', 'h3', 'p']

        # 解说：首先：markdown()函数初步将MarkDown文本转换为HTML
        # 然后 通过 bleach 的 clean() 函数去除所有不在白名单allowed_tags中的标签。
        # 最后 通过 bleach 的 clean() 函数将纯文本中的所有 url 转换为<a>链接。
        # 这最后一步是很有必要的，因为MarkDown规范没有为自动生成链接提供官方支持，PageDown以扩展的形式实现了该功能
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'),
                tags=allowed_tags,
                strip=True)
        )

# 说明：以下操作将 Post的 on_changed_body 函数注册到body字段上，是SQLAlchemy "set"事件的监听程序。
# 这意味这只要这个类实例的body字段设了新值，on_changed_body 函数就会自动被调用
# on_changed_body 函数把body字段中的文本渲染成 HTML 格式，结果保存在 body_html 中
db.event.listen(Post.body, 'set', Post.on_changed_body)


@login_manager.user_loader
def load_user(user_id):
    '''当前是加载用户的回调函数， 如果能找到用户，则返回用户对象，否则返回None'''
    return User.query.get(int(user_id))
