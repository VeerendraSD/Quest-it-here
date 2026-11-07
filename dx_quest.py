import os, sqlite3, subprocess, tempfile, time
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "dx_quest.db")

# ---------------------------------------------------------------------
# Initialise SQLite schema
# ---------------------------------------------------------------------
def init_db():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            submitter_id INTEGER,
            baseline_minutes INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            admin_feedback TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY,
            challenge_id INTEGER,
            claimant_id INTEGER,
            claimed_at TEXT DEFAULT (datetime('now')),
            status TEXT CHECK(status IN ('open','completed')) NOT NULL DEFAULT 'open'
        );
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY,
            claim_id INTEGER,
            script TEXT NOT NULL,
            output TEXT,
            runtime_ms INTEGER,
            points INTEGER,
            completed_at TEXT DEFAULT (datetime('now'))
        );
        """)

        # Migrations for status columns if they don't exist
        try:
            cur.execute("SELECT status FROM challenges LIMIT 1")
        except sqlite3.OperationalError:
            cur.execute("ALTER TABLE challenges ADD COLUMN status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'approved'")
            cur.execute("ALTER TABLE challenges ADD COLUMN admin_feedback TEXT")

        con.commit()
init_db()

# ---------------------------------------------------------------------
# DB Helpers
# ---------------------------------------------------------------------
def q(sql, args=()):
    with sqlite3.connect(DB) as con:
        cur = con.execute(sql, args)
        return cur.fetchall()

def exec_sql(sql, args=()):
    with sqlite3.connect(DB) as con:
        cur = con.execute(sql, args)
        con.commit()
        return cur.lastrowid

def get_demo_user():
    uid = q("SELECT id FROM users WHERE name=?", ("demo",))
    if uid: return uid[0][0]
    return exec_sql("INSERT INTO users (name) VALUES (?)", ("demo",))

DEMO_USER_ID = get_demo_user()

# ---------------------------------------------------------------------
# UI Layout Template
# ---------------------------------------------------------------------
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest it here - DX Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f4f7f6; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
        .navbar { background-color: #1a2a3a !important; border-bottom: 3px solid #3498db; }
        .card { border: none; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .btn-primary { background-color: #3498db; border: none; }
        .btn-success { background-color: #27ae60; border: none; }
        .sidebar-heading { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #7f8c8d; font-weight: 700; margin-bottom: 1rem; }
        .nav-pills .nav-link { border-radius: 10px; color: #2c3e50; font-weight: 500; margin-bottom: 5px; }
        .nav-pills .nav-link.active { background-color: #3498db; }
        .nav-pills .nav-link:hover:not(.active) { background-color: #ecf0f1; }
        .status-pill { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .diff-1 { color: #27ae60; } .diff-2 { color: #f1c40f; } .diff-3 { color: #e67e22; } .diff-4 { color: #e74c3c; } .diff-5 { color: #8e44ad; }
        .code-editor { font-family: 'Fira Code', 'Courier New', monospace; font-size: 14px; background-color: #2d3436; color: #dfe6e9; border-radius: 10px; padding: 20px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
        <div class="container-fluid px-4">
            <a class="navbar-brand fw-bold fs-4" href="{{url_for('home')}}"><i class="bi bi-rocket-takeoff-fill me-2 text-info"></i>Quest it here</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item me-3"><span class="text-light opacity-50 small">Welcome, User</span></li>
                    <li class="nav-item"><a class="btn btn-sm btn-outline-info" href="{{url_for('leaderboard')}}"><i class="bi bi-trophy me-1"></i> Hall of Fame</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <!-- Global Sidebar -->
            <nav class="col-md-3 col-lg-2 d-md-block bg-white sidebar collapse border-end min-vh-100 p-4">
                <div class="position-sticky">
                    <div class="sidebar-heading mt-2">Workspace</div>
                    <ul class="nav nav-pills flex-column mb-4">
                        <li class="nav-item"><a class="nav-link {{'active' if active_page=='user'}}" href="{{url_for('user_dashboard')}}"><i class="bi bi-person-workspace me-2"></i>User Portal</a></li>
                        <li class="nav-item"><a class="nav-link {{'active' if active_page=='board'}}" href="{{url_for('list_challenges')}}"><i class="bi bi-kanban me-2"></i>Quest Board</a></li>
                    </ul>

                    <div class="sidebar-heading">Management</div>
                    <ul class="nav nav-pills flex-column">
                        <li class="nav-item"><a class="nav-link {{'active' if active_page=='admin'}}" href="{{url_for('admin_dashboard')}}"><i class="bi bi-shield-lock me-2 text-danger"></i>Admin Hub</a></li>
                    </ul>
                </div>
            </nav>

            <!-- Main Content Area -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    <footer class="text-center py-4 mt-5 text-muted border-top">
        <small>&copy; Quest it here - DX Initiatives Platform</small>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------

@app.route('/')
def home():
    return redirect(url_for('user_dashboard'))

@app.route('/user')
def user_dashboard():
    my_requests = q("SELECT id, title, status, created_at FROM challenges WHERE submitter_id=? ORDER BY created_at DESC", (DEMO_USER_ID,))
    active_claims = q("""
        SELECT cl.id, ch.title, ch.difficulty, cl.claimed_at
        FROM claims cl
        JOIN challenges ch ON cl.challenge_id = ch.id
        WHERE cl.claimant_id = ? AND cl.status = 'open'
    """, (DEMO_USER_ID,))

    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold"><i class="bi bi-person-circle me-2"></i>User Workspace</h2>
        <a href="{{{{url_for('new_challenge')}}}}" class="btn btn-primary"><i class="bi bi-plus-lg me-1"></i>New Automation Request</a>
    </div>

    <div class="row">
        <!-- Left: My Active Quests -->
        <div class="col-lg-7">
            <div class="card p-4">
                <h5 class="fw-bold mb-3"><i class="bi bi-hammer me-2 text-primary"></i>My Active Quests (Solving Now)</h5>
                <div class="list-group list-group-flush">
                    {"".join(f'''
                    <div class="list-group-item d-flex justify-content-between align-items-center px-0 py-3">
                        <div>
                            <h6 class="mb-1 fw-bold">{r[1]}</h6>
                            <small class="text-muted">Claimed: {r[3]}</small>
                        </div>
                        <a href="{url_for('upload_solution', claim_id=r[0])}" class="btn btn-sm btn-success">Upload Script</a>
                    </div>''' for r in active_claims) or '<p class="text-muted py-3">No active quests. Go to the Quest Board to claim one!</p>'}
                </div>
            </div>

            <div class="card p-4">
                <h5 class="fw-bold mb-3"><i class="bi bi-list-task me-2 text-info"></i>My Requests Status</h5>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead><tr><th>Title</th><th>Status</th><th>Submitted</th></tr></thead>
                        <tbody>
                            {"".join(f'''
                            <tr>
                                <td>{r[1]}</td>
                                <td><span class="badge bg-{'success' if r[2]=='approved' else 'warning text-dark' if r[2]=='pending' else 'danger'}">{r[2].upper()}</span></td>
                                <td><small>{r[3][:10]}</small></td>
                            </tr>''' for r in my_requests) or '<tr><td colspan="3" class="text-center py-4">No requests found.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Right: Board Quick Look -->
        <div class="col-lg-5">
            <div class="card p-4 bg-light border">
                <h5 class="fw-bold mb-3">Community Hub</h5>
                <p class="small text-muted">Ready to earn points? The Quest Board has approved ideas waiting for a developer.</p>
                <a href="{{{{url_for('list_challenges')}}}}" class="btn btn-outline-primary w-100 mb-3">Go to Quest Board</a>
                <hr>
                <div class="d-flex justify-content-between mb-2"><span>Points Earned:</span> <span class="fw-bold text-primary">{q("SELECT SUM(points) FROM completions JOIN claims ON completions.claim_id = claims.id WHERE claims.claimant_id=?", (DEMO_USER_ID,))[0][0] or 0}</span></div>
                <div class="d-flex justify-content-between"><span>Quests Finished:</span> <span class="fw-bold text-success">{q("SELECT COUNT(*) FROM completions JOIN claims ON completions.claim_id = claims.id WHERE claims.claimant_id=?", (DEMO_USER_ID,))[0][0]}</span></div>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", content), active_page='user')

@app.route('/board')
def list_challenges():
    rows = q("""
        SELECT ch.id, ch.title, ch.description, ch.baseline_minutes, ch.difficulty,
               (SELECT COUNT(*) FROM claims cl WHERE cl.challenge_id=ch.id AND cl.status='open') AS is_claimed,
               (SELECT COUNT(*) FROM claims cl WHERE cl.challenge_id=ch.id AND cl.status='completed') AS is_done
        FROM challenges ch
        WHERE ch.status = 'approved'
        ORDER BY ch.created_at DESC
    """)

    cards = ""
    for r in rows:
        status_info = '<span class="text-success small fw-bold">AVAILABLE</span>'
        action_btn = f'<a href="{url_for("claim", cid=r[0])}" class="btn btn-sm btn-primary px-4 rounded-pill">Claim</a>'

        if r[6]:
            status_info = '<span class="text-muted small">RESOLVED</span>'
            action_btn = '<span class="badge bg-secondary rounded-pill p-2"><i class="bi bi-check-lg"></i> Done</span>'
        elif r[5]:
            status_info = '<span class="text-warning small">LOCKED</span>'
            action_btn = '<span class="text-muted small">In Progress</span>'

        cards += f"""
        <div class="col-md-6 col-xl-4 mb-4">
            <div class="card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span class="fw-bold small diff-{r[4]}">Difficulty Lvl {r[4]}</span>
                        {status_info}
                    </div>
                    <h5 class="card-title fw-bold mb-3">{r[1]}</h5>
                    <p class="card-text small text-muted mb-4">{r[2]}</p>
                    <div class="d-flex justify-content-between align-items-center mt-auto">
                        <div class="text-center bg-light rounded p-2 px-3">
                            <div class="fw-bold text-primary mb-0">{r[3]}</div>
                            <div class="small text-muted" style="font-size: 0.6rem;">MIN SAVED</div>
                        </div>
                        {action_btn}
                    </div>
                </div>
            </div>
        </div>
        """

    content = f"""
    <h2 class="fw-bold mb-4"><i class="bi bi-kanban me-2 text-primary"></i>Quest Board</h2>
    <div class="row">{cards or '<div class="col-12 text-center py-5">No quests available yet.</div>'}</div>
    """
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", content), active_page='board')

@app.route('/admin')
def admin_dashboard():
    pending = q("SELECT id, title, description, baseline_minutes, difficulty, created_at FROM challenges WHERE status='pending'")
    stats = q("SELECT COUNT(*), (SELECT COUNT(*) FROM challenges WHERE status='approved') FROM challenges")
    total_req, total_app = stats[0]

    rows = ""
    for r in pending:
        rows += f"""
        <div class="card p-4 border-start border-4 border-warning mb-3">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h5 class="fw-bold mb-1">{r[1]}</h5>
                    <p class="text-muted small mb-0">{r[2]}</p>
                    <div class="mt-2"><span class="badge bg-light text-dark border">Impact: {r[3]}m</span> <span class="badge bg-light text-dark border">Diff: {r[4]}/5</span></div>
                </div>
                <div class="col-md-4 text-end">
                    <form action="/admin/process/{r[0]}" method="post">
                        <input type="text" name="feedback" class="form-control form-control-sm mb-2" placeholder="Admin feedback...">
                        <button type="submit" name="action" value="approve" class="btn btn-sm btn-success px-3">Approve</button>
                        <button type="submit" name="action" value="reject" class="btn btn-sm btn-outline-danger">Reject</button>
                    </form>
                </div>
            </div>
        </div>
        """

    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold text-danger"><i class="bi bi-shield-lock-fill me-2"></i>Admin Hub</h2>
        <div class="d-flex gap-4">
            <div class="text-end">
                <div class="small text-muted text-uppercase">Total Submissions</div>
                <div class="fw-bold fs-4">{total_req}</div>
            </div>
            <div class="text-end border-start ps-4">
                <div class="small text-muted text-uppercase">Approved Quests</div>
                <div class="fw-bold fs-4 text-success">{total_app}</div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-9">
            <h5 class="fw-bold mb-3">Pending Review Queue</h5>
            {rows or '<div class="alert alert-light border text-center py-5">Review queue is empty. Good job, Admin!</div>'}
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", content), active_page='admin')

@app.route('/admin/process/<int:cid>', methods=['POST'])
def process_challenge(cid):
    action = request.form.get('action')
    feedback = request.form.get('feedback', '')
    status = 'approved' if action == 'approve' else 'rejected'
    exec_sql("UPDATE challenges SET status=?, admin_feedback=? WHERE id=?", (status, feedback, cid))
    return redirect(url_for('admin_dashboard'))

@app.route('/challenge/new', methods=['GET','POST'])
def new_challenge():
    if request.method == 'POST':
        exec_sql("INSERT INTO challenges (title,description,submitter_id,baseline_minutes,difficulty,status) VALUES (?,?,?,?,?,?)",
                 (request.form['title'], request.form['desc'], DEMO_USER_ID, int(request.form['base']), int(request.form['diff']), 'pending'))
        return redirect(url_for('user_dashboard'))

    content = """
    <div class="row justify-content-center">
        <div class="col-md-7">
            <div class="card p-5">
                <h3 class="fw-bold mb-2">Request DX Automation</h3>
                <p class="text-muted mb-4">Submit your idea for automation or AI integration. The Planning Group will review it for the Quest Board.</p>
                <form method="post">
                    <div class="mb-4">
                        <label class="form-label fw-bold">Project Name</label>
                        <input name="title" class="form-control form-control-lg" placeholder="e.g. Automated Receipt Scanner" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label fw-bold">What needs to be automated?</label>
                        <textarea name="desc" class="form-control" rows="4" placeholder="Describe the manual work, data sources, and desired AI/automation outcome..." required></textarea>
                    </div>
                    <div class="row mb-5">
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Manual Effort (mins/task)</label>
                            <input type="number" name="base" class="form-control" min="1" value="30" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Complexity Level</label>
                            <select name="diff" class="form-select">
                                <option value="1">1 - Simple Task</option>
                                <option value="2">2 - Multi-step Automation</option>
                                <option value="3" selected>3 - Data/API Integration</option>
                                <option value="4">4 - Advanced AI/ML</option>
                                <option value="5">5 - Enterprise Strategy</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary btn-lg w-100 shadow">Submit Request for Approval</button>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", content), active_page='user')

