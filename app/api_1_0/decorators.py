# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from functools import wraps
from flask import g
from .errors import forbidden

reload(sys)
sys.setdefaultencoding("utf-8")

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('没有足够的权限')
            return f(*args, **kwargs)
        return decorated_function
    return decorator