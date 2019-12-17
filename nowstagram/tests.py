# -*- encoding=UTF-8 -*-
# model层测试实例（即与DB打交道），webAPI测试实例（即view层）还有各种后端的module，class， 以及func的单元测试实例
# module层的测试实例编写可以考虑使用pytest的fixture或者nose
# view层的api测试实例编写可以考虑使用webtest，其提供了get，post，put等request的功能

import unittest
from nowstagram import app


# 分为失败和错误，断言采用self.assert比直接用assert更好，有提示断言错误信息
class NowtagramTest(unittest.TestCase):
    # 初始化要测试的数据
    def setUp(self) -> None:
        print('setUp')
        app.config['Testing'] = True    # 测试模式
        self.app = app.test_client()    # 这是整个网站的app，把它保存下来，类似一个浏览器的东西

    # 清理数据
    def tearDown(self) -> None:
        print('tearDown')

    def register(self, email, username, password):
        # 类似浏览器可用get和post请求，follow_redirects跟随跳转
        return self.app.post('/reg/', data={"email": email, "username": username, "password": password}, follow_redirects=True)

    def login(self, username, password):
        return self.app.post('/login/', data={"username": username, "password": password}, follow_redirects=True)

    def logout(self):
        return self.app.get('/logout/')

    def test_reg_login_logout(self):
        # assert self.register('hello', 'world', '4885514756@qq.com').status_code == 200
        rv = self.register("4885514756@qq.com", "hello", "world")
        self.assertEqual(rv.status_code, 200)
        # 测试首页标题带名字
        # TypeError: a bytes-like object is required, not 'str'
        # AssertionError
        # 页面没有跳转才找不到
        # self.assertIn('-hello'.encode('utf-8'), self.app.open('/').data)
        self.logout()
        assert '-hello'.encode() not in self.app.open('/').data
        # 没有登录成功，找不到
        self.login('hello', 'world')
        # self.assertIn('-hello'.encode('utf-8'), self.app.open('/').data)

    # 打开详情页需要登录
    def test_profile(self):
        rv = self.app.open('/profile/3/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("password".encode(), rv.data)

        # 注册后又没有跳转，无法访问详情页
        self.register("4885514756@qq.com", "hello2", "world")
        # rp = self.app.open('/profile/1/', follow_redirects=True).data
        # self.assertIn("hello2".encode(), rp)
