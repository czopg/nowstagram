# -*- encoding=UTF-8 -*-

from nowtagram import app, db, mail
from flask import render_template, redirect, request, flash, get_flashed_messages, send_from_directory, current_app
from nowtagram.models import User, Image, Comment
# 使用md5的加密算法hashlib
import random, hashlib, json, uuid, os, re
from flask_login import login_user, logout_user, login_required, current_user
from nowtagram.qiniusdk import qiniu_upload_file
from flask_mail import Message
from threading import Thread


# 首页
@app.route('/')
def index():
    # images = Image.query.order_by(Image.id.desc()).limit(10).all()
    # return render_template('index.html', images=images)

    # 实现主页的AJAX分页显示
    paginate = Image.query.order_by(db.desc(Image.id)).paginate(page=1, per_page=10, error_out=False)
    return render_template('index.html', images=paginate.items, has_next=paginate.has_next)


# 分页显示主页的图片，点更多动态加载图片
@app.route('/index/images/<int:page>/<int:per_page>/')
def index_images(page, per_page):
    paginate = Image.query.order_by(db.desc(Image.id)).paginate(page=page, per_page=per_page, error_out=False)
    v_map = {'has_next': paginate.has_next}
    images = []
    # 主页json格式如何处理？传入的这3个变量是如何处理的？
    for image in paginate.items:
        # comments = []
        # # 循环添加完评论的内容
        # for i in range(0, min(2, len(image.comments))):
        #     comment = image.comments[i]
        #     comments.append({'username': comment.user.username, 'id': comment.user_id, 'content': comment.content})
        comment_username = []
        comment_uid = []
        comment_content = []
        for c_i in image.comments:
            comment_username.append(c_i.user.username)
            comment_uid.append(c_i.user.id)
            comment_content.append(c_i.content)

        # 日期：字符串类型，分别加上以上三个评论相关变量
        imgvo = {'created_date': str(image.created_date), 'id': image.id, 'url': image.url,
                 'comment_count': len(image.comments), 'user_id': image.user_id, 'head_url': image.user.head_url,
                 'username': image.user.username, 'comment_username': comment_username, 'comment_uid': comment_uid,
                 'comment_content': comment_content}
        images.append(imgvo)
    v_map['images'] = images
    return json.dumps(v_map)


# 图片详情页
# static忘记了一个/号，弄得一直加载CSS出现404...
@app.route('/image/<int:image_id>/')
@login_required
def image(image_id):
    # 由index里查询的图片id来查找相应的图片
    v_image = Image.query.get(image_id)
    # 用is代替==
    if v_image is None:
        return redirect('/')

    # 倒序显示评论,
    comments = Comment.query.filter_by(image_id=image_id).order_by(db.desc(Comment.id)).limit(20).all()
    return render_template('pageDetail.html', image=v_image, comments=comments)


# 个人详情页
@app.route('/profile/<int:user_id>')
@login_required     # 只有登录才能查看
def profile(user_id):
    user = User.query.get(user_id)
    if user is None:
        return redirect('/')

    # 分页显示用户的图片
    paginate = Image.query.filter_by(user_id=user_id).paginate(page=1, per_page=3, error_out=False)
    return render_template('profile.html', user=user, images=paginate.items, has_next=paginate.has_next)


# 分页显示个人详情页的图片，点更多动态加载图片
@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    paginate = Image.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
    # 判断是否还有下一页，是否需要显示更多按钮，paginate.has_next参数
    v_map = {'has_next': paginate.has_next}
    # 返回的图片信息也放到map里
    images = []
    for image in paginate.items:
        imgvo = {'id': image.id, 'url': image.url, 'comment_count': len(image.comments)}
        images.append(imgvo)
    v_map['images'] = images

    # 返回json格式的数据，用json.dumps而不是json.dump，然后靠前端处理相应的数据
    return json.dumps(v_map)


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
    if msg is not None:
        # category指信息来自哪里
        flash(msg, category=category)
    return redirect(target)


# 注册接口，点注册按钮需要判断会发生什么
@app.route('/reg/', methods=['GET', 'POST'])
def reg():
    # request.args是url里的值，request.form是body里的值
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()
    reg_mail = request.values.get('reg_mail').strip()

    if reg_mail == '':
        return redirect_with_msg('/regloginpage/', '邮箱不能为空', category='reglogin')
    if username == '' or password == '':
        return redirect_with_msg('/regloginpage/', '用户名或密码不能为空', category='reglogin')

    # 通过正则表达式判断邮箱格式是否正确
    # 转义字符，用户名@服务器域名，用户名只能以数字或字母开头和结尾
    regexp = '^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]@[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]{2,4}){1,}$'
    # 正则表达式转换为模式对象
    pat = re.compile(regexp)
    isok = pat.match(reg_mail)
    if isok is None:
        return redirect_with_msg('/regloginpage/', '邮箱格式错误', category='reglogin')

    user = User.query.filter_by(username=username).first()

    if user is not None:
        return redirect_with_msg('/regloginpage/', '用户名已存在', category='reglogin')

    # 更多判断

    # 为md5密码加盐
    salt = '.'.join(random.sample('0123456789abcdefghiABCDEFGHI', 10))
    m = hashlib.md5()
    # python3下字符串为Unicode类型，而hash传递时需要的是utf-8类型，因此，需要类型转换
    m.update((password+salt).encode('utf8'))
    # md5加密出来的十六进制字符串
    password = m.hexdigest()

    user = User(username, password, reg_mail, salt)
    db.session.add(user)
    db.session.commit()

    # 邮箱注册验证
    token = user.generate_activate_token()
    send_mail(user.email, 'Sharepics Email Activation', 'activate', username=user.username, token=token)
    # 此处实现邮箱验证和不验证的区别

    # 登录用户
    login_user(user)

    # next = request.values.get('next')
    # if next is not None and next.startswith('/'):
    #     return redirect(next)

    # return redirect('/')
    # 注册完跳到邮件发送页
    return render_template('mail.html')


