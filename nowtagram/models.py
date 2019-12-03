# -*- encoding=UTF-8 -*-

from nowtagram import db
import random
from datetime import datetime


# 用户模型，不定义表名则默认为类名的小写
class User(db.Model):
    # 添加不同的表名以防和其他数据库同名的表出现外键约束而报错！！！
    __tablename__ = 'ins_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(32))
    # 头像地址
    head_url = db.Column(db.String(256))
    # 一对多，在一的一方定义关系，反向引用，要用backref=db.backref('user')而不是backref='user'
    # 该用户发的所有图片
    images = db.relationship('Image', backref='user', lazy='dynamic')
    # 该用户发的所有评论
    # comments = db.relationship('Comment', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password
        # 使用网站提供的随机图片
        self.head_url = 'http://images.nowcoder.com/head/' + str(random.randint(0, 1000)) + 'm.png'

    def __repr__(self):
        return '<User: %d %s>' % (self.id, self.username)


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
