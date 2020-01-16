import sqlite3
import os
if os.path.exists('Todo.db'):
    os.remove('Todo.db')
    print(os.path.exists('Todo.db'))
conn = sqlite3.connect('Todo.db')
cur = conn.cursor()
cur.execute('''CREATE TABLE Todo
             (id integer primary key,task text, dueby text, status text)''')
cur.execute('''CREATE TABLE Auth
             (token text primary key,read_write integer)''')
conn.commit()
conn.close()