# 登录接口，点登录按钮需要判断会发生什么
@app.route('/login/', methods=['GET', 'POST'])
def login():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    if username == '' or password == '':
        return redirect_with_msg('/regloginpage/', '用户名或密码不能为空', category='reglogin')

    user = User.query.filter_by(username=username).first()
    if user is None:
        return redirect_with_msg('/regloginpage/', '用户不存在', category='reglogin')

    m = hashlib.md5()
    m.update((password + user.salt).encode('utf8'))
    if m.hexdigest() != user.password:
        return redirect_with_msg('/regloginpage/', '密码错误', category='reglogin')

    if not user.status:
        return redirect_with_msg('/regloginpage/', '账户尚未激活，请激活后再登录', category='reglogin')

    login_user(user)

    # 需要经由login.html的表单form提交再在此处获取，因为login链接本来就是在表单form跳转到这的
    next = request.values.get('next')
    if next is not None and next.startswith('/'):
        return redirect(next)

    return redirect('/')


# 登出
@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/')


# 上传保存，返回相关url
def save_to_local(file, filename):
    # 保存目录
    save_dir = app.config['UPLOAD_DIR']
    # file里有save属性可以保存文件，os.path.join
    file.save(os.path.join(save_dir, filename))
    return '/image/' + filename


# 图片上传
@app.route('/upload/', methods=['POST'])
@login_required
def upload():
    # 调用request.files[名字]，流返回字节
    file = request.files['file']

    # 可见file里有很多HTTP头的属性
    # print(dir(file))

    # 文件的后缀匹配
    file_ext = ''
    if file.filename.find('.') > 0:
        # 分隔符查找最后一个.符号后的后缀，去掉空格，小写匹配
        file_ext = file.filename.rsplit('.', 1)[1].strip().lower()

    # 通过uuid生成唯一文件名，并且去除不合法字符，并且通过文件后缀名限制文件类型
    if file_ext in app.config['ALLOWED_EXT']:
        # 重命名文件名，因为用户上传的文件名可能包含html标签之类的，普遍做法是过滤掉不符合的词语
        # 演示用uuid生成随机文件名，uuid是通用唯一识别码,包含-
        file_name = str(uuid.uuid1()).replace('-', '') + '.' + file_ext

        # 保存文件到服务器
        # url = save_to_local(file, file_name)
        url = qiniu_upload_file(file, file_name)

        if url is not None:
            db.session.add(Image(url, current_user.id))
            db.session.commit()

    return redirect('/profile/%d' % current_user.id)


# 图片下载显示
@app.route('/image/<image_name>')
def view_image(image_name):
    # flask里带有此类api，send_from_directory
    return send_from_directory(app.config['UPLOAD_DIR'], image_name)


# 图片详情页增加评论，首页评论功能实现也用这个
@app.route('/addcomment/', methods=['POST'])
@login_required
def add_comment():
    # 类型转换，返回的可能是字符串
    image_id = int(request.values['image_id'])
    content = request.values['content']
    comment = Comment(content, image_id, current_user.id)
    db.session.add(comment)
    db.session.commit()

    return json.dumps({'code': 0, 'id': comment.id, 'content': content,
                       'username': comment.user.username, 'user_id': comment.user_id})


# flask-mail发送注册邮件
# 异步发送邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


# 视图函数名称不能设置为mail，否则会报错
def send_mail(to, subject, template, **kwargs):
    # 创建信息实例，recipients是个列表，包含所有收件人，Hello是邮箱的主题
    msg = Message(subject, recipients=[to])

    # 邮件发送给目标，可以有文本，两种方式呈现，你能看见怎样的取决于你的客户端
    # msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    # 使用多线程，在实际开发中，若是不使用异步、多线程等方式，网页会卡住
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


# 账户激活
@app.route('/activate/<token>/')
def activate(token):
    if User.check_activate_token(token):
        flash('激活成功')
        return redirect('/regloginpage/')
    else:
        flash('激活失败')
        return redirect('/')