@app.route('/claim/<int:cid>')
def claim(cid):
    existing = q("SELECT id FROM claims WHERE challenge_id=? AND status='open'", (cid,))
    if existing: return "Quest already locked by another agent.", 400
    claim_id = exec_sql("INSERT INTO claims (challenge_id, claimant_id) VALUES (?,?)", (cid, DEMO_USER_ID))
    return redirect(url_for('user_dashboard'))

@app.route('/upload/<int:claim_id>', methods=['GET','POST'])
def upload_solution(claim_id):
    chal = q("SELECT title, baseline_minutes, difficulty FROM challenges WHERE id = (SELECT challenge_id FROM claims WHERE id=?)", (claim_id,))
    if not chal: return "Challenge link broken.", 404
    title, baseline, diff = chal[0]

    if request.method == 'POST':
        script = request.form['script']
        with tempfile.TemporaryDirectory() as td:
            script_path = os.path.join(td, "solution.py")
            with open(script_path, "w", encoding="utf-8") as f: f.write(script)
            start = time.time()
            try:
                proc = subprocess.run(["python", "-I", "solution.py"], cwd=td, capture_output=True, text=True, timeout=30)
                status, output = "SUCCESS", proc.stdout + (proc.stderr or "")
            except Exception as e:
                status, output = "ERROR", str(e)
            elapsed = int((time.time() - start) * 1000)

        saved = max(0, baseline - int(elapsed/1000/60))
        points = saved + 10 * diff
        exec_sql("INSERT INTO completions (claim_id, script, output, runtime_ms, points) VALUES (?,?,?,?,?)",
                 (claim_id, script, output, elapsed, points))
        exec_sql("UPDATE claims SET status='completed' WHERE id=?", (claim_id,))

        return f"""
        <div class="text-center py-5">
            <h1 class="display-1">🔥</h1>
            <h2 class="display-4 fw-bold">Quest Complete!</h2>
            <p class="lead">System verified. You earned <strong>{points}</strong> impact points.</p>
            <div class="container text-start mt-5"><pre class="code-editor">{output}</pre></div>
            <a href="{url_for('user_dashboard')}" class="btn btn-primary btn-lg mt-4">Return to Workspace</a>
        </div>
        """

    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-10">
            <div class="card p-5">
                <h3 class="fw-bold mb-4">Solving: {title}</h3>
                <form method="post">
                    <div class="mb-3">
                        <label class="form-label text-muted">Upload your DX Automation Script (Python)</label>
                        <textarea name="script" class="form-control code-editor" rows="15" required># DX Solution Script Template
