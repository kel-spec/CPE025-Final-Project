import bcrypt
from modules.db import get_conn, init_db

def hash_pw(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_pw(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def create_user(username: str, password: str, role: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required."
    if role not in ("user", "admin"):
        return False, "Invalid role."

    init_db()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
            (username.strip().lower(), hash_pw(password), role),
        )
        conn.commit()
        return True, "Account created."
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg:
            return False, "Username already exists."
        return False, "Failed to create account."

def authenticate(username: str, password: str) -> tuple[bool, dict | None]:
    init_db()
    conn = get_conn()
    cur = conn.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username=?",
        (username.strip().lower(),),
    )
    row = cur.fetchone()
    if not row:
        return False, None
    user_id, uname, pw_hash, role = row
    if not verify_pw(password, pw_hash):
        return False, None
    return True, {"id": user_id, "username": uname, "role": role}

def ensure_default_admin():
    """
    Optional: seeds one admin if none exist.
    Username: admin
    Password: admin123
    """
    init_db()
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    (n_admin,) = cur.fetchone()
    if n_admin == 0:
        create_user("admin", "admin123", "admin")
