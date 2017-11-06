#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'vincent'

import os
import sys
from app import create_app, db
from app.models import Role, User, Post

# 注意此处导入外部包时会有一个坑点儿，例如使用 from flask.ext.xxxx as xxxxxx 时，启动服务后会打出一堆的包导入记录，改成 from flask_xx 就可以了
# 例如: from flask.ext.script import Manager, Shell 改为 下面这一行就不会显示一堆 包导入记录了
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

reload(sys)
sys.setdefaultencoding("utf-8")

app = create_app(os.getenv('FLASKY_CONFIG') or 'default')
# 加载一些命令行工具包
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Post=Post)
# 命令行工具- 新增一个命令行参数 shell ，自动加载 对象
manager.add_command('shell', Shell(make_context=make_shell_context))
# 命令行工具- 添加一个命令行参数 db 加载数据库迁移命令
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """运行这个单元测试"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()