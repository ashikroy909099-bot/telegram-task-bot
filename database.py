import sqlite3

conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    pending INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0
)
""")

# TASKS
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    reward REAL
)
""")

# REPORTS (Replaces submissions/submissions_v2 for better tracking)
cur.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task_id INTEGER,
    proof TEXT,
    status TEXT DEFAULT 'pending',
    UNIQUE(user_id, task_id)
)
""")

# WITHDRAW
cur.execute("""
CREATE TABLE IF NOT EXISTS withdraw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    address TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()

# -------- FUNCTIONS --------
def add_user(uid):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def update_balance(uid, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def add_task(title, description, reward):
    cur.execute("INSERT INTO tasks (title, description, reward) VALUES (?,?,?)", (title, description, reward))
    conn.commit()

def get_tasks():
    cur.execute("SELECT * FROM tasks")
    return cur.fetchall()

def get_available_tasks(uid):
    cur.execute("""
        SELECT * FROM tasks 
        WHERE id NOT IN (SELECT task_id FROM reports WHERE user_id=?)
    """, (uid,))
    return cur.fetchall()

def get_task(task_id):
    cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    return cur.fetchone()

def add_report(uid, task_id, proof):
    try:
        cur.execute("INSERT INTO reports (user_id, task_id, proof) VALUES (?, ?, ?)", (uid, task_id, proof))
        cur.execute("UPDATE users SET pending = pending + 1 WHERE user_id=?", (uid,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def check_report_exists(uid, task_id):
    cur.execute("SELECT 1 FROM reports WHERE user_id=? AND task_id=?", (uid, task_id))
    return cur.fetchone() is not None

def approve_report(uid, task_id, reward):
    cur.execute("UPDATE reports SET status='approved' WHERE user_id=? AND task_id=?", (uid, task_id))
    cur.execute("""
        UPDATE users
        SET balance = balance + ?, pending = pending - 1, completed = completed + 1
        WHERE user_id=?
    """, (reward, uid))
    conn.commit()

def add_withdraw(uid, amount, address):
    cur.execute("INSERT INTO withdraw (user_id,amount,address) VALUES (?,?,?)",
                (uid, amount, address))
    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, uid))
    conn.commit()

def get_withdraws():
    cur.execute("SELECT * FROM withdraw WHERE status='pending'")
    return cur.fetchall()
def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()