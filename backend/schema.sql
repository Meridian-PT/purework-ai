-- Pure Work AI - Production Schema
-- SQLite

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',  -- admin, manager, employee
    company TEXT DEFAULT 'Pure Technology',
    department TEXT,
    title TEXT,
    location TEXT,
    phone TEXT,
    emergency_contact TEXT,
    start_date TEXT,
    status TEXT DEFAULT 'active',  -- active, onboarding, inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pto_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    leave_type TEXT NOT NULL,  -- vacation, sick, personal, bereavement, fmla
    total_days REAL NOT NULL DEFAULT 0,
    used_days REAL NOT NULL DEFAULT 0,
    pending_days REAL NOT NULL DEFAULT 0,
    year INTEGER NOT NULL DEFAULT 2026,
    UNIQUE(user_id, leave_type, year)
);

CREATE TABLE IF NOT EXISTS pto_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    leave_type TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    days REAL NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, approved, denied
    reviewer_id INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    jurisdiction TEXT,
    category TEXT,
    version TEXT DEFAULT '1.0',
    content_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_acknowledgments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    policy_id INTEGER NOT NULL REFERENCES policies(id),
    acknowledged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, policy_id)
);

CREATE TABLE IF NOT EXISTS onboarding_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    task TEXT NOT NULL,
    due_period TEXT,  -- Pre-start, Day 1, Week 1, etc.
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in-progress, done
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    cycle_name TEXT NOT NULL,
    self_done INTEGER DEFAULT 0,
    manager_done INTEGER DEFAULT 0,
    rating REAL,
    goals_met TEXT,
    status TEXT DEFAULT 'pending',  -- pending, in-progress, completed
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    category TEXT,
    due_date TEXT,
    total_required INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',  -- pending, in-progress, done
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    sop_id TEXT NOT NULL,
    output_type TEXT NOT NULL,  -- presentation, quiz, audio, flashcards
    score REAL,
    passed INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assessment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    assessment_type TEXT NOT NULL,
    scores_json TEXT,
    overall_score REAL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