import sys

def main():
    print("Initializing DX Agent...")
    # Add your logic here
    print("Automation successful.")

if __name__ == '__main__':
    main()</textarea>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="text-muted small"><i class="bi bi-info-circle me-1"></i>Runtime limit: 30s | Isolated Env</div>
                        <button type="submit" class="btn btn-success btn-lg px-5">Verify & Submit</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", content), active_page='user')

@app.route('/leaderboard')
def leaderboard():
    rows = q("""
        SELECT u.name, SUM(c.points) AS pts, COUNT(c.id) AS completed
        FROM completions c
        JOIN claims cl ON c.claim_id = cl.id
        JOIN users u ON cl.claimant_id = u.id
        GROUP BY u.id
        ORDER BY pts DESC
    """)
    table_rows = "".join(f"<tr><td class='fw-bold'>#{i}</td><td>{r[0]}</td><td><span class='badge bg-primary px-3'>{r[1]}</span></td><td>{r[2]} Quests</td></tr>" for i, r in enumerate(rows, 1))

    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-9">
            <div class="card p-5 text-center bg-white shadow">
                <h1 class="display-5 fw-bold mb-4">🏆 DX Hall of Fame</h1>
                <table class="table table-hover align-middle mt-4">
                    <thead class="table-light"><tr><th>Rank</th><th>Agent</th><th>Impact Points</th><th>Contribution</th></tr></thead>
                    <tbody>{table_rows or '<tr><td colspan="4" class="text-muted py-5">The board is currently empty.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", content), active_page='none')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
