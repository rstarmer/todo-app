import os
from flask import Flask, request, session, g, redirect, url_for, render_template, abort, flash, jsonify
import sqlite3
from datetime import datetime
import objectstore
# Configuration

DATABASE='flaskr.db'
DEBUG = True
SECRET_KEY = 'secret'
USERNAME = 'admin'
PASSWORD = 'password'
HOST = '0.0.0.0'
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar("APP_CONFIG")

objstr = objectstore.ObjectStore(app.config['KEYSTONE_AUTH_URL'], app.config['SWIFT_USER'], app.config['SWIFT_PASS'], app.config['TENANT_NAME'], app.config['KEYSTONE_AUTH_VERSION'], app.config['CONTAINER'], app.config['SWIFT_CONTAINER_BASE_PATH'])
# Code to connect to the flaskr database from config
def connect_db():
    """ Connects to the database """
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

# Code to initialize/Create the database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Open database connection
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

# close database connection
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    """Searches the database for entries, then displays them."""
    db = get_db()
    cur = db.execute('select * from entries order by entries.id desc')
    entries = cur.fetchall()
    return render_template('index.html', entries=entries)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login/authentication/session management."""
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """User logout/authentication/session management."""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_entry():
    """Add new post to database."""
    if not session.get('logged_in'):
        abort(401)
    db = get_db() 
#    fileitem = request.files['file']
#    file_data = fileitem.read()
    if request.files['file']:
       fileitem = request.files['file']
       file_data = fileitem.read()
       now = datetime.now()
       objstr.put_object(fileitem.filename, file_data)
       db.execute('insert into entries(title, text, attachment_container, objectname) values(?,?,?,?)', [request.form['title'], request.form['text'], app.config['CONTAINER'], fileitem.filename])
       db.commit()
    else:
       db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
       db.commit()

    flash('New entry was successfully posted')
    return redirect(url_for('index'))

@app.route('/delete/<post_id>', methods=['GET'])
def delete_entry(post_id):
    '''Delete post from database'''
    result = { 'status':0, 'message': 'Error'  }
    try:
        db = get_db()
        db.execute('delete from entries where id=' + post_id)
        db.commit()
        result = { 'status':1, 'message': "Post Deleted" }
    except Exception as e:
        result = { 'status':0, 'message': repr(e) }

    return jsonify(result)

@app.route('/gettempurl/<post_id>', methods=['GET'])
def get_temp_url(post_id):
    
    result = { 'status':0, 'message': 'Error'  }
    try:
        db = get_db()
        cur = db.execute('select attachment_container, objectname from entries where id=' + post_id)
        rv = cur.fetchone()
        container = rv[0]
        objectname = rv[1]
        tempurl = objstr.get_temp_url(objectname, 60)
        result = { 'status':1, 'url': tempurl }
    except Exception as e:
        result = { 'status':0, 'url': repr(e) }

    return jsonify(result)


if __name__ == '__main__':
    init_db()
    if objstr.check_container_stats(app.config['CONTAINER']):
       pass
    else:
       objstr.create_container(app.config['CONTAINER'])

    app.run(host=app.config['HOST'])
    
