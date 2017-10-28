# -*- coding: utf-8 -*-
__author__ = 'vincent'

from flask import Blueprint

auth = Blueprint('auth', __name__)
from . import views
