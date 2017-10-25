from flask import Flask
from flask import abort
from flask.ext.script import Manager

app = Flask(__name__)
manager = Manager(app)

@app.route('/')
def index():
    return '<h1>Hello World!</h1>'

@app.route('/user/<name>')
def user(name):
    return '<h1>Hello %s</h1>'.format(name)

#
# @app.route('/user/<id>')
# def get_user(id):
#     user = load_user(id)
#     if not user:
#         abort(404)
#     return '<h1>Hello %s</h1>'.format(name)

if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()