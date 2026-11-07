# 🚀 Quest it here

> **An Internal Digital Transformation (DX) & Automation Platform**  
> Bridging the gap between frontline operational challenges and scalable technical solutions.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap)](https://getbootstrap.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Overview

**Quest it here** is a zero-cost, local-first web platform designed to streamline how organizations identify, govern, and execute automation initiatives. It transforms ad-hoc scripting into a structured, gamified, and secure workflow.

Instead of scattered scripts on local machines, this platform creates a centralized **Governance & Execution Hub** where:

1.  **Employees (Requesters)** submit automation and AI integration requests with estimated business impact.
2.  **Administrators (Planning Group)** review, prioritize, and approve requests to ensure strategic alignment.
3.  **Engineers / DX Generalists (Solvers)** claim approved "Quests," write sandboxed Python automation scripts in a professional IDE-like editor, and earn **Impact Points** based on verified time savings.

---

## ✨ Key Features

| Category | Features |
| :--- | :--- |
| **🏛️ Role-Based Access** | **User Portal:** Submit requests, track status, solve quests, view personal stats.<br>**Admin Hub:** Review queue, one-click Approve/Reject, feedback loop, global metrics.<br>**Quest Board:** Public board of approved tasks with difficulty, impact, and claim status. |
| **💻 Pro Developer Experience** | **CodeMirror Editor:** Line numbers, Dracula theme, Python syntax highlighting, auto-indentation.<br>**Syntax Guard:** Server-side `ast.parse()` validation blocks execution on syntax errors with exact line numbers.<br>**Secure Sandbox:** Execution via `subprocess` + `python -I` (isolated mode), 30s hard timeout, temp directory cleanup. |
| **📊 Gamification & Analytics** | **Impact Scoring:** `Points = (Baseline Minutes - Runtime Minutes) + (10 × Difficulty)`.<br>**Hall of Fame:** Real-time leaderboard ranking contributors by total impact.<br>**Visual Dashboard:** Personal stats cards for "Active Quests" and "Total Impact". |
| **🛡️ Enterprise Governance** | **Approval Workflow:** Requests start as `PENDING` → Admin Review → `APPROVED` (Public) / `REJECTED`.<br>**Claim Locking:** Prevents duplicate work; only one solver per quest.<br> **Audit Trail:** Full history of scripts, outputs, runtimes, and points stored in SQLite. |
| **💰 Zero Infrastructure Cost** | Runs entirely on local machine. No Docker, Kubernetes, Cloud SQL, or paid SaaS required. Single file `dx_quest.py` + SQLite. |

---

## 🛠️ Technology Stack

*   **Backend:** Python 3.11+, Flask 3.0
*   **Database:** SQLite 3 (via standard library `sqlite3`)
*   **Security/Sandboxing:** `subprocess`, `tempfile`, `ast` (Abstract Syntax Tree)
*   **Frontend:** HTML5, Bootstrap 5.3, Bootstrap Icons, Jinja2 Templates
*   **Editor:** CodeMirror 5 (Dracula Theme, Python Mode)

---

## 🚀 Getting Started

### Prerequisites
*   Python **3.11+** installed.
*   Git (for cloning).

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/Quest-it-here.git
cd Quest-it-here

# 2. Create & activate virtual environment (Recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
# OR simply: pip install Flask
```

### Running the Application

```bash
python dx_quest.py
```

Open your browser and navigate to:  
👉 **`http://127.0.0.1:5001/`**

---

## 🗂️ Project Structure

```text
Quest_it_here/
│
├── dx_quest.py         # Main Flask Application (Routes, Logic, Sandbox, Auth)
├── requirements.txt    # Python Dependencies
├── .gitignore          # Ignores __pycache__, .venv, *.db, IDE folders
├── README.md           # This file
│
├── dx_quest.db         # SQLite Database (Auto-generated on first run)
│
└── view_db.py          # (Optional) CLI Utility to inspect DB tables
```

---

## 🧭 User Workflow Guide

### 1. Employee: Submit a Request
*   Go to **User Portal** → **+ New Automation Request**.
*   Fill in Title, Description, Estimated Manual Minutes, and Difficulty (1-5).
*   Status becomes **`PENDING`**.

### 2. Admin: Govern & Approve
*   Go to **Admin Hub** (Top Right Navbar).
*   Review pending cards. Add feedback if needed.
*   Click **Approve** → Quest moves to Board. Click **Reject** → Returns to user with feedback.

### 3. Engineer: Claim & Solve
*   Go to **Quest Board** (Sidebar).
*   See **AVAILABLE** cards (Green badge). Click **Claim Quest**.
*   Return to **User Portal** → **My Active Quests** → **Open Editor**.
*   Write Python code in the **CodeMirror Editor**.
*   Click **Verify & Submit**.
    *   ✅ **Syntax OK** → Runs in sandbox → Shows Output + **Points Awarded**.
    *   ❌ **Syntax Error** → Red Alert with **Line Number** → Code **NOT executed**.

### 4. Track Impact
*   **Hall of Fame** (Navbar) → Real-time Leaderboard.
*   **User Portal** → Personal Stats Cards (Total Points, Quests Done).

---

## 🔒 Security & Sandboxing Details

The platform treats all user-submitted code as **untrusted**.

1.  **Syntax Validation (`ast`):** Before execution, `ast.parse(code)` validates the Abstract Syntax Tree. Invalid syntax raises `SyntaxError` immediately; the subprocess is **never spawned**.
2.  **Process Isolation (`subprocess`):** Code runs in a separate OS process, not the main Flask thread. A crash or infinite loop in user code **cannot** freeze the web server.
3.  **Python Isolated Mode (`-I`):** The interpreter starts with `-I` flag: ignores `PYTHONPATH`, ignores `site` module, prevents `import` of user-site packages. Reduces attack surface.
4.  **Filesystem Jail (`tempfile`):** A unique temporary directory is created for each run. The script is written there, executed there, and the directory is **deleted immediately** after.
5.  **Resource Limits:** Hard **30-second timeout** (`subprocess.timeout`). Prevents resource exhaustion (fork bombs, infinite loops).

---

## 📦 Requirements

Create a `requirements.txt` file (or install manually):

```text
Flask>=3.0.0
```

> **Note:** `sqlite3`, `subprocess`, `tempfile`, `ast`, `os`, `time` are Python Standard Library modules. No extra installs needed for core logic.

---

## 🤝 Contributing

This project was built as a demonstration of **DX Engineering** capabilities. Contributions for UI polish, additional sandboxes (Node.js, Bash), or notification systems are welcome!

1.  Fork the repo.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit changes (`git commit -m 'Add amazing feature'`).
4.  Push to branch (`git push origin feature/amazing-feature`).
4.  Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👨‍💻 Author & Acknowledgments

**Built by:** [Your Name]  
**Role:** Project Lead & Architect (Team of 4)  
**Context:** Designed to demonstrate end-to-end Digital Transformation workflow: **Ideation → Governance → Secure Execution → Impact Measurement**.

*Inspired by real-world challenges in manufacturing, logistics, and service industries where frontline staff need a voice in automation.*