-- ================================================================
-- Pure Work AI - Database Schema (Cloudflare D1 / SQLite)
-- Sprint 1 Foundation - 7 core tables
-- ================================================================

-- Companies table: multi-tenant root
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'starter',
    settings TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_companies_slug ON companies(slug);

-- Users table: authentication and identity
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(email, company_id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company ON users(company_id);

-- Assessment results: stores completed assessment data
CREATE TABLE IF NOT EXISTS assessment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    assessment_type TEXT NOT NULL,
    score_json TEXT NOT NULL DEFAULT '{}',
    total_score REAL,
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_assessments_user ON assessment_results(user_id);
CREATE INDEX idx_assessments_company ON assessment_results(company_id);
CREATE INDEX idx_assessments_type ON assessment_results(assessment_type);

-- Policy acknowledgments: tracks which policies each user has signed
CREATE TABLE IF NOT EXISTS policy_acknowledgments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    policy_name TEXT NOT NULL,
    policy_version TEXT NOT NULL DEFAULT '1.0',
    acknowledged_at TEXT NOT NULL DEFAULT (datetime('now')),
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(user_id, policy_name, policy_version)
);

CREATE INDEX idx_policy_ack_user ON policy_acknowledgments(user_id);
CREATE INDEX idx_policy_ack_company ON policy_acknowledgments(company_id);

-- Onboarding progress: tracks new hire onboarding completion
-- Sprint 4: Uses notes column as JSON store for tracker data:
--   { items_completed_json: [], signoffs_json: {}, total_items: N, started_at: T, updated_at: T }
-- Tracker rows have phase='_tracker' and task_name='_tracker'
CREATE TABLE IF NOT EXISTS onboarding_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    playbook_type TEXT NOT NULL,
    phase TEXT NOT NULL,
    task_name TEXT NOT NULL,
    is_complete INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    assigned_to TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_onboarding_user ON onboarding_progress(user_id);
CREATE INDEX idx_onboarding_company ON onboarding_progress(company_id);

-- SOP access log: tracks which SOPs users have viewed/downloaded
CREATE TABLE IF NOT EXISTS sop_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    sop_name TEXT NOT NULL,
    action TEXT NOT NULL DEFAULT 'view',
    accessed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_sop_access_user ON sop_access_log(user_id);
CREATE INDEX idx_sop_access_company ON sop_access_log(company_id);

-- Training completions: tracks training module completion
CREATE TABLE IF NOT EXISTS training_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    training_name TEXT NOT NULL,
    module_name TEXT,
    score REAL,
    passed INTEGER,
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    certificate_url TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_training_user ON training_completions(user_id);
CREATE INDEX idx_training_company ON training_completions(company_id);
