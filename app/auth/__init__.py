# -*- coding: utf-8 -*-
__author__ = 'vincent'

import sys
from flask import Blueprint

auth = Blueprint('auth', __name__)
from . import views


reload(sys)
sys.setdefaultencoding("utf-8")
