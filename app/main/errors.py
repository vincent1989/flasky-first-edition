# -*- coding: utf-8 -*-
__author__ = 'vincent'

from flask import render_template
from flask import request
from flask import jsonify
from . import main

@main.app_errorhandler(403)
def forbidden(e):
    '''这个错误处理程序检查 Accept 请求首部（Werkzeug 将其解码为 request.accept_mimetypes）根据首部的值决定客户端期望接收的响应格式
    浏览器一般不限制响应格式，所以只为接收JSON格式而不接收HTML格式的客户端生成JSON格式响应'''
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'frobidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    '''这个错误处理程序检查 Accept 请求首部（Werkzeug 将其解码为 request.accept_mimetypes）根据首部的值决定客户端期望接收的响应格式
    浏览器一般不限制响应格式，所以只为接收JSON格式而不接收HTML格式的客户端生成JSON格式响应'''
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404



@main.app_errorhandler(500)
def internal_server_error(e):
    '''这个错误处理程序检查 Accept 请求首部（Werkzeug 将其解码为 request.accept_mimetypes）根据首部的值决定客户端期望接收的响应格式
    浏览器一般不限制响应格式，所以只为接收JSON格式而不接收HTML格式的客户端生成JSON格式响应'''
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
