-- ================================================================
-- Pure Work AI - Demo Seed Data
-- Sprint 5: Realistic sample data for sales demonstrations
--
-- Demo Company: Acme Manufacturing Inc.
-- 5 Demo Users with varied roles and progress levels
-- Credentials: All users use password 'password123'
-- ================================================================

-- ----------------------------------------------------------------
-- COMPANY
-- ----------------------------------------------------------------
INSERT OR IGNORE INTO companies (id, name, slug, plan, settings)
VALUES (
  1,
  'Acme Manufacturing Inc.',
  'acme',
  'professional',
  '{"industry":"manufacturing","size":"50-100","region":"Ontario, Canada"}'
);

-- ----------------------------------------------------------------
-- USERS
-- Password pattern matches the base64 auth in worker.js (plain comparison)
-- ----------------------------------------------------------------
INSERT OR IGNORE INTO users (id, company_id, email, password_hash, name, role, is_active)
VALUES
  (1, 1, 'admin@demo.com',    'password123', 'Sarah Mitchell',   'admin',    1),
  (2, 1, 'manager@demo.com',  'password123', 'James Rodriguez',  'manager',  1),
  (3, 1, 'employee@demo.com', 'password123', 'Alex Chen',        'employee', 1),
  (4, 1, 'lisa@demo.com',     'password123', 'Lisa Thompson',    'employee', 1),
  (5, 1, 'marcus@demo.com',   'password123', 'Marcus Williams',  'employee', 1);

-- ----------------------------------------------------------------
-- ASSESSMENT RESULTS
-- Sarah: DISC (82%), Manager Readiness (88%), Culture Fit (91%)
-- James: DISC (75%), Safety Competency (94%), Sales Aptitude (72%)
-- Alex:  DISC (68%), Culture Fit (79%)
-- ----------------------------------------------------------------

