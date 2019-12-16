# -*- coding: utf-8 -*-

from nowtagram import app
from qiniu import Auth, put_data, put_stream, put_file
import os

# 先下载到本地路径
save_dir = app.config['UPLOAD_DIR']

# 需要填写你的 Access Key 和 Secret Key
access_key = app.config['QINIU_ACCESS_KEY']
secret_key = app.config['QINIU_SECRET_KEY']

# 构建鉴权对象
q = Auth(access_key, secret_key)

# 要上传的空间
bucket_name = app.config['QINIU_BUCKET_NAME']

# 域的前缀
domain_prefix = app.config['QINIU_DOMAIN']


# 图片上传保存，作用同views模块里的save_to_local，返回url
def qiniu_upload_file(source_file, save_file_name):
    # 生成上传 Token，可以指定过期时间等，3600s后过期
    token = q.upload_token(bucket_name, save_file_name)

    # 以下方法有问题
    # os.fstat() 方法用于返回文件描述符fd的状态，st_size: 文件大小，以byte为单位
    # ret, info = put_stream(token, save_file_name, source_file.stream,
    #                        "qiniu", os.fstat(source_file.stream.fileno()).st_size)
    # ret, info = put_stream(token, save_file_name, source_file.stream,
    #                        "qiniu", source_file.stream.tell())

    # 折中的方法，先存到本地，再用官方文档的方法put_file
    source_file.save(os.path.join(save_dir, save_file_name))
    ret, info = put_file(token, save_file_name, os.path.join(save_dir, save_file_name))

    # 此前服务端还有自己独有的上传 API，现在也推荐统一成基于客户端上传的工作方式
    # ret, info = put_data(token, save_file_name, source_file.stream)
    # print(type(source_file.stream)): <class 'tempfile.SpooledTemporaryFile'>

    # print(type(info.status_code), info)
    if info.status_code == 200:
        # 七牛云文件的外链域名
        return domain_prefix + save_file_name

    return None
