import bcrypt
from modules.db import get_conn, init_db

def hash_pw(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_pw(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def create_user(
    *,
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    password: str,
    vehicle_type: str,
    privacy_accepted: bool
) -> tuple[bool, str]:
    # Basic validation
    if not all([first_name, last_name, username, email, password, vehicle_type]):
        return False, "All fields are required."
    if not privacy_accepted:
        return False, "You must confirm you have read the privacy disclosure."

    uname = username.strip().lower()
    mail = email.strip().lower()

    init_db()
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO users(username, password_hash, role, first_name, last_name, email, vehicle_type, privacy_accepted)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                uname,
                hash_pw(password),
                "user",
                first_name.strip(),
                last_name.strip(),
                mail,
                vehicle_type.strip(),
                1,
            ),
        )
        conn.commit()
        return True, "Account created."
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg and "username" in msg:
            return False, "Username already exists."
        return False, "Failed to create account."

def authenticate(username: str, password: str) -> tuple[bool, dict | None]:
    init_db()
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT id, username, password_hash, role, first_name, last_name, email, vehicle_type
        FROM users
        WHERE username=?
        """,
        (username.strip().lower(),),
    )
    row = cur.fetchone()
    if not row:
        return False, None

    user_id, uname, pw_hash, role, first_name, last_name, email, vehicle_type = row
    if not verify_pw(password, pw_hash):
        return False, None

    return True, {
        "id": user_id,
        "username": uname,
        "role": role,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "vehicle_type": vehicle_type,
    }

def ensure_default_admin():
    """
    Seeds one admin if none exist.
    Username: admin
    Password: admin123
    """
    init_db()
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    (n_admin,) = cur.fetchone()

    if n_admin == 0:
        # Admin profile fields can be blank in prototype
        conn.execute(
            """
            INSERT INTO users(username, password_hash, role, privacy_accepted)
            VALUES(?,?,?,?)
            """,
            ("admin", hash_pw("admin123"), "admin", 1),
        )
        conn.commit()
