from flask import Flask,jsonify,request,json
from flask_restplus import Api, Resource, fields,reqparse
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3
from uuid import uuid4

# custom import from file auth.py
from auth import *


def get_date():
    from datetime import datetime

    return datetime.today().strftime('%Y-%m-%d')

def isdate(date):
    from datetime import datetime
    try:
        year,month,day = map(int,date.split('-'))
        return datetime(year,month,day).strftime('%Y-%m-%d')
        # return True
    except:
        return False

def isstatus(stat):
    v1 = ['finished','notstarted','inprogress']
    return stat.lower().replace(' ','') in v1

def getstatus(stat):
    v1 = ['finished','notstarted','inprogress']
    v2 = ['finished','not started','in progress']
    ind = v1.index(stat.lower().replace(' ',''))
    return v2[ind]

# Auth
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API',
        'scopes': {
            'read': 'Grant read-only access',
            'write': 'Grant read-write access',
        }
    }
}
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
    authorizations=authorizations,
    security={'apikey': 'read'}
)


ns = api.namespace('todos', description='TODO operations')
auth = api.namespace('auth', description='Authorization operations')
todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'dueby': fields.String(default=get_date(), description='The deadline for the task'),
    'status': fields.String(default="not started",description='The current status of the task'),
})
status = api.model('status', {
    'status': fields.String(required=True,description='The current status of the task',default="not started"),
})

parser_due = reqparse.RequestParser()
parser_due.add_argument('due_date', type=str, help='Date on which the due tasks are to be retreived')

class TodoDAO(object):
    def __init__(self):
        pass

    def get(self, id):
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('select * from Todo where id=?',[str(id)])
        x = cur.fetchone()
        try:
            ans = {}
            ans['id'] = x[0]
            ans['task'] = x[1]
            ans['dueby'] = x[2]
            ans['status'] = x[3]
            return ans
        except:
            api.abort(404, reason="Resource not found",message="Todo {} doesn't exist".format(id))

    def create(self, data):
        if 'task' not in data:
            api.abort(400, reason="badRequest",message="task field is required")
        else:
            if not isdate(data.get('dueby',0)):
                    api.abort(400, reason="badRequest",message="dueby is required and should be in YYYY-MM-DD format")
            else:
                data['dueby'] = isdate(data['dueby'])
                data['status'] = data.get('status','not started').lower().strip().replace(' ','')
                v1 = ['finished','notstarted','inprogress']
                if data['status'] not in v1:
                    api.abort(400, reason="badRequest",message="status should be one of [finished,not started,in progress]")
                vals = ['finished','not started','in progress']
                data['status'] = vals[v1.index(data['status'])]
                todo = data
                conn = sqlite3.connect('Todo.db')
                cur = conn.cursor()
                vals = [todo['task'],todo['dueby'],todo['status']]
                cur.execute('''insert into Todo(task,dueby,status) values(?,?,?)''',vals)
                conn.commit()
                cur.execute('select max(id) from Todo')
                todo['id'] = cur.fetchone()[0]
                return todo

    def update(self, id, data):
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        vals = [data['task'],data['status'],data['dueby'],str(id)]
        cur.execute('update Todo set task=?,status=?,dueby=? where id=?',vals)
        conn.commit()
        return self.get(id)

    def delete(self, id):
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('delete from Todo where id=?',[str(id)])
        conn.commit()
    
    def getall(self):
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('select * from Todo')
        temp = []
        for x in cur.fetchall():
            ans = {}
            ans['id'] = x[0]
            ans['task'] = x[1]
            ans['dueby'] = x[2]
            ans['status'] = x[3]
            temp.append(ans)
        return temp
    def query_due(self,date):
        if not isdate(date):
            api.abort(400, reason="badRequest",message="due_date parameter should be in YYYY-MM-DD format")
        date = isdate(date)
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('select * from Todo where dueby=?',[date])
        temp = []
        for x in cur.fetchall():
            ans = {}
            ans['id'] = x[0]
            ans['task'] = x[1]
            ans['dueby'] = x[2]
            ans['status'] = x[3]
            temp.append(ans)
        return temp
    def query_overdue(self):
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        date = get_date()
        cur.execute('select * from Todo where dueby<? and status!="finished"',[date])
        temp = []
        for x in cur.fetchall():
            ans = {}
            ans['id'] = x[0]
            ans['task'] = x[1]
            ans['dueby'] = x[2]
            ans['status'] = x[3]
            temp.append(ans)
        return temp
    def query_finished(self):
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('select * from Todo where status="finished"')
        temp = []
        for x in cur.fetchall():
            ans = {}
            ans['id'] = x[0]
            ans['task'] = x[1]
            ans['dueby'] = x[2]
            ans['status'] = x[3]
            temp.append(ans)
        return temp



