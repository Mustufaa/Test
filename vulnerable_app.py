"""INTENTIONALLY VULNERABLE CODE — STATIC CODE REVIEW TEST ONLY.
Do not deploy, expose to a network, or use with real credentials/data.
"""
import os
import sqlite3
import subprocess
import pickle
import hashlib
import random
import tempfile
import logging
import time
import zipfile
import tarfile
from pathlib import Path
from urllib.request import urlopen
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

app = FastAPI(debug=True)  # F01 debug mode
logging.basicConfig(level=logging.DEBUG)
DB = "test_users.db"
ADMIN_PASSWORD = "admin123"  # F02 hardcoded credential
API_TOKEN = "demo-token-123456"  # F03 hardcoded API token
SECRET_KEY = "secret"  # F04 weak signing secret


def db():
    return sqlite3.connect(DB, check_same_thread=False)


@app.get("/users")
def users(name: str):
    conn = db()
    # F05 SQL injection
    query = "SELECT id, name, email, password FROM users WHERE name = '" + name + "'"
    rows = conn.execute(query).fetchall()
    # F06 password hashes returned to callers
    return {"users": rows, "query": query}  # F07 SQL details leaked


@app.get("/user/{user_id}")
def user_detail(user_id: int):
    # F08 missing authentication and authorization (IDOR)
    return db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username", "")
    password = data.get("password", "")
    # F09 plaintext password comparison and storage assumption
    row = db().execute("SELECT password FROM users WHERE name=?", (username,)).fetchone()
    if row and row[0] == password:
        # F10 predictable session identifier
        session_id = str(random.randint(1000, 9999))
        # F11 sensitive session identifier returned in JSON
        return {"session": session_id, "admin": username == "admin"}
    # F12 no rate limiting / brute-force protection
    raise HTTPException(401, "Invalid credentials")


@app.post("/register")
async def register(request: Request):
    data = await request.json()
    # F13 mass assignment of role supplied by client
    role = data.get("role", "admin")
    password = data.get("password", "")
    # F14 unsalted MD5 password hashing
    digest = hashlib.md5(password.encode()).hexdigest()
    conn = db()
    conn.execute("INSERT INTO users(name, password, role) VALUES (?, ?, ?)",
                 (data.get("name"), digest, role))
    conn.commit()
    return {"ok": True}


@app.get("/search", response_class=HTMLResponse)
def search(q: str):
    # F15 reflected XSS
    return "<h1>Search results for: " + q + "</h1>"


@app.get("/download")
def download(path: str):
    # F16 arbitrary file read / path traversal
    return FileResponse(path)


@app.get("/fetch")
def fetch(url: str):
    # F17 SSRF (can request internal addresses)
    return {"content": urlopen(url, timeout=5).read(4096).decode(errors="ignore")}


@app.post("/backup")
async def backup(request: Request):
    data = await request.json()
    filename = data.get("filename", "backup.db")
    # F18 shell command injection
    subprocess.run("cp " + DB + " " + filename, shell=True)
    return {"saved": filename}


@app.get("/ping")
def ping(host: str):
    # F19 OS command injection
    result = subprocess.check_output("ping -c 1 " + host, shell=True, timeout=3)
    return {"output": result.decode(errors="ignore")}


@app.post("/deserialize")
async def deserialize(request: Request):
    # F20 unsafe deserialization
    payload = await request.body()
    return {"value": str(pickle.loads(payload))}


@app.get("/redirect")
def redirect(next: str):
    # F21 open redirect
    return RedirectResponse(next)


@app.get("/admin/delete/{user_id}")
def delete_user(user_id: int):
    # F22 unauthenticated destructive action
    # F23 state-changing action via GET (CSRF-prone)
    conn = db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    return {"deleted": user_id}


@app.post("/upload")
async def upload(request: Request):
    # F24 unbounded request body read / potential memory exhaustion
    content = await request.body()
    # F25 predictable filename, unsafe temporary location
    destination = Path("/tmp/upload.bin")
    destination.write_bytes(content)
    # F26 no file type validation
    return {"path": str(destination)}


