# -*- encoding=UTF-8 -*-

from nowtagram import app, db
from flask import render_template, redirect, request, flash, get_flashed_messages
from nowtagram.models import User, Image
# 使用md5的加密算法hashlib
import random, hashlib, json
from flask_login import login_user, logout_user, login_required, current_user


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
@login_required     # 只有登录才能查看
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')

    # 分页显示用户的图片
    paginate = Image.query.filter_by(user_id=user_id).paginate(page=1, per_page=3, error_out=False)
    return render_template('profile.html', user=user, images=paginate.items, has_next=paginate.has_next)


# 分页显示个人详情页的图片，点更多动态加载图片
@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    paginate = Image.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
    # 判断是否还有下一页，是否需要显示更多按钮，paginate.has_next参数
    map = {'has_next': paginate.has_next}
    # 返回的图片信息也放到map里
    images = []
    for image in paginate.items:
        imgvo = {'id': image.id, 'url': image.url, 'comment_count': len(image.comments)}
        images.append(imgvo)
    map['images'] = images

    # 返回json格式的数据，用json.dumps而不是json.dump，然后靠前端处理相应的数据
    return json.dumps(map)


# 注册登录页
@app.route('/regloginpage/')
def regloginpage():
    msg = ''
    # 只收集来自登录注册的闪现信息
    for m in get_flashed_messages(with_categories=False, category_filter='reglogin'):
        msg += m

    # 当用户试图访问某个页面或评论某个页面时，我们会要求其先登录，然后在用户在登录后自动跳转
    # 到用户试图访问的页面，即实现用户在登录后跳转回前一页，可添加next参数实现跳转
    return render_template('login.html', msg=msg, next=request.values.get('next'))


# 因为要闪现很多信息，需包装成函数
def redirect_with_msg(target, msg, category):
    if msg != None:
        # category指信息来自哪里
        flash(msg, category=category)
    return redirect(target)


# 注册接口，点注册按钮需要判断会发生什么
@app.route('/reg/', methods=['GET', 'POST'])
def reg():
    # request.args是url里的值，request.form是body里的值
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    if username == '' or password == '':
        return redirect_with_msg('/regloginpage/', '用户名或密码不能为空', category='reglogin')

    user = User.query.filter_by(username=username).first()
    if user != None:
        return redirect_with_msg('/regloginpage/', '用户名已存在', category='reglogin')

    # 更多判断

    # 为md5密码加盐
    salt = '.'.join(random.sample('0123456789abcdefghiABCDEFGHI', 10))
    m = hashlib.md5()
    # python3下字符串为Unicode类型，而hash传递时需要的是utf-8类型，因此，需要类型转换
    m.update((password+salt).encode('utf8'))
    # md5加密出来的十六进制字符串
    password = m.hexdigest()

    user = User(username, password, salt)
    db.session.add(user)
    db.session.commit()

    # 登录用户
    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/'):
        return redirect(next)

    return redirect('/')


# 登录接口，点登录按钮需要判断会发生什么
@app.route('/login/', methods=['GET', 'POST'])
def login():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    if username == '' or password == '':
        return redirect_with_msg('/regloginpage/', '用户名或密码不能为空', category='reglogin')

    user = User.query.filter_by(username=username).first()
    if user == None:
        return redirect_with_msg('/regloginpage/', '用户不存在', category='reglogin')

    m = hashlib.md5()
    m.update((password + user.salt).encode('utf8'))
    if m.hexdigest() != user.password:
        return redirect_with_msg('/regloginpage/', '密码错误', category='reglogin')

    login_user(user)

    # 需要经由login.html的表单form提交再在此处获取，因为login链接本来就是在表单form跳转到这的
    next = request.values.get('next')
    if next != None and next.startswith('/'):
        return redirect(next)

    return redirect('/')


# 登出
@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/')





