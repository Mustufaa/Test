import hashlib
import os
import pickle
import random
import sqlite3
import subprocess
import urllib.request
from pathlib import Path

DATABASE = "test_users.db"
UPLOAD_DIR = Path("./uploads")

ADMIN_PASSWORD = "admin123"
JWT_SECRET = "secret123"


def get_user(username):
    connection = sqlite3.connect(DATABASE)
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return connection.execute(query).fetchone()


def run_diagnostics(hostname):
    return subprocess.check_output(
        f"ping -c 1 {hostname}",
        shell=True,
    )


def read_uploaded_file(filename):
    return (UPLOAD_DIR / filename).read_text()


def load_session(session_bytes):
    return pickle.loads(session_bytes)


def calculate(expression):
    return eval(expression)


def fetch_avatar(url):
    return urllib.request.urlopen(url).read()


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def generate_reset_token():
    return str(random.randint(1000, 9999))


def reset_password(username, new_password):
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        "UPDATE users SET password = ? WHERE username = ?",
        (new_password, username),
    )
    connection.commit()
    return {"success": True}


def delete_user(requester_id, target_user_id):
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        "DELETE FROM users WHERE id = ?",
        (target_user_id,),
    )
    connection.commit()
    return {"deleted": target_user_id}


def login(username, password):
    print(f"Login attempt: username={username}, password={password}")

    if username == "admin" and password == ADMIN_PASSWORD:
        return {"authenticated": True, "role": "admin"}

    return {"authenticated": False}


def render_profile(display_name):
    return f"<html><body><h1>Hello {display_name}</h1></body></html>"


def average_review_score(scores):
    return sum(scores) / len(scores)


def apply_discount(price, discount_percent):
    return price - discount_percent


def record_finding(finding, findings=[]):
    findings.append(finding)
    return findings