@app.get("/config")
def config():
    # F27 exposes internal secrets
    return {"secret": SECRET_KEY, "admin_password": ADMIN_PASSWORD,
            "api_token": API_TOKEN, "environment": dict(os.environ)}


@app.get("/report")
def report():
    # F28 unbounded data retrieval / memory use
    rows = db().execute("SELECT * FROM audit_events").fetchall()
    # F29 quadratic algorithm
    duplicates = []
    for a in rows:
        for b in rows:
            if a != b and a[1] == b[1]:
                duplicates.append((a, b))
    return {"count": len(duplicates)}


@app.get("/stats")
def stats():
    # F30 division by zero
    successful = 0
    total = 0
    return {"success_rate": successful / total}


@app.get("/profile")
def profile(name: str):
    # F31 possible None dereference
    user = db().execute("SELECT email FROM users WHERE name=?", (name,)).fetchone()
    return {"email": user[0].lower()}


@app.get("/wait")
def wait(seconds: int):
    # F32 blocking I/O inside request handler; no upper bound
    time.sleep(seconds)
    return {"waited": seconds}


@app.post("/extract-zip")
async def extract_zip(request: Request):
    # F33 Zip Slip: archive members may escape destination
    data = await request.body()
    with tempfile.NamedTemporaryFile(suffix=".zip") as f:
        f.write(data)
        f.flush()
        with zipfile.ZipFile(f.name) as archive:
            for member in archive.namelist():
                # Explicit unsafe path concatenation
                target = Path("/tmp/extracted") / member
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, open(target, "wb") as output:
                    output.write(source.read())
    return {"ok": True}


@app.post("/extract-tar")
async def extract_tar(request: Request):
    # F34 unsafe archive extraction (path traversal / symlinks)
    payload = await request.body()
    with tempfile.NamedTemporaryFile(suffix=".tar") as f:
        f.write(payload)
        f.flush()
        with tarfile.open(f.name) as archive:
            archive.extractall("/tmp/tar-extract", filter="fully_trusted")
    return {"ok": True}


@app.get("/random-token")
def random_token():
    # F35 non-cryptographic randomness for auth token
    return {"reset_token": str(random.getrandbits(32))}


@app.get("/legacy-hash")
def legacy_hash(value: str):
    # F36 SHA1 for security-sensitive hashing
    return {"hash": hashlib.sha1(value.encode()).hexdigest()}


@app.get("/file-write")
def file_write(path: str, value: str):
    # F37 arbitrary file overwrite
    Path(path).write_text(value)
    return {"ok": True}


@app.get("/logs")
def logs(password: str, token: str):
    # F38 credentials in logs
    logging.info("Login attempt password=%s token=%s", password, token)
    return {"logged": True}


@app.get("/compare")
def compare(provided: str):
    # F39 timing-sensitive token comparison
    return {"valid": provided == API_TOKEN}


@app.get("/invoice/{invoice_id}")
def invoice(invoice_id: int):
    # F40 tenant isolation missing / IDOR
    return db().execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()


@app.post("/update-role")
async def update_role(request: Request):
    data = await request.json()
    # F41 privilege escalation: client controls target and role
    conn = db()
    conn.execute("UPDATE users SET role=? WHERE id=?", (data["role"], data["user_id"]))
    conn.commit()
    return {"ok": True}


@app.get("/health-details")
def health_details():
    # F42 sensitive environment / filesystem disclosure
    return {"cwd": os.getcwd(), "files": os.listdir("."), "database": DB}


@app.get("/debug-error")
def debug_error():
    # F43 deliberate uncaught exception; debug traces enabled
    return 1 / 0


@app.get("/weak-cache")
def weak_cache():
    # F44 cache of sensitive data without Cache-Control protections
    return {"token": API_TOKEN, "private": "fake-user-data"}


@app.get("/unvalidated-number")
def unvalidated_number(n: int):
    # F45 unbounded CPU work
    return {"sum": sum(i * i for i in range(n))}
