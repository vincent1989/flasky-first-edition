# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
from flask import abort
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from datetime import datetime

app = Flask(__name__)

# 通过命令行方式管理 app
manager = Manager(app)
# 添加 Bootstrap
bootstrap = Bootstrap(app)

# 添加 Moment
moment = Moment(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)




if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()