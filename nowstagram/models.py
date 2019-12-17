# -*- encoding=UTF-8 -*-

from nowstagram import db, login_manager
import random
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


# 用户模型，不定义表名则默认为类名的小写
class User(db.Model):
    # 添加不同的表名以防和其他数据库同名的表出现外键约束而报错！！！
    __tablename__ = 'ins_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(32))
    # 加强md5密码 加盐值
    salt = db.Column(db.String(32))
    # 头像地址
    head_url = db.Column(db.String(256))
    # 一对多，在一的一方定义关系，反向引用，要用backref=db.backref('user')而不是backref='user'
    # 该用户发的所有图片
    images = db.relationship('Image', backref='user', lazy='dynamic')
    # 该用户发的所有评论
    # comments = db.relationship('Comment', backref='user', lazy='dynamic')

    email = db.Column(db.String(64))
    # 是否激活
    status = db.Column(db.Boolean)

    def __init__(self, username, password, email='', salt=''):
        self.username = username
        self.password = password
        self.email = email
        self.salt = salt
        # 使用网站提供的随机图片
        self.head_url = 'http://images.nowcoder.com/head/' + str(random.randint(0, 1000)) + 'm.png'

    def __repr__(self):
        return '<User: %d %s>' % (self.id, self.username)

    # Flask-Login提供了UserMixin类，你只要继承这个类就行，它提供了对这些方法的默认实现
    # 用户类需要包含包含以下性质和方法才能使用flask-login
    @property   # 把方法当成属性使用
    def is_authenticated(self):     # 是否是认证的
        return True

    @property
    def is_active(self):    # 是否是激活的
        return True

    @property
    def is_anonymous(self):     # 是否是匿名的
        return False

    def get_id(self):
        return self.id

    # 获取token和验证token是通过itsdangerous这个库来实现
    # 生成账户激活的token
    def generate_activate_token(self, expiration=3600):
        # 这个函数需要两个参数，一个密匙，从配置文件获取，一个时间，这里1小时
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # 为ID生成一个加密签名，然后再对数据和签名进行序列化，生成令牌版字符串（就是一长串乱七八糟的东西）,然后返回
        return s.dumps({'id': self.id})

    # 账户激活（静态方法），所有用户共用此方法？
    @staticmethod
    def check_activate_token(token):
        # 传入和刚才一样的密匙，解码要用
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)   # 解码
        except:
            return False
        u = User.query.get(data['id'])
        if not u:
            # 用户已被删除
            return False
        if not u.status:
            u.status = True
            db.session.add(u)
            db.session.commit()
        return True


# 图像模型
class Image(db.Model):
    __tablename__ = 'ins_image'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(512))
    created_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('ins_user.id'))
    # user属性
    comments = db.relationship('Comment')

    def __init__(self, url, user_id):
        self.url = url
        self.user_id = user_id
        # 获取现在的时间
        self.created_date = datetime.now()

    def __repr__(self):
        return '<Image: %d %s>' % (self.id, self.url)


# 评论模型
class Comment(db.Model):
    __tablename__ = 'ins_comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(1024))
    # 评论的状态：0为正常，1为删除（比如不规范被管理员删除）
    status = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('ins_user.id'))
    image_id = db.Column(db.Integer, db.ForeignKey('ins_image.id'))
    # user属性
    user = db.relationship('User')

    def __init__(self, content, image_id, user_id):
        self.content = content
        self.image_id = image_id
        self.user_id = user_id

    def __repr__(self):
        return '<Comment: %d %s>' % (self.id, self.content)


# 回调函数（通过session里的id获取用户信息）
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
