import app
from flask import render_template

with app.app.test_request_context('/'):
    templates = [
        'base.html', 'login.html', 'register.html', 'dashboard.html',
        'students.html', 'add_student.html', 'edit_student.html', 'grades.html'
    ]
    for tpl in templates:
        try:
            render_template(tpl)
            print('OK', tpl)
        except Exception as exc:
            print('ERROR', tpl, type(exc).__name__)
            raise