DAO = TodoDAO()
# DAO.create({'task': 'Build an API'})
# DAO.create({'task': '?????'})
# DAO.create({'task': 'profit!'})


@ns.route('/')
@ns.response(401,'Not Authorized')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos',security='apikey')
    @read_required
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''

        return DAO.getall()

    @ns.doc('create_todo',security='apikey')
    @write_required
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/overdue')
@ns.response(401,'Not Authorized')
class TodoQueryOverdue(Resource):
    ''' lists all overdue tasks '''
    @ns.doc('list_overdue_todos',security='apikey')
    @read_required
    @ns.marshal_list_with(todo)
    def get(self):
        ''' Get a list of overdue tasks '''
        return DAO.query_overdue()

@ns.route('/finished')
@ns.response(401,'Not Authorized')
class TodoQueryFinished(Resource):
    ''' lists all finished tasks '''
    @ns.doc('list_finished_todos',security='apikey')
    @read_required
    @ns.marshal_list_with(todo)
    def get(self):
        ''' Get a list of finished tasks '''
        return DAO.query_finished()

@ns.route('/due')
@ns.response(401,'Not Authorized')
@ns.response(400,'Invalid due_date format')
class TodoQueryDue(Resource):
    ''' lists all tasks due on due_date '''
    @ns.doc('list_due_todos',security='apikey')
    @read_required
    @ns.expect(parser_due,required=True)
    @ns.marshal_list_with(todo)
    def get(self):
        ''' Get a list of all tasks due on due_date'''
        args = parser_due.parse_args()
        return DAO.query_due(args['due_date'])


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.response(401,'Not Authorized')
@ns.response(400,'Bad Request')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo',security='apikey')
    @read_required
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo',security='apikey')
    @write_required
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204
    @ns.doc('update_todo',security='apikey')
    @write_required
    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        data = api.payload
        if 'task' not in data:
            api.abort(400, reason="badRequest",message="updated task field not provided")
        elif not isdate(data.get('dueby','')):
            api.abort(400, reason="badRequest",message="dueby should be in YYYY-MM-DD format")
        elif not isstatus(data.get('status','')):
            api.abort(400, reason="badRequest",message="status should be one of [finished,not started,in progress]")
        data['status'] = getstatus(data['status'])
        
        return DAO.update(id, api.payload)

    @ns.doc('changestatus_todo',security='apikey')
    @write_required
    @ns.expect(status)
    @ns.marshal_with(todo)
    def patch(self,id):
        '''Update status of a task given its identifier and new status'''
        x= DAO.get(id)
        x['status'] = api.payload.get('status',x['status'])
        # v1 = ['finished','notstarted','inprogress']
        if not isstatus(x['status']):
            api.abort(400, reason="badRequest",message="status should be one of [finished,not started,in progress]")
        x['status'] = getstatus(x['status'])
        return DAO.update(id,x)


auth_model = api.model('auth', {
    'token': fields.String(required=True,description='The Auth token or secret key generated'),
    'type' : fields.String(required=True,description='Type of the key (either read or write(read and write))')
})

@auth.route('/read')
class AuthRead(Resource):
    ''' Generate a read access token'''
    @auth.doc('create_readtoken')
    @ns.marshal_with(auth_model)
    def get(self):
        ''' Generate a read access token'''
        token = str(uuid4())
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('insert into Auth values(?,0)',[token])
        conn.commit()
        conn.close()
        return {'token' : token,'type' : 'read'}

@auth.route('/write')
class AuthWrite(Resource):
    ''' Generate a write access token'''
    @auth.doc('create_writetoken')
    @ns.marshal_with(auth_model)
    def get(self):
        ''' Generate a write access token'''
        token = str(uuid4())
        conn = sqlite3.connect('Todo.db')
        cur = conn.cursor()
        cur.execute('insert into Auth values(?,1)',[token])
        conn.commit()
        conn.close()
        return {'token' : token,'type' : 'write'}
        

if __name__ == '__main__':
    app.run()