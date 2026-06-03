from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3, hashlib, os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production-xyz123')
DB = 'hr.db'

# ---------- DB helpers ----------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def query(sql, args=(), one=False):
    conn = get_db()
    cur = conn.execute(sql, args)
    conn.commit()
    rv = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return rv

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ---------- Auth decorators ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'manager':
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated

# ---------- Pages ----------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

# ---------- Auth API ----------
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json
    user = query('SELECT * FROM users WHERE login=? AND password=?',
                 (d['login'], hash_pw(d['password'])), one=True)
    if not user:
        return jsonify({'error': 'Неверный логин или пароль'}), 401
    session['user_id'] = user['id']
    session['role']    = user['role']
    session['name']    = user['name']
    session['emp_id']  = user['employee_id']
    return jsonify({'role': user['role'], 'name': user['name']})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/me')
@login_required
def api_me():
    return jsonify({
        'name':   session['name'],
        'role':   session['role'],
        'emp_id': session['emp_id']
    })

# ---------- Employees API ----------
@app.route('/api/employees', methods=['GET'])
@login_required
def get_employees():
    rows = query('SELECT * FROM employees ORDER BY lname')
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees', methods=['POST'])
@login_required
@manager_required
def add_employee():
    d = request.json
    query('INSERT INTO employees (fname,lname,dept,position,since) VALUES (?,?,?,?,?)',
          (d['fname'], d['lname'], d['dept'], d['position'], d['since']))
    return jsonify({'ok': True})

@app.route('/api/employees/<int:eid>', methods=['PUT'])
@login_required
@manager_required
def update_employee(eid):
    d = request.json
    query('UPDATE employees SET fname=?,lname=?,dept=?,position=? WHERE id=?',
          (d['fname'], d['lname'], d['dept'], d['position'], eid))
    return jsonify({'ok': True})

@app.route('/api/employees/<int:eid>', methods=['DELETE'])
@login_required
@manager_required
def delete_employee(eid):
    query('DELETE FROM employees WHERE id=?', (eid,))
    query('DELETE FROM kpis WHERE employee_id=?', (eid,))
    return jsonify({'ok': True})

# ---------- KPI API ----------
@app.route('/api/kpis', methods=['GET'])
@login_required
def get_kpis():
    if session['role'] == 'manager':
        rows = query('''SELECT k.*, e.fname, e.lname FROM kpis k
                        JOIN employees e ON k.employee_id=e.id
                        ORDER BY k.date DESC''')
    else:
        rows = query('''SELECT k.*, e.fname, e.lname FROM kpis k
                        JOIN employees e ON k.employee_id=e.id
                        WHERE k.employee_id=? ORDER BY k.date DESC''',
                     (session['emp_id'],))
    return jsonify([dict(r) for r in rows])

@app.route('/api/kpis', methods=['POST'])
@login_required
@manager_required
def add_kpi():
    d = request.json
    query('INSERT INTO kpis (employee_id,metric,score,comment,date) VALUES (?,?,?,?,?)',
          (d['employee_id'], d['metric'], d['score'], d.get('comment',''), d['date']))
    return jsonify({'ok': True})

@app.route('/api/kpis/<int:kid>', methods=['DELETE'])
@login_required
@manager_required
def delete_kpi(kid):
    query('DELETE FROM kpis WHERE id=?', (kid,))
    return jsonify({'ok': True})

# ---------- Tasks API ----------
@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    if session['role'] == 'manager':
        rows = query('''SELECT t.*, e.fname, e.lname FROM tasks t
                        JOIN employees e ON t.employee_id=e.id
                        ORDER BY t.created_at DESC''')
    else:
        rows = query('''SELECT t.*, e.fname, e.lname FROM tasks t
                        JOIN employees e ON t.employee_id=e.id
                        WHERE t.employee_id=? ORDER BY t.created_at DESC''',
                     (session['emp_id'],))
    return jsonify([dict(r) for r in rows])

@app.route('/api/tasks', methods=['POST'])
@login_required
@manager_required
def add_task():
    d = request.json
    from datetime import date
    query('INSERT INTO tasks (employee_id,title,description,status,created_at) VALUES (?,?,?,?,?)',
          (d['employee_id'], d['title'], d.get('description',''), 'new', date.today().isoformat()))
    return jsonify({'ok': True})

@app.route('/api/tasks/<int:tid>/done', methods=['POST'])
@login_required
def complete_task(tid):
    from datetime import date
    task = query('SELECT * FROM tasks WHERE id=?', (tid,), one=True)
    if not task:
        return jsonify({'error': 'Not found'}), 404
    if session['role'] == 'employee' and task['employee_id'] != session['emp_id']:
        return jsonify({'error': 'Forbidden'}), 403
    query('UPDATE tasks SET status=?, done_at=? WHERE id=?',
          ('done', date.today().isoformat(), tid))
    return jsonify({'ok': True})

@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
@login_required
@manager_required
def delete_task(tid):
    query('DELETE FROM tasks WHERE id=?', (tid,))
    return jsonify({'ok': True})

# ---------- Reports API ----------
@app.route('/api/reports/summary')
@login_required
@manager_required
def report_summary():
    rows = query('''
        SELECT e.dept,
               COUNT(DISTINCT e.id) as emp_count,
               ROUND(AVG(k.score),1) as avg_kpi
        FROM employees e
        LEFT JOIN kpis k ON k.employee_id=e.id
        GROUP BY e.dept
    ''')
    return jsonify([dict(r) for r in rows])

@app.route('/api/reports/employees')
@login_required
@manager_required
def report_employees():
    rows = query('''
        SELECT e.id, e.fname, e.lname, e.dept, e.position,
               COUNT(k.id) as kpi_count,
               ROUND(AVG(k.score),1) as avg_kpi,
               MAX(k.score) as best_score
        FROM employees e
        LEFT JOIN kpis k ON k.employee_id=e.id
        GROUP BY e.id ORDER BY avg_kpi DESC
    ''')
    return jsonify([dict(r) for r in rows])

# ---------- Init DB ----------
def init_db():
    conn = get_db()
    conn.executescript(open('schema.sql').read())
    conn.close()

if __name__ == '__main__':
    if not os.path.exists(DB):
        init_db()
    app.run(debug=True)