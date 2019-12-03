# -*- encoding=UTF-8 -*-

from nowtagram import app, db
from flask_script import Manager
from nowtagram.models import User, Image, Comment
import random
from sqlalchemy import or_, and_

manager = Manager(app)


def get_image_url():
    return 'http://images.nowcoder.com/head/' + str(random.randint(0, 1000)) + 'm.png'


# 实现一个脚本命令
@manager.command
def init_database():
    db.drop_all()
    db.create_all()

    # 增
    for i in range(1, 101):
        db.session.add(User('User' + str(i), 'pw' + str(i)))
        for j in range(1, 4):
            db.session.add(Image(get_image_url(), i))     # id是从1开始的
            for k in range(1, 4):
                # id数值一定要正确对应设置，否则报错外键设置不对应
                db.session.add(Comment('This is comment ' + str(k), 3*(i-1)+j, i))
    db.session.commit()

    # 改
    for i in range(50, 100, 2):
        user = User.query.get(i)
        user.username = 'New1 ' + user.username

    User.query.filter_by(id=51).update({'username': 'New2 '})
    db.session.commit()

    # 删
    for i in range(50, 100, 2):
        comment = Comment.query.get(i)
        db.session.delete(comment)
    db.session.commit()

    # 查
    print(1, User.query.all())
    print(2, User.query.get(3))
    print(3, User.query.filter_by(id=5).first())
    print(4, User.query.order_by(User.id.desc()).offset(1).limit(2).all())
    print(5, User.query.filter(User.username.endswith('0')).limit(3).all())
    print(6, User.query.filter(or_(User.id == 88, User.id == 99)).all())
    print(7, User.query.filter(and_(User.id > 88, User.id < 93)).all())
    print(8, User.query.filter(or_(User.id == 88, User.id == 99)).first_or_404())
    # 分页查询
    print(9, User.query.order_by(User.id.desc()).paginate(page=1, per_page=10).items)
    user = User.query.get(1)
    print(10, user.images.all())

    image = Image.query.get(1)
    print(11, image, image.user)


if __name__ == '__main__':
    manager.run()
