# -*- coding: utf-8 -*-

from threading import Thread

from flask import render_template
from flask_mail import Mail, Message

def send_async_email(app, msg):
    with app.app_context():
        app.mail.send(msg)

def send_mail(app, to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr