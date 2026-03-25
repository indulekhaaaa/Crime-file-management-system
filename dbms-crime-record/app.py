"""
Crime Record Management System — Flask Backend
"""

import sqlite3
import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'crime_records.db')
SCHEMA   = os.path.join(BASE_DIR, 'schema.sql')
SAMPLE   = os.path.join(BASE_DIR, 'sample_data.sql')

app = Flask(__name__)
app.secret_key = 'crms-secret-key-2026-change-in-production'


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv  = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(sql, args=()):
    db  = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


def init_db():
    """Create tables and load sample data if DB is new."""
    db_exists = os.path.exists(DATABASE)
    with app.app_context():
        db = get_db()
        with open(SCHEMA) as f:
            db.executescript(f.read())
        if not db_exists:
            with open(SAMPLE) as f:
                raw = f.read()
            # Re-hash the placeholder passwords properly
            db.executescript(raw)
            # Fix admin password
            db.execute(
                "UPDATE users SET password_hash=? WHERE username='admin'",
                (generate_password_hash('admin123'),)
            )
            db.execute(
                "UPDATE users SET password_hash=? WHERE username='officer1'",
                (generate_password_hash('officer123'),)
            )
            db.commit()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def log_action(table, operation, record_id, details=''):
    user = session.get('username', 'system')
    execute_db(
        "INSERT INTO audit_log (table_name,operation,record_id,changed_by,details) VALUES (?,?,?,?,?)",
        (table, operation, record_id, user, details)
    )


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = query_db("SELECT * FROM users WHERE username=?", (username,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    total_criminals = query_db("SELECT COUNT(*) AS c FROM criminal", one=True)['c']
    total_firs      = query_db("SELECT COUNT(*) AS c FROM fir", one=True)['c']
    open_cases      = query_db("SELECT COUNT(*) AS c FROM fir WHERE status='Open'", one=True)['c']
    under_inv       = query_db("SELECT COUNT(*) AS c FROM fir WHERE status='Under Investigation'", one=True)['c']
    closed_cases    = query_db("SELECT COUNT(*) AS c FROM fir WHERE status='Closed'", one=True)['c']
    total_officers  = query_db("SELECT COUNT(*) AS c FROM police_officer", one=True)['c']
    repeat_offenders= query_db("SELECT COUNT(*) AS c FROM criminal WHERE previous_cases > 2", one=True)['c']

    recent_firs = query_db("""
        SELECT f.fir_id, f.crime_type, f.date_filed, f.status,
               c.name AS criminal_name, p.name AS officer_name
        FROM fir f
        JOIN criminal c       ON f.criminal_id = c.criminal_id
        JOIN police_officer p ON f.officer_id  = p.officer_id
        ORDER BY f.date_filed DESC LIMIT 5
    """)

    crime_stats = query_db("""
        SELECT crime_type, COUNT(*) AS total
        FROM fir GROUP BY crime_type ORDER BY total DESC LIMIT 6
    """)

    return render_template('dashboard.html',
        total_criminals=total_criminals,
        total_firs=total_firs,
        open_cases=open_cases,
        under_inv=under_inv,
        closed_cases=closed_cases,
        total_officers=total_officers,
        repeat_offenders=repeat_offenders,
        recent_firs=recent_firs,
        crime_stats=crime_stats
    )


# ---------------------------------------------------------------------------
# Criminal Management
# ---------------------------------------------------------------------------
@app.route('/criminals')
@login_required
def criminals_list():
    search = request.args.get('search', '').strip()
    if search:
        rows = query_db(
            "SELECT * FROM criminal WHERE name LIKE ? ORDER BY name",
            (f'%{search}%',)
        )
    else:
        rows = query_db("SELECT * FROM criminal ORDER BY criminal_id DESC")
    return render_template('criminals/index.html', criminals=rows, search=search)


@app.route('/criminals/add', methods=['GET', 'POST'])
@login_required
def criminal_add():
    if request.method == 'POST':
        name   = request.form.get('name', '').strip()
        age    = request.form.get('age', 0)
        gender = request.form.get('gender', '')
        addr   = request.form.get('address', '').strip()
        prev   = request.form.get('previous_cases', 0)
        if not name or not gender:
            flash('Name and gender are required.', 'danger')
            return render_template('criminals/form.html', action='Add', criminal=request.form)
        cid = execute_db(
            """INSERT INTO criminal (name,age,gender,address,previous_cases,updated_at)
               VALUES (?,?,?,?,?,datetime('now'))""",
            (name, age, gender, addr, prev)
        )
        log_action('criminal', 'INSERT', cid, f'Added criminal: {name}')
        flash('Criminal record added successfully.', 'success')
        return redirect(url_for('criminals_list'))
    return render_template('criminals/form.html', action='Add', criminal={})


@app.route('/criminals/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
def criminal_edit(cid):
    criminal = query_db("SELECT * FROM criminal WHERE criminal_id=?", (cid,), one=True)
    if not criminal:
        flash('Criminal not found.', 'danger')
        return redirect(url_for('criminals_list'))
    if request.method == 'POST':
        name   = request.form.get('name', '').strip()
        age    = request.form.get('age', 0)
        gender = request.form.get('gender', '')
        addr   = request.form.get('address', '').strip()
        prev   = request.form.get('previous_cases', 0)
        execute_db(
            """UPDATE criminal SET name=?,age=?,gender=?,address=?,previous_cases=?,
               updated_at=datetime('now') WHERE criminal_id=?""",
            (name, age, gender, addr, prev, cid)
        )
        log_action('criminal', 'UPDATE', cid, f'Updated criminal: {name}')
        flash('Criminal record updated.', 'success')
        return redirect(url_for('criminals_list'))
    return render_template('criminals/form.html', action='Edit', criminal=criminal)


@app.route('/criminals/<int:cid>/view')
@login_required
def criminal_view(cid):
    criminal = query_db("SELECT * FROM criminal WHERE criminal_id=?", (cid,), one=True)
    if not criminal:
        flash('Criminal not found.', 'danger')
        return redirect(url_for('criminals_list'))
    firs = query_db("""
        SELECT f.*, p.name AS officer_name
        FROM fir f JOIN police_officer p ON f.officer_id=p.officer_id
        WHERE f.criminal_id=? ORDER BY f.date_filed DESC
    """, (cid,))
    return render_template('criminals/view.html', criminal=criminal, firs=firs)


@app.route('/criminals/<int:cid>/delete', methods=['POST'])
@login_required
@admin_required
def criminal_delete(cid):
    criminal = query_db("SELECT name FROM criminal WHERE criminal_id=?", (cid,), one=True)
    if criminal:
        execute_db("DELETE FROM criminal WHERE criminal_id=?", (cid,))
        log_action('criminal', 'DELETE', cid, f'Deleted criminal: {criminal["name"]}')
        flash('Criminal record deleted.', 'success')
    return redirect(url_for('criminals_list'))


# ---------------------------------------------------------------------------
# FIR Management
# ---------------------------------------------------------------------------
@app.route('/fir')
@login_required
def fir_list():
    status_filter = request.args.get('status', '')
    crime_filter  = request.args.get('crime_type', '').strip()
    sql = """
        SELECT f.*, c.name AS criminal_name, p.name AS officer_name
        FROM fir f
        JOIN criminal c       ON f.criminal_id = c.criminal_id
        JOIN police_officer p ON f.officer_id  = p.officer_id
        WHERE 1=1
    """
    args = []
    if status_filter:
        sql += " AND f.status=?"
        args.append(status_filter)
    if crime_filter:
        sql += " AND f.crime_type LIKE ?"
        args.append(f'%{crime_filter}%')
    sql += " ORDER BY f.date_filed DESC"
    firs = query_db(sql, args)
    crime_types = query_db("SELECT DISTINCT crime_type FROM fir ORDER BY crime_type")
    return render_template('fir/index.html', firs=firs,
                           status_filter=status_filter,
                           crime_filter=crime_filter,
                           crime_types=crime_types)


@app.route('/fir/add', methods=['GET', 'POST'])
@login_required
def fir_add():
    criminals = query_db("SELECT criminal_id, name FROM criminal ORDER BY name")
    officers  = query_db("SELECT officer_id, name, rank FROM police_officer ORDER BY name")
    if request.method == 'POST':
        crime_type  = request.form.get('crime_type', '').strip()
        date_filed  = request.form.get('date_filed', datetime.now().strftime('%Y-%m-%d'))
        location    = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        criminal_id = request.form.get('criminal_id')
        officer_id  = request.form.get('officer_id')
        status      = request.form.get('status', 'Open')
        if not all([crime_type, location, criminal_id, officer_id]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('fir/form.html', action='Register', fir=request.form,
                                   criminals=criminals, officers=officers)
        fid = execute_db(
            """INSERT INTO fir (crime_type,date_filed,location,description,
               criminal_id,officer_id,status,updated_at)
               VALUES (?,?,?,?,?,?,?,datetime('now'))""",
            (crime_type, date_filed, location, description, criminal_id, officer_id, status)
        )
        # Auto-create case_status entry
        execute_db(
            "INSERT INTO case_status (fir_id) VALUES (?)", (fid,)
        )
        # Increment previous_cases for criminal
        execute_db(
            "UPDATE criminal SET previous_cases=previous_cases+1 WHERE criminal_id=?",
            (criminal_id,)
        )
        log_action('fir', 'INSERT', fid, f'Registered FIR #{fid}: {crime_type}')
        flash('FIR registered successfully.', 'success')
        return redirect(url_for('fir_list'))
    return render_template('fir/form.html', action='Register', fir={},
                           criminals=criminals, officers=officers)


@app.route('/fir/<int:fid>/edit', methods=['GET', 'POST'])
@login_required
def fir_edit(fid):
    fir = query_db("SELECT * FROM fir WHERE fir_id=?", (fid,), one=True)
    if not fir:
        flash('FIR not found.', 'danger')
        return redirect(url_for('fir_list'))
    criminals = query_db("SELECT criminal_id, name FROM criminal ORDER BY name")
    officers  = query_db("SELECT officer_id, name, rank FROM police_officer ORDER BY name")
    if request.method == 'POST':
        crime_type  = request.form.get('crime_type', '').strip()
        date_filed  = request.form.get('date_filed')
        location    = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        criminal_id = request.form.get('criminal_id')
        officer_id  = request.form.get('officer_id')
        status      = request.form.get('status', 'Open')
        execute_db(
            """UPDATE fir SET crime_type=?,date_filed=?,location=?,description=?,
               criminal_id=?,officer_id=?,status=?,updated_at=datetime('now')
               WHERE fir_id=?""",
            (crime_type, date_filed, location, description,
             criminal_id, officer_id, status, fid)
        )
        log_action('fir', 'UPDATE', fid, f'Updated FIR #{fid}')
        flash('FIR updated successfully.', 'success')
        return redirect(url_for('fir_list'))
    return render_template('fir/form.html', action='Edit', fir=fir,
                           criminals=criminals, officers=officers)


@app.route('/fir/<int:fid>/view')
@login_required
def fir_view(fid):
    fir = query_db("""
        SELECT f.*, c.name AS criminal_name, c.age, c.gender,
               p.name AS officer_name, p.rank, p.station
        FROM fir f
        JOIN criminal c       ON f.criminal_id=c.criminal_id
        JOIN police_officer p ON f.officer_id=p.officer_id
        WHERE f.fir_id=?
    """, (fid,), one=True)
    if not fir:
        flash('FIR not found.', 'danger')
        return redirect(url_for('fir_list'))
    case = query_db("SELECT * FROM case_status WHERE fir_id=?", (fid,), one=True)
    return render_template('fir/view.html', fir=fir, case=case)


@app.route('/fir/<int:fid>/delete', methods=['POST'])
@login_required
@admin_required
def fir_delete(fid):
    execute_db("DELETE FROM fir WHERE fir_id=?", (fid,))
    log_action('fir', 'DELETE', fid, f'Deleted FIR #{fid}')
    flash('FIR deleted.', 'success')
    return redirect(url_for('fir_list'))


# ---------------------------------------------------------------------------
# Officer Management
# ---------------------------------------------------------------------------
@app.route('/officers')
@login_required
def officers_list():
    search = request.args.get('search', '').strip()
    if search:
        rows = query_db(
            "SELECT * FROM police_officer WHERE name LIKE ? OR station LIKE ? ORDER BY name",
            (f'%{search}%', f'%{search}%')
        )
    else:
        rows = query_db("SELECT * FROM police_officer ORDER BY officer_id DESC")
    return render_template('officers/index.html', officers=rows, search=search)


@app.route('/officers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def officer_add():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        rank    = request.form.get('rank', '').strip()
        station = request.form.get('station', '').strip()
        badge   = request.form.get('badge_no', '').strip()
        phone   = request.form.get('phone', '').strip()
        if not all([name, rank, station]):
            flash('Name, rank, and station are required.', 'danger')
            return render_template('officers/form.html', action='Add', officer=request.form)
        oid = execute_db(
            """INSERT INTO police_officer (name,rank,station,badge_no,phone,updated_at)
               VALUES (?,?,?,?,?,datetime('now'))""",
            (name, rank, station, badge or None, phone or None)
        )
        log_action('police_officer', 'INSERT', oid, f'Added officer: {name}')
        flash('Officer record added.', 'success')
        return redirect(url_for('officers_list'))
    return render_template('officers/form.html', action='Add', officer={})


@app.route('/officers/<int:oid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def officer_edit(oid):
    officer = query_db("SELECT * FROM police_officer WHERE officer_id=?", (oid,), one=True)
    if not officer:
        flash('Officer not found.', 'danger')
        return redirect(url_for('officers_list'))
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        rank    = request.form.get('rank', '').strip()
        station = request.form.get('station', '').strip()
        badge   = request.form.get('badge_no', '').strip()
        phone   = request.form.get('phone', '').strip()
        execute_db(
            """UPDATE police_officer SET name=?,rank=?,station=?,badge_no=?,phone=?,
               updated_at=datetime('now') WHERE officer_id=?""",
            (name, rank, station, badge or None, phone or None, oid)
        )
        log_action('police_officer', 'UPDATE', oid, f'Updated officer: {name}')
        flash('Officer record updated.', 'success')
        return redirect(url_for('officers_list'))
    return render_template('officers/form.html', action='Edit', officer=officer)


@app.route('/officers/<int:oid>/view')
@login_required
def officer_view(oid):
    officer = query_db("SELECT * FROM police_officer WHERE officer_id=?", (oid,), one=True)
    if not officer:
        flash('Officer not found.', 'danger')
        return redirect(url_for('officers_list'))
    firs = query_db("""
        SELECT f.*, c.name AS criminal_name
        FROM fir f JOIN criminal c ON f.criminal_id=c.criminal_id
        WHERE f.officer_id=? ORDER BY f.date_filed DESC
    """, (oid,))
    return render_template('officers/view.html', officer=officer, firs=firs)


@app.route('/officers/<int:oid>/delete', methods=['POST'])
@login_required
@admin_required
def officer_delete(oid):
    officer = query_db("SELECT name FROM police_officer WHERE officer_id=?", (oid,), one=True)
    if officer:
        execute_db("DELETE FROM police_officer WHERE officer_id=?", (oid,))
        log_action('police_officer', 'DELETE', oid, f'Deleted officer: {officer["name"]}')
        flash('Officer deleted.', 'success')
    return redirect(url_for('officers_list'))


# ---------------------------------------------------------------------------
# Case Tracking
# ---------------------------------------------------------------------------
@app.route('/cases')
@login_required
def cases_list():
    stage_filter  = request.args.get('stage', '')
    court_filter  = request.args.get('court', '')
    sql = """
        SELECT cs.*, f.crime_type, f.location, f.status AS fir_status,
               c.name AS criminal_name, p.name AS officer_name
        FROM case_status cs
        JOIN fir f            ON cs.fir_id = f.fir_id
        JOIN criminal c       ON f.criminal_id = c.criminal_id
        JOIN police_officer p ON f.officer_id  = p.officer_id
        WHERE 1=1
    """
    args = []
    if stage_filter:
        sql += " AND cs.investigation_stage=?"
        args.append(stage_filter)
    if court_filter:
        sql += " AND cs.court_status=?"
        args.append(court_filter)
    sql += " ORDER BY cs.updated_at DESC"
    cases = query_db(sql, args)
    stages = ['Initial Inquiry','Evidence Collection','Suspect Interrogation',
              'Charge Sheet Filed','Completed']
    courts = ['Pending','Trial Ongoing','Acquitted','Convicted','Case Dismissed']
    return render_template('cases/index.html', cases=cases,
                           stage_filter=stage_filter, court_filter=court_filter,
                           stages=stages, courts=courts)


@app.route('/cases/<int:csid>/edit', methods=['GET', 'POST'])
@login_required
def case_edit(csid):
    case = query_db("""
        SELECT cs.*, f.crime_type, f.location, f.fir_id,
               c.name AS criminal_name, p.name AS officer_name
        FROM case_status cs
        JOIN fir f            ON cs.fir_id=f.fir_id
        JOIN criminal c       ON f.criminal_id=c.criminal_id
        JOIN police_officer p ON f.officer_id=p.officer_id
        WHERE cs.case_id=?
    """, (csid,), one=True)
    if not case:
        flash('Case not found.', 'danger')
        return redirect(url_for('cases_list'))
    stages = ['Initial Inquiry','Evidence Collection','Suspect Interrogation',
              'Charge Sheet Filed','Completed']
    courts = ['Pending','Trial Ongoing','Acquitted','Convicted','Case Dismissed']
    if request.method == 'POST':
        stage  = request.form.get('investigation_stage')
        court  = request.form.get('court_status')
        notes  = request.form.get('notes', '').strip()
        # Sync FIR status
        fir_status = 'Open'
        if stage == 'Completed' and court in ('Convicted','Acquitted','Case Dismissed'):
            fir_status = 'Closed'
        elif stage in ('Evidence Collection','Suspect Interrogation','Charge Sheet Filed'):
            fir_status = 'Under Investigation'
        execute_db(
            """UPDATE case_status SET investigation_stage=?,court_status=?,notes=?,
               updated_at=datetime('now') WHERE case_id=?""",
            (stage, court, notes, csid)
        )
        execute_db(
            "UPDATE fir SET status=?,updated_at=datetime('now') WHERE fir_id=?",
            (fir_status, case['fir_id'])
        )
        log_action('case_status', 'UPDATE', csid, f'Stage: {stage}, Court: {court}')
        flash('Case status updated.', 'success')
        return redirect(url_for('cases_list'))
    return render_template('cases/form.html', case=case, stages=stages, courts=courts)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@app.route('/reports')
@login_required
def reports():
    # Open cases
    open_cases = query_db("""
        SELECT f.fir_id, f.crime_type, f.date_filed, f.location, f.status,
               c.name AS criminal_name, p.name AS officer_name
        FROM fir f
        JOIN criminal c       ON f.criminal_id=c.criminal_id
        JOIN police_officer p ON f.officer_id=p.officer_id
        WHERE f.status IN ('Open','Under Investigation')
        ORDER BY f.date_filed
    """)
    # Repeat offenders
    repeat_offenders = query_db("""
        SELECT c.criminal_id, c.name, c.age, c.gender, c.previous_cases,
               COUNT(f.fir_id) AS total_firs
        FROM criminal c
        LEFT JOIN fir f ON c.criminal_id=f.criminal_id
        WHERE c.previous_cases > 2
        GROUP BY c.criminal_id ORDER BY c.previous_cases DESC
    """)
    # FIRs per officer
    firs_per_officer = query_db("""
        SELECT p.officer_id, p.name, p.rank, p.station, COUNT(f.fir_id) AS total_firs,
               SUM(CASE WHEN f.status='Open' THEN 1 ELSE 0 END) AS open_firs
        FROM police_officer p
        LEFT JOIN fir f ON p.officer_id=f.officer_id
        GROUP BY p.officer_id ORDER BY total_firs DESC
    """)
    # Crime type distribution
    crime_dist = query_db("""
        SELECT crime_type, COUNT(*) AS total,
               SUM(CASE WHEN status='Open' THEN 1 ELSE 0 END) AS open_count,
               SUM(CASE WHEN status='Closed' THEN 1 ELSE 0 END) AS closed_count
        FROM fir GROUP BY crime_type ORDER BY total DESC
    """)
    # Recent audit log
    audit = query_db(
        "SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT 20"
    )
    return render_template('reports/index.html',
                           open_cases=open_cases,
                           repeat_offenders=repeat_offenders,
                           firs_per_officer=firs_per_officer,
                           crime_dist=crime_dist,
                           audit=audit)


# ---------------------------------------------------------------------------
# API endpoints (JSON) — for chart data
# ---------------------------------------------------------------------------
@app.route('/api/crime-stats')
@login_required
def api_crime_stats():
    rows = query_db(
        "SELECT crime_type, COUNT(*) AS total FROM fir GROUP BY crime_type ORDER BY total DESC"
    )
    return jsonify({'labels': [r['crime_type'] for r in rows],
                    'data':   [r['total'] for r in rows]})


@app.route('/api/status-stats')
@login_required
def api_status_stats():
    rows = query_db(
        "SELECT status, COUNT(*) AS total FROM fir GROUP BY status"
    )
    return jsonify({'labels': [r['status'] for r in rows],
                    'data':   [r['total'] for r in rows]})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
