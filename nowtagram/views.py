# -*- encoding=UTF-8 -*-

from nowtagram import app
from flask import render_template, redirect
from nowtagram.models import User, Image


# 首页
@app.route('/')
def index():
    images = Image.query.order_by(Image.id.desc()).limit(10).all()
    return render_template('index.html', images=images)


# 图片详情页
# static忘记了一个/号，弄得一直加载CSS出现404...
@app.route('/image/<int:image_id>/')
def image(image_id):
    # 由index里查询的图片id来查找相应的图片
    image = Image.query.get(image_id)
    if image == None:
        return redirect('/')
    return render_template('pageDetail.html', image=image)


# 个人详情页
@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')
    return render_template('profile.html', user=user)
