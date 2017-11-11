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


# 注意把代码覆盖集成到 manage.py 脚本中又一个小问题。test()函数收到 --coverage选项的值后再启动覆盖测试已经晚了，
# 那时全局作用域中的所有代码都已经执行了。为了检测的准确性，设定完整环境变量 FLASK_COVERAGE 后，脚本会重启。
# 再次运行时，脚本顶端的代码发现已经设定了环境变量，于是立即启动覆盖测试。
# coverage.coverage() 用于启动覆盖测试引擎。
# branch=True 选项开启分支覆盖分析除了跟踪那行代码已经执行之外，还要检查每个条件语句的 True 分支和 False 分支是否都执行了。
# include 选项用来限制程序包中文件的分析范围，只对这些文件中的代码进行覆盖检测。
# 如果不指定 include 选项，则虚拟环境中安装的全部扩展和测试代码都会包含进覆盖测试报告中，这会给报告添加很多杂项
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

cfg=os.getenv('FLASKY_CONFIG') or 'default'

app = create_app(cfg)
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
def test(coverage=False):
    """运行这个单元测试"""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest
    cfg='testing'
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


if __name__ == '__main__':
    manager.run()