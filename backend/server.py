"""
Pure Work AI - Backend Server
FastAPI + SQLite - Working demo with real data persistence
"""

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Pure Work AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).parent / "purework.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
PUBLIC_PATH = Path(__file__).parent.parent / "public"
TOKENS = {}  # token -> user_id mapping


# -- Database --

@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
        # Check if seed data exists
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            seed_data(conn)


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_data(conn):
    """Seed demo data."""
    users = [
        ("admin@demo.com", "Sarah Mitchell", hash_pw("password123"), "admin", "Human Resources", "HR Director", "Toronto, ON", "(416) 555-0101", "John Mitchell / (416) 555-0102", "2022-03-15"),
        ("manager@demo.com", "James Rodriguez", hash_pw("password123"), "manager", "Sales", "Sales Manager", "Toronto, ON", "(416) 555-0103", "Maria Rodriguez / (416) 555-0104", "2021-06-01"),
        ("employee@demo.com", "Alex Chen", hash_pw("password123"), "employee", "Engineering", "Software Engineer", "Toronto, ON", "(416) 555-0201", "Lin Chen / (416) 555-0202", "2023-01-10"),
        ("lisa@demo.com", "Lisa Thompson", hash_pw("password123"), "employee", "Manufacturing", "Manufacturing Lead", "Hamilton, ON", "(905) 555-0301", "Dan Thompson / (905) 555-0302", "2022-09-01"),
        ("marcus@demo.com", "Marcus Williams", hash_pw("password123"), "employee", "Operations", "Operations Coordinator", "Brampton, ON", "(905) 555-0401", "Tanya Williams / (905) 555-0402", "2024-02-12"),
    ]
    for u in users:
        conn.execute(
            "INSERT INTO users (email, name, password_hash, role, department, title, location, phone, emergency_contact, start_date) VALUES (?,?,?,?,?,?,?,?,?,?)",
            u,
        )

    # PTO balances
    for uid in range(1, 6):
        conn.execute("INSERT INTO pto_balances (user_id, leave_type, total_days, used_days, pending_days) VALUES (?, 'vacation', 15, ?, ?)", (uid, uid * 1.5, 1 if uid < 3 else 0))
        conn.execute("INSERT INTO pto_balances (user_id, leave_type, total_days, used_days, pending_days) VALUES (?, 'sick', 5, ?, 0)", (uid, 1 if uid == 2 else 0))
        conn.execute("INSERT INTO pto_balances (user_id, leave_type, total_days, used_days, pending_days) VALUES (?, 'personal', 3, ?, 0)", (uid, 1 if uid == 1 else 0))

    # Policies
    policies = [
        ("Workplace Harassment Policy (Ontario)", "Ontario", "Compliance"),
        ("Health & Safety Policy (Ontario)", "Ontario", "Safety"),
        ("AI Use Policy", "Universal", "Technology"),
        ("Progressive Discipline Policy (Ontario)", "Ontario", "HR"),
        ("Remote Work Policy", "Universal", "HR"),
        ("Confidentiality & IP Agreement", "Universal", "Legal"),
        ("Drug & Alcohol Policy", "Universal", "Safety"),
        ("Social Media Policy", "Universal", "Communications"),
        ("Travel & Expense Policy", "Universal", "Finance"),
        ("Fall Protection (Construction)", "Construction", "Safety"),
        ("BCEA Policy (South Africa)", "South Africa", "Employment"),
        ("LRA Policy (South Africa)", "South Africa", "Compliance"),
    ]
    for p in policies:
        conn.execute("INSERT INTO policies (name, jurisdiction, category) VALUES (?,?,?)", p)

    # Some acknowledgments for Sarah (admin)
    for pid in [1, 2, 3, 4, 5, 6, 7]:
        conn.execute("INSERT INTO policy_acknowledgments (user_id, policy_id) VALUES (1, ?)", (pid,))

    # PTO requests
    pto_requests = [
        (3, "vacation", "2026-07-21", "2026-07-25", 5, "Family trip", "pending"),
        (4, "sick", "2026-07-08", "2026-07-08", 1, "", "approved"),
        (5, "vacation", "2026-08-11", "2026-08-15", 5, "Summer vacation", "approved"),
        (2, "personal", "2026-07-14", "2026-07-14", 1, "Appointment", "pending"),
    ]
    for r in pto_requests:
        conn.execute("INSERT INTO pto_requests (user_id, leave_type, start_date, end_date, days, reason, status) VALUES (?,?,?,?,?,?,?)", r)

    # Reviews
    reviews = [
        (1, "Q3 2026 Mid-Year", 1, 1, 4.5, "5/5", "completed"),
        (2, "Q3 2026 Mid-Year", 1, 1, 4.2, "4/5", "completed"),
        (3, "Q3 2026 Mid-Year", 1, 0, None, "3/4", "in-progress"),
        (4, "Q3 2026 Mid-Year", 1, 0, None, "4/4", "in-progress"),
        (5, "Q3 2026 Mid-Year", 0, 0, None, "2/4", "pending"),
    ]
    for r in reviews:
        conn.execute("INSERT INTO reviews (user_id, cycle_name, self_done, manager_done, rating, goals_met, status) VALUES (?,?,?,?,?,?,?)", r)

    # Compliance items
    compliance = [
        ("OSHA 10-Hour Construction Safety", "Safety", "2026-08-01", 8, 6, "in-progress"),
        ("Anti-Harassment Training (Title VII)", "Compliance", "2026-07-15", 8, 8, "done"),
        ("HazCom / GHS Training", "Safety", "2026-09-01", 4, 3, "in-progress"),
        ("Fall Protection Competent Person", "Construction", "2026-07-30", 2, 2, "done"),
        ("First Aid/CPR/AED Certification", "Safety", "2026-10-01", 8, 4, "in-progress"),
        ("I-9 / E-Verify Compliance", "Compliance", "2026-07-01", 8, 7, "in-progress"),
    ]
    for c in compliance:
        conn.execute("INSERT INTO compliance_items (item, category, due_date, total_required, completed_count, status) VALUES (?,?,?,?,?,?)", c)

    # Onboarding tasks for Marcus (employee 5, status=onboarding)
    conn.execute("UPDATE users SET status='onboarding' WHERE id=5")
    tasks = [
        (5, "Welcome email sent", "Pre-start", "done"),
        (5, "IT equipment ordered", "Pre-start", "done"),
        (5, "Office tour and introductions", "Day 1", "done"),
        (5, "OSHA safety orientation", "Day 1", "in-progress"),
        (5, "HR paperwork (W-4, I-9, direct deposit)", "Day 1-2", "in-progress"),
        (5, "Role-specific training plan review", "Week 1", "pending"),
        (5, "Meet with manager (goals and expectations)", "Week 1", "pending"),
        (5, "System access setup", "Week 1", "pending"),
        (5, "First project shadow assignment", "Week 2", "pending"),
        (5, "30-day check-in scheduled", "Day 5", "pending"),
    ]
    for t in tasks:
        conn.execute("INSERT INTO onboarding_tasks (user_id, task, due_period, status) VALUES (?,?,?,?)", t)

    conn.commit()


