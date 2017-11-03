# -*- coding: utf-8 -*-
__author__ = 'vincent'

from flask import Blueprint

# 定义蓝本的名字 以及蓝本所在的包 或者 模块儿
main = Blueprint('main', __name__)

# 导入 路由 以及 错误处理程序
from . import views, errors
from ..models import Permission

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)