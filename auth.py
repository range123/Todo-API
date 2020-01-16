from functools import wraps
from flask import request
import sqlite3

def check_token(token):
    conn = sqlite3.connect('Todo.db')
    c = conn.cursor()
    c.execute('select * from Auth where token=?',[token])
    x = c.fetchall()
    if len(x) == 0:
        conn.close()
        return 0
    if x[0][1] == 0:
        conn.close()
        return 1
    conn.close()
    return 2
def write_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        if 'X-API' in request.headers:
            token = request.headers['X-API']

        if not token:
            return {'reason': 'permissionDenied','message' : 'No Auth token provided'}, 401
        x = check_token(token)
        if x == 0:
            return {'reason': 'permissionDenied','message' : 'Invalid auth token'}, 401
        if x == 1:
            return {'reason': 'permissionDenied','message' : 'You do not have write access'}, 401

        # print('TOKEN: {}'.format(token))
        return f(*args, **kwargs)
    return decorated
def read_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        if 'X-API' in request.headers:
            token = request.headers['X-API']

        if not token:
            return {'reason': 'permissionDenied','message' : 'No Auth token provided'}, 401

        if check_token(token) == 0:
            return {'reason': 'permissionDenied','message' : 'You do not have read or write access'}, 401

        # print('TOKEN: {}'.format(token))
        return f(*args, **kwargs)
    return decorated