# -- Auth --

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    user_id = TOKENS.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return dict(user)


# -- Models --

class LoginRequest(BaseModel):
    email: str
    password: str

class PTORequest(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    days: float
    reason: Optional[str] = ""

class PTOAction(BaseModel):
    status: str  # approved, denied

class PolicyAck(BaseModel):
    policy_id: int

class TaskAction(BaseModel):
    status: str  # in-progress, done

class QuizResult(BaseModel):
    sop_id: str
    score: float
    passed: bool


# -- Routes: Auth --

@app.post("/api/auth/login")
def login(req: LoginRequest):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", (req.email,)).fetchone()
        if not user or user["password_hash"] != hash_pw(req.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = secrets.token_hex(32)
        TOKENS[token] = user["id"]
        return {
            "token": token,
            "user": {
                "id": user["id"], "name": user["name"], "email": user["email"],
                "role": user["role"], "company": user["company"],
            },
        }


# -- Routes: Dashboard --

@app.get("/api/dashboard")
def dashboard(user=Depends(get_current_user)):
    with get_db() as conn:
        assess_count = conn.execute("SELECT COUNT(*) FROM assessment_results WHERE user_id=?", (user["id"],)).fetchone()[0]
        total_policies = conn.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
        acked = conn.execute("SELECT COUNT(*) FROM policy_acknowledgments WHERE user_id=?", (user["id"],)).fetchone()[0]
        onboarding = conn.execute("SELECT COUNT(*) as done FROM onboarding_tasks WHERE user_id=? AND status='done'", (user["id"],)).fetchone()[0]
        onboarding_total = conn.execute("SELECT COUNT(*) FROM onboarding_tasks WHERE user_id=?", (user["id"],)).fetchone()[0]
        ob_pct = round((onboarding / onboarding_total) * 100) if onboarding_total > 0 else 0
        return {
            "assessments_completed": assess_count, "total_assessments": 13,
            "policies_acknowledged": acked, "total_policies": total_policies,
            "onboarding_percent": ob_pct, "content_count": 83,
        }


@app.get("/api/dashboard/activity")
def dashboard_activity(user=Depends(get_current_user)):
    return {"activities": []}


# -- Routes: PTO --

@app.get("/api/pto/balances")
def get_pto_balances(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM pto_balances WHERE user_id=?", (user["id"],)).fetchall()
        return [dict(r) for r in rows]


@app.get("/api/pto/requests")
def get_pto_requests(user=Depends(get_current_user)):
    with get_db() as conn:
        if user["role"] in ("admin", "manager"):
            rows = conn.execute("""
                SELECT r.*, u.name as employee_name FROM pto_requests r
                JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT r.*, u.name as employee_name FROM pto_requests r
                JOIN users u ON r.user_id = u.id WHERE r.user_id=? ORDER BY r.created_at DESC
            """, (user["id"],)).fetchall()
        return [dict(r) for r in rows]


@app.post("/api/pto/requests")
def create_pto_request(req: PTORequest, user=Depends(get_current_user)):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO pto_requests (user_id, leave_type, start_date, end_date, days, reason) VALUES (?,?,?,?,?,?)",
            (user["id"], req.leave_type, req.start_date, req.end_date, req.days, req.reason),
        )
        # Update pending balance
        conn.execute(
            "UPDATE pto_balances SET pending_days = pending_days + ? WHERE user_id=? AND leave_type=?",
            (req.days, user["id"], req.leave_type),
        )
        conn.commit()
        return {"ok": True, "message": "Request submitted"}


@app.put("/api/pto/requests/{request_id}")
def action_pto_request(request_id: int, action: PTOAction, user=Depends(get_current_user)):
    if user["role"] not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Only managers can approve/deny")
    with get_db() as conn:
        req = conn.execute("SELECT * FROM pto_requests WHERE id=?", (request_id,)).fetchone()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        conn.execute(
            "UPDATE pto_requests SET status=?, reviewer_id=?, reviewed_at=? WHERE id=?",
            (action.status, user["id"], datetime.utcnow().isoformat(), request_id),
        )
        # Update balances
        if action.status == "approved":
            conn.execute(
                "UPDATE pto_balances SET used_days = used_days + ?, pending_days = pending_days - ? WHERE user_id=? AND leave_type=?",
                (req["days"], req["days"], req["user_id"], req["leave_type"]),
            )
        elif action.status == "denied":
            conn.execute(
                "UPDATE pto_balances SET pending_days = pending_days - ? WHERE user_id=? AND leave_type=?",
                (req["days"], req["user_id"], req["leave_type"]),
            )
        conn.commit()
        return {"ok": True, "message": f"Request {action.status}"}


# -- Routes: Policies --

@app.get("/api/policies")
def get_policies(user=Depends(get_current_user)):
    with get_db() as conn:
        policies = conn.execute("SELECT * FROM policies").fetchall()
        acks = conn.execute("SELECT policy_id FROM policy_acknowledgments WHERE user_id=?", (user["id"],)).fetchall()
        acked_ids = set(r["policy_id"] for r in acks)
        return [
            {**dict(p), "status": "acknowledged" if p["id"] in acked_ids else "pending"}
            for p in policies
        ]


@app.post("/api/policies/acknowledge")
def acknowledge_policy(req: PolicyAck, user=Depends(get_current_user)):
    with get_db() as conn:
        try:
            conn.execute("INSERT INTO policy_acknowledgments (user_id, policy_id) VALUES (?,?)", (user["id"], req.policy_id))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already acknowledged
        return {"ok": True}


# -- Routes: Onboarding --

@app.get("/api/onboarding/tasks")
def get_onboarding_tasks(user=Depends(get_current_user)):
    with get_db() as conn:
        if user["role"] in ("admin", "manager"):
            rows = conn.execute("""
                SELECT t.*, u.name as employee_name FROM onboarding_tasks t
                JOIN users u ON t.user_id = u.id ORDER BY t.id
            """).fetchall()
        else:
            rows = conn.execute("SELECT * FROM onboarding_tasks WHERE user_id=? ORDER BY id", (user["id"],)).fetchall()
        return [dict(r) for r in rows]


@app.put("/api/onboarding/tasks/{task_id}")
def update_onboarding_task(task_id: int, action: TaskAction, user=Depends(get_current_user)):
    with get_db() as conn:
        completed_at = datetime.utcnow().isoformat() if action.status == "done" else None
        conn.execute(
            "UPDATE onboarding_tasks SET status=?, completed_at=? WHERE id=?",
            (action.status, completed_at, task_id),
        )
        conn.commit()
        return {"ok": True}


# -- Routes: Reviews --

@app.get("/api/reviews")
def get_reviews(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT r.*, u.name, u.title FROM reviews r
            JOIN users u ON r.user_id = u.id ORDER BY r.id
        """).fetchall()
        return [dict(r) for r in rows]


# -- Routes: Compliance --

@app.get("/api/compliance")
def get_compliance(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM compliance_items ORDER BY due_date").fetchall()
        return [dict(r) for r in rows]


# -- Routes: Training --

@app.post("/api/training/complete")
def complete_training(req: QuizResult, user=Depends(get_current_user)):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO training_completions (user_id, sop_id, output_type, score, passed) VALUES (?,?,?,?,?)",
            (user["id"], req.sop_id, "quiz", req.score, 1 if req.passed else 0),
        )
        conn.commit()
        return {"ok": True, "message": "Training completion recorded"}


@app.get("/api/training/history")
def get_training_history(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM training_completions WHERE user_id=? ORDER BY completed_at DESC",
            (user["id"],),
        ).fetchall()
        return [dict(r) for r in rows]


# -- Routes: Users (admin) --

@app.get("/api/users")
def get_users(user=Depends(get_current_user)):
    if user["role"] not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Admin only")
    with get_db() as conn:
        rows = conn.execute("SELECT id, email, name, role, department, title, location, status, start_date FROM users").fetchall()
        return [dict(r) for r in rows]


# -- Static files --

app.mount("/", StaticFiles(directory=str(PUBLIC_PATH), html=True), name="static")


# -- Startup --

@app.on_event("startup")
def startup():
    init_db()
    print(f"Pure Work AI backend running. DB: {DB_PATH}")
    print(f"Serving frontend from: {PUBLIC_PATH}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
