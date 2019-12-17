# 模块导出文件
# -*- encoding=UTF-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# 出现了flask TemplateNotFound这个问题，原因在于Flask这个对象一个项目中只能创建一个，
# 我们把它放到了一个__init__.py文件中,创建的时候，没有template_folder这个属性，所以默认是templates
# 这个文件夹，由于__init___.py文件的目录与templates没有在统一目录下，所以找不到。
# app = Flask(__name__, template_folder='../templates', static_folder="", static_url_path="")

# 选中templates文件夹—>右键—>选择Mark Directory as Template Folder
app = Flask(__name__)
# 用于jinja2中支持break和continue的扩展
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
# 导入配置文件
app.config.from_pyfile('app.conf')

app.secret_key = 'nowcoder'

db = SQLAlchemy(app)

# 初始化
login_manager = LoginManager(app)
# 没登录自动跳转
login_manager.login_view = '/regloginpage/'
# 这个没看见显示
login_manager.login_message = '请登录后再访问！'
login_manager.login_message_category = 'info'

# 邮箱实例
mail = Mail(app)

# 这句需要加，否则出现页面404 not found；需要加在db语句的后面，因为models模块也加载了db，而加载两次db会报错
from nowstagram import models, views