-- Sarah Mitchell - DISC Assessment (82%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (1, 1, 1, 'disc', '{
  "dimensions": {
    "Dominance": 78,
    "Influence": 85,
    "Steadiness": 62,
    "Conscientiousness": 90
  },
  "primary_style": "C/I",
  "summary": "Sarah leads with Conscientiousness and Influence. She combines analytical rigor with strong interpersonal skills, making her effective in leadership roles that require both precision and people management.",
  "strengths": ["Data-driven decision making", "Clear communication", "Process improvement", "Team motivation"],
  "development_areas": ["Delegation under pressure", "Patience with ambiguity"]
}', 82.0, '2026-06-15T10:30:00Z');

-- Sarah Mitchell - Manager Readiness (88%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (2, 1, 1, 'manager-readiness', '{
  "dimensions": {
    "Communication": 92,
    "Delegation": 85,
    "Conflict Resolution": 88,
    "Performance Management": 90,
    "Strategic Thinking": 84,
    "Team Development": 91
  },
  "readiness_level": "Ready",
  "summary": "Sarah demonstrates strong readiness for management responsibilities. Exceptional communication and team development skills. Minor gap in strategic delegation under high workload.",
  "top_strength": "Communication",
  "growth_priority": "Strategic Thinking"
}', 88.0, '2026-06-18T14:15:00Z');

-- Sarah Mitchell - Culture Fit (91%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (3, 1, 1, 'culture-fit', '{
  "dimensions": {
    "Integrity": 95,
    "Accountability": 92,
    "Transparency": 88,
    "Growth Mindset": 90,
    "Innovation": 86,
    "Persistence": 93,
    "Love": 94
  },
  "alignment": "Strong",
  "summary": "Sarah shows exceptional alignment with organizational values. Particularly strong in Integrity, Love (team care), and Persistence. Her innovation score suggests she may benefit from more exposure to creative problem-solving initiatives.",
  "top_value": "Integrity",
  "growth_area": "Innovation"
}', 91.0, '2026-06-20T09:45:00Z');

-- James Rodriguez - DISC Assessment (75%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (4, 2, 1, 'disc', '{
  "dimensions": {
    "Dominance": 88,
    "Influence": 72,
    "Steadiness": 58,
    "Conscientiousness": 70
  },
  "primary_style": "D",
  "summary": "James leads strongly with Dominance. He is results-oriented, direct, and decisive. Can improve by slowing down to build consensus and attend to details before acting.",
  "strengths": ["Quick decision making", "Goal orientation", "Problem solving", "Taking initiative"],
  "development_areas": ["Active listening", "Patience with process", "Empathetic communication"]
}', 75.0, '2026-06-12T11:00:00Z');

-- James Rodriguez - Safety Competency (94%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (5, 2, 1, 'safety-competency', '{
  "dimensions": {
    "Hazard Identification": 96,
    "Emergency Procedures": 92,
    "PPE Knowledge": 98,
    "Incident Reporting": 90,
    "Regulatory Awareness": 88,
    "Safety Leadership": 95
  },
  "competency_level": "Expert",
  "summary": "James demonstrates expert-level safety competency. Outstanding PPE knowledge and hazard identification. His safety leadership score reflects strong ability to model safe behavior for the team.",
  "certification_recommended": "CRSP (Canadian Registered Safety Professional)",
  "top_area": "PPE Knowledge"
}', 94.0, '2026-06-14T08:30:00Z');

-- James Rodriguez - Sales Aptitude (72%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (6, 2, 1, 'sales-aptitude', '{
  "dimensions": {
    "Prospecting": 68,
    "Relationship Building": 74,
    "Needs Analysis": 70,
    "Presentation Skills": 78,
    "Negotiation": 75,
    "Closing": 65
  },
  "aptitude_level": "Developing",
  "summary": "James shows solid foundational sales skills, particularly in presentations and negotiation. Prospecting and closing are areas where targeted training would yield quick improvement.",
  "top_skill": "Presentation Skills",
  "development_focus": "Closing Techniques"
}', 72.0, '2026-06-22T16:00:00Z');

-- Alex Chen - DISC Assessment (68%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (7, 3, 1, 'disc', '{
  "dimensions": {
    "Dominance": 55,
    "Influence": 60,
    "Steadiness": 85,
    "Conscientiousness": 72
  },
  "primary_style": "S",
  "summary": "Alex leads with Steadiness. He is a reliable, patient team player who values stability and consistency. Can develop by being more assertive in group settings and embracing change more readily.",
  "strengths": ["Reliability", "Team collaboration", "Careful analysis", "Conflict avoidance"],
  "development_areas": ["Assertiveness", "Comfort with change", "Speaking up in meetings"]
}', 68.0, '2026-06-25T13:20:00Z');

-- Alex Chen - Culture Fit (79%)
INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at)
VALUES (8, 3, 1, 'culture-fit', '{
  "dimensions": {
    "Integrity": 88,
    "Accountability": 82,
    "Transparency": 72,
    "Growth Mindset": 76,
    "Innovation": 70,
    "Persistence": 85,
    "Love": 80
  },
  "alignment": "Good",
  "summary": "Alex shows good overall cultural alignment with strong Integrity and Persistence scores. Transparency and Innovation are growth areas - encouraging Alex to share ideas more openly would strengthen team contribution.",
  "top_value": "Integrity",
  "growth_area": "Transparency"
}', 79.0, '2026-06-27T10:10:00Z');

-- ----------------------------------------------------------------
-- POLICY ACKNOWLEDGMENTS
-- 10 policies in the system (matching content-manifest.json)
-- Sarah: 10/10 | James: 7/10 | Alex: 3/10 | Lisa: 1/10 | Marcus: 0/10
-- ----------------------------------------------------------------

-- All 10 policy names for reference:
-- 1. Workplace Harassment Policy (Ontario)
-- 2. AI Use Policy
-- 3. Working Alone Policy (Ontario)
-- 4. Health & Safety Policy (Ontario)
-- 5. Social Media Policy
-- 6. Travel & Expense Policy
-- 7. Personal Days Policy (Ontario)
-- 8. Progressive Discipline Policy (Ontario)
-- 9. Remote Work Policy
-- 10. Confidentiality & IP Policy

-- Sarah Mitchell: ALL 10 policies acknowledged
INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES
  (1,  1, 1, 'Workplace Harassment Policy (Ontario)',         '1.0', '2026-06-10T09:00:00Z', '192.168.1.100'),
  (2,  1, 1, 'AI Use Policy',                                 '1.0', '2026-06-10T09:05:00Z', '192.168.1.100'),
  (3,  1, 1, 'Working Alone Policy (Ontario)',                 '1.0', '2026-06-10T09:10:00Z', '192.168.1.100'),
  (4,  1, 1, 'Health & Safety Policy (Ontario)',               '1.0', '2026-06-10T09:15:00Z', '192.168.1.100'),
  (5,  1, 1, 'Social Media Policy',                            '1.0', '2026-06-10T09:20:00Z', '192.168.1.100'),
  (6,  1, 1, 'Travel & Expense Policy',                        '1.0', '2026-06-10T09:25:00Z', '192.168.1.100'),
  (7,  1, 1, 'Personal Days Policy (Ontario)',                  '1.0', '2026-06-10T09:30:00Z', '192.168.1.100'),
  (8,  1, 1, 'Progressive Discipline Policy (Ontario)',         '1.0', '2026-06-10T09:35:00Z', '192.168.1.100'),
  (9,  1, 1, 'Remote Work Policy',                              '1.0', '2026-06-10T09:40:00Z', '192.168.1.100'),
  (10, 1, 1, 'Confidentiality & IP Policy',                     '1.0', '2026-06-10T09:45:00Z', '192.168.1.100');

-- James Rodriguez: 7 of 10 policies (missing Personal Days, Remote Work, Confidentiality)
INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES
  (11, 2, 1, 'Workplace Harassment Policy (Ontario)',         '1.0', '2026-06-11T10:00:00Z', '192.168.1.101'),
  (12, 2, 1, 'AI Use Policy',                                 '1.0', '2026-06-11T10:08:00Z', '192.168.1.101'),
  (13, 2, 1, 'Working Alone Policy (Ontario)',                 '1.0', '2026-06-11T10:15:00Z', '192.168.1.101'),
  (14, 2, 1, 'Health & Safety Policy (Ontario)',               '1.0', '2026-06-11T10:22:00Z', '192.168.1.101'),
  (15, 2, 1, 'Social Media Policy',                            '1.0', '2026-06-11T10:30:00Z', '192.168.1.101'),
  (16, 2, 1, 'Travel & Expense Policy',                        '1.0', '2026-06-11T10:38:00Z', '192.168.1.101'),
  (17, 2, 1, 'Progressive Discipline Policy (Ontario)',         '1.0', '2026-06-11T10:45:00Z', '192.168.1.101');

-- Alex Chen: 3 of 10 policies (Harassment, AI Use, H&S)
INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES
  (18, 3, 1, 'Workplace Harassment Policy (Ontario)',         '1.0', '2026-06-20T14:00:00Z', '192.168.1.102'),
  (19, 3, 1, 'AI Use Policy',                                 '1.0', '2026-06-20T14:10:00Z', '192.168.1.102'),
  (20, 3, 1, 'Health & Safety Policy (Ontario)',               '1.0', '2026-06-20T14:20:00Z', '192.168.1.102');

-- Lisa Thompson: 1 of 10 policies (Harassment only)
INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES
  (21, 4, 1, 'Workplace Harassment Policy (Ontario)',         '1.0', '2026-06-28T11:00:00Z', '192.168.1.103');

-- Marcus Williams: 0 policies acknowledged (no rows)

-- ----------------------------------------------------------------
-- ONBOARDING PROGRESS
-- Lisa: Manufacturing playbook, 45% complete
-- Marcus: General SMB playbook, 15% complete
--
-- Uses Sprint 4 tracker pattern: phase='_tracker', task_name='_tracker'
-- notes column stores JSON: { items_completed_json, signoffs_json, total_items, started_at, updated_at }
-- ----------------------------------------------------------------

-- Lisa Thompson - Manufacturing Onboarding (45% complete)
-- Manufacturing playbook has ~40 items total
-- Pre-Start (8 items: done), Day 1 (10 items: done), Week 1 (10 items: 50% = 5 done)
-- Total completed: 23 of 40 = ~45% (we round to make it realistic -- use 18/40=45%)
INSERT OR IGNORE INTO onboarding_progress (id, user_id, company_id, playbook_type, phase, task_name, is_complete, completed_at, assigned_to, notes)
VALUES (1, 4, 1, 'manufacturing', '_tracker', '_tracker', 0, NULL, 'James Rodriguez', '{
  "items_completed_json": [
    "pre-start-1", "pre-start-2", "pre-start-3", "pre-start-4", "pre-start-5", "pre-start-6", "pre-start-7", "pre-start-8",
    "day1-1", "day1-2", "day1-3", "day1-4", "day1-5", "day1-6", "day1-7", "day1-8", "day1-9", "day1-10",
    "week1-1", "week1-2", "week1-3", "week1-4", "week1-5"
  ],
  "signoffs_json": {
    "pre-start": {"signed_by": "James Rodriguez", "signed_at": "2026-06-25T16:00:00Z", "notes": "All pre-start items completed. Workspace and PPE ready."},
    "day1": {"signed_by": "James Rodriguez", "signed_at": "2026-06-28T17:30:00Z", "notes": "Orientation complete. Lisa was enthusiastic and asked great questions about safety protocols."}
  },
  "total_items": 50,
  "started_at": "2026-06-24T08:00:00Z",
  "updated_at": "2026-07-02T15:30:00Z"
}');

-- Marcus Williams - General SMB Onboarding (15% complete)
-- General SMB playbook has ~40 items total
-- Pre-Start: 50% done (4 of 8 items)
-- Nothing else started
INSERT OR IGNORE INTO onboarding_progress (id, user_id, company_id, playbook_type, phase, task_name, is_complete, completed_at, assigned_to, notes)
VALUES (2, 5, 1, 'general-smb', '_tracker', '_tracker', 0, NULL, 'Sarah Mitchell', '{
  "items_completed_json": [
    "pre-start-1", "pre-start-2", "pre-start-3", "pre-start-4", "pre-start-5", "pre-start-6"
  ],
  "signoffs_json": {},
  "total_items": 40,
  "started_at": "2026-07-01T08:00:00Z",
  "updated_at": "2026-07-03T11:00:00Z"
}');

-- ----------------------------------------------------------------
-- SOP / CONTENT ACCESS LOG
-- Shows various users accessing different content items
-- ----------------------------------------------------------------
INSERT OR IGNORE INTO sop_access_log (id, user_id, company_id, sop_name, action, accessed_at) VALUES
  (1,  1, 1, 'SOP Master Template',                   'download', '2026-06-10T08:30:00Z'),
  (2,  1, 1, 'Manufacturing SOP Pack',                 'view',     '2026-06-10T08:45:00Z'),
  (3,  1, 1, 'Manufacturing SOP Pack',                 'download', '2026-06-10T08:46:00Z'),
  (4,  1, 1, 'Workplace Harassment Policy (Ontario)',   'view',     '2026-06-10T09:00:00Z'),
  (5,  2, 1, 'Safety SOP Pack',                        'download', '2026-06-11T10:00:00Z'),
  (6,  2, 1, 'Manufacturing SOP Pack',                 'view',     '2026-06-11T10:15:00Z'),
  (7,  2, 1, 'Manufacturing Onboarding Playbook',      'download', '2026-06-24T07:45:00Z'),
  (8,  3, 1, 'AI Use Policy',                           'view',     '2026-06-20T14:05:00Z'),
  (9,  3, 1, 'Operations Roles (7 JDs)',               'download', '2026-06-22T09:30:00Z'),
  (10, 4, 1, 'Manufacturing Onboarding Playbook',      'view',     '2026-06-28T08:00:00Z'),
  (11, 4, 1, 'Safety SOP Pack',                        'view',     '2026-06-28T08:20:00Z'),
  (12, 4, 1, 'Health & Safety Policy (Ontario)',        'view',     '2026-06-28T08:35:00Z'),
  (13, 5, 1, 'General SMB Onboarding Playbook',       'download', '2026-07-01T08:10:00Z'),
  (14, 1, 1, 'Benchmarking Methodology Guide',        'view',     '2026-07-02T11:00:00Z'),
  (15, 1, 1, 'Compensation Source Guide',              'download', '2026-07-02T11:15:00Z');
