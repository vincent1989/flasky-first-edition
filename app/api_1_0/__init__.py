__author__ = 'vincent'
from flask import Blueprint


api = Blueprint('api', __name__)

from . import authentication
from . import comments
from . import decorators
from . import errors
from . import posts
from . import users

