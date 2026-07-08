/**
 * Pure Work AI - Cloudflare Worker API
 * Sprint 1+2+3+4+5: Authentication, Dashboard, Assessment Center, Content Library,
 * Policy Acknowledgment, Onboarding Tracker, Admin Dashboard, User Management,
 * Demo Seed Data
 *
 * Routes:
 *   POST /api/auth/login           - Authenticate user (demo credentials for MVP)
 *   GET  /api/auth/me              - Get current user from token
 *   GET  /api/dashboard            - Dashboard metrics (real counts from D1)
 *   GET  /api/dashboard/activity   - Recent activity feed across all modules
 *   POST /api/assessments/results  - Save/update assessment result
 *   GET  /api/assessments/results  - Get user's assessment results
 *   GET  /api/assessments/team     - Get team results (admin/manager only)
 *   POST /api/library/access       - Log content library access/download
 *   GET  /api/library/stats        - Get content access stats (admin/manager)
 *   POST /api/policies/acknowledge - Acknowledge a policy
 *   GET  /api/policies/status      - Get user's policy acknowledgments
 *   GET  /api/policies/team        - Get team policy status (admin/manager)
 *   POST /api/onboarding/start     - Start onboarding for a user (admin/manager)
 *   GET  /api/onboarding/me        - Get current user's onboarding progress
 *   PUT  /api/onboarding/update    - Update onboarding progress
 *   GET  /api/onboarding/team      - Get all onboarding progress (admin/manager)
 *   POST /api/onboarding/signoff   - Record supervisor sign-off at milestone
 *   GET  /api/users                - List all company users (admin only)
 *   POST /api/users                - Create new user (admin only)
 *   PUT  /api/users/:id            - Update user (admin only)
 *   POST /api/seed                 - Seed demo data (dev only, no auth)
 *   *    /api/*                    - 404 for unknown API routes
 *
 * Static assets are served by Cloudflare Pages from /public/.
 * This worker handles the /api/* namespace only.
 */

/* ================================================================
   CONFIGURATION
   ================================================================ */

/** Demo users for MVP (replaced with D1 database in Sprint 2) */
const DEMO_USERS = [
  {
    id: 1,
    email: 'admin@demo.com',
    password: 'password123',
    name: 'Sarah Mitchell',
    role: 'admin',
    company: 'Acme Manufacturing Inc.'
  },
  {
    id: 2,
    email: 'manager@demo.com',
    password: 'password123',
    name: 'James Rodriguez',
    role: 'manager',
    company: 'Acme Manufacturing Inc.'
  },
  {
    id: 3,
    email: 'employee@demo.com',
    password: 'password123',
    name: 'Alex Chen',
    role: 'employee',
    company: 'Acme Manufacturing Inc.'
  },
  {
    id: 4,
    email: 'lisa@demo.com',
    password: 'password123',
    name: 'Lisa Thompson',
    role: 'employee',
    company: 'Acme Manufacturing Inc.'
  },
  {
    id: 5,
    email: 'marcus@demo.com',
    password: 'password123',
    name: 'Marcus Williams',
    role: 'employee',
    company: 'Acme Manufacturing Inc.'
  }
];

/** Token expiry duration (24 hours in milliseconds) */
const TOKEN_EXPIRY_MS = 24 * 60 * 60 * 1000;

/* ================================================================
   TOKEN HELPERS (Simple base64 encoding for MVP)
   ================================================================ */

/**
 * Create a simple auth token by base64-encoding user data and expiry.
 * In production, this would be a proper JWT with signing.
 */
function createToken(user) {
  const payload = {
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role,
    company: user.company,
    exp: Date.now() + TOKEN_EXPIRY_MS
  };
  /* btoa works in Cloudflare Workers runtime */
  return btoa(JSON.stringify(payload));
}

/**
 * Validate and decode a token. Returns the user payload or null.
 */
function validateToken(token) {
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token));

    /* Check expiry */
    if (!payload.exp || payload.exp < Date.now()) {
      return null;
    }

    /* Check required fields */
    if (!payload.id || !payload.email || !payload.name) {
      return null;
    }

    return {
      id: payload.id,
      email: payload.email,
      name: payload.name,
      role: payload.role,
      company: payload.company
    };
  } catch (e) {
    return null;
  }
}

/**
 * Extract bearer token from Authorization header.
 */
function extractToken(request) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader) return null;

  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') return null;

  return parts[1];
}

/* ================================================================
   CORS HEADERS
   ================================================================ */

/** Standard CORS headers applied to all API responses */
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400'
};

/**
 * Create a JSON response with CORS headers.
 */
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS
    }
  });
}

/**
 * Handle CORS preflight (OPTIONS) requests.
 */
function handleOptions() {
  return new Response(null, {
    status: 204,
    headers: CORS_HEADERS
  });
}

/* ================================================================
   ROUTE HANDLERS
   ================================================================ */

/**
 * POST /api/auth/login
 * Authenticate with email and password.
 * Returns token and user data on success.
 */
async function handleLogin(request) {
  /* Only accept POST */
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { email, password } = body;

  if (!email || !password) {
    return jsonResponse({ error: 'Email and password are required.' }, 400);
  }

  /* Find matching user (case-insensitive email) */
  const user = DEMO_USERS.find(
    u => u.email.toLowerCase() === email.toLowerCase() && u.password === password
  );

  if (!user) {
    return jsonResponse({ error: 'Invalid email or password.' }, 401);
  }

  /* Generate token */
  const token = createToken(user);

  /* Return user data (excluding password) */
  return jsonResponse({
    token,
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      company: user.company
    }
  });
}

/**
 * GET /api/auth/me
 * Validate token and return current user info.
 */
async function handleAuthMe(request) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Invalid or expired token.' }, 401);
  }

  return jsonResponse({ user });
}

/**
 * GET /api/dashboard
 * Return dashboard metrics with real assessment count from D1.
 */
async function handleDashboard(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  /* Verify authentication */
  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  let assessmentsCompleted = 0;
  let policiesAcknowledged = 0;
  let onboardingPercent = 0;

  /* Query D1 for real counts if database is available */
  if (env && env.DB) {
    try {
      const assessResult = await env.DB.prepare(
        'SELECT COUNT(DISTINCT assessment_type) as count FROM assessment_results WHERE user_id = ?'
      ).bind(user.id).first();
      assessmentsCompleted = assessResult ? assessResult.count : 0;

      const policyResult = await env.DB.prepare(
        'SELECT COUNT(DISTINCT policy_name) as count FROM policy_acknowledgments WHERE user_id = ?'
      ).bind(user.id).first();
      policiesAcknowledged = policyResult ? policyResult.count : 0;

      /* Get onboarding progress for this user */
      const onboardingResult = await env.DB.prepare(
        'SELECT items_completed_json, total_items FROM onboarding_progress WHERE user_id = ? ORDER BY started_at DESC LIMIT 1'
      ).bind(user.id).first();
      if (onboardingResult && onboardingResult.total_items > 0) {
        const completed = JSON.parse(onboardingResult.items_completed_json || '[]');
        onboardingPercent = Math.round((completed.length / onboardingResult.total_items) * 100);
      }
    } catch (e) {
      /* Fall back to 0 if DB query fails */
      console.error('Dashboard DB query failed:', e);
    }
  }

  return jsonResponse({
    assessments_completed: assessmentsCompleted,
    total_assessments: 8,
    policies_acknowledged: policiesAcknowledged,
    total_policies: 10,
    onboarding_percent: onboardingPercent,
    content_count: 34
  });
}

/* ================================================================
   ASSESSMENT ENDPOINTS (Sprint 2)
   ================================================================ */

/**
 * POST /api/assessments/results
 * Save or update assessment results for the authenticated user.
 * Body: { assessment_type, scores_json, overall_score }
 * If a result already exists for this user + assessment_type, it updates.
 */
async function handleSaveAssessmentResult(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { assessment_type, scores_json, overall_score } = body;

  if (!assessment_type) {
    return jsonResponse({ error: 'assessment_type is required.' }, 400);
  }

  /* Use company_id 1 as default for demo users without company_id */
  const companyId = user.company_id || 1;
  const scoresStr = typeof scores_json === 'string' ? scores_json : JSON.stringify(scores_json || {});
  const overallNum = typeof overall_score === 'number' ? overall_score : parseFloat(overall_score) || 0;
  const now = new Date().toISOString();

  if (!env || !env.DB) {
    /* No database: return a mock response */
    return jsonResponse({
      id: 'mock-' + Date.now(),
      assessment_type,
      overall_score: overallNum,
      completed_at: now
    });
  }

  try {
    /* Check if user already has a result for this assessment type */
    const existing = await env.DB.prepare(
      'SELECT id FROM assessment_results WHERE user_id = ? AND assessment_type = ?'
    ).bind(user.id, assessment_type).first();

    if (existing) {
      /* UPDATE existing result */
      await env.DB.prepare(
        'UPDATE assessment_results SET score_json = ?, total_score = ?, completed_at = ? WHERE id = ?'
      ).bind(scoresStr, overallNum, now, existing.id).run();

      return jsonResponse({
        id: existing.id,
        assessment_type,
        overall_score: overallNum,
        completed_at: now
      });
    } else {
      /* INSERT new result */
      const result = await env.DB.prepare(
        'INSERT INTO assessment_results (user_id, company_id, assessment_type, score_json, total_score, completed_at) VALUES (?, ?, ?, ?, ?, ?)'
      ).bind(user.id, companyId, assessment_type, scoresStr, overallNum, now).run();

      return jsonResponse({
        id: result.meta.last_row_id,
        assessment_type,
        overall_score: overallNum,
        completed_at: now
      }, 201);
    }
  } catch (e) {
    console.error('Save assessment result error:', e);
    return jsonResponse({ error: 'Failed to save assessment result.' }, 500);
  }
}

/**
 * GET /api/assessments/results
 * Return all assessment results for the authenticated user.
 */
async function handleGetAssessmentResults(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (!env || !env.DB) {
    return jsonResponse({ results: [] });
  }

  try {
    const { results } = await env.DB.prepare(
      'SELECT id, assessment_type, score_json, total_score, completed_at FROM assessment_results WHERE user_id = ? ORDER BY completed_at DESC'
    ).bind(user.id).all();

    return jsonResponse({ results: results || [] });
  } catch (e) {
    console.error('Get assessment results error:', e);
    return jsonResponse({ error: 'Failed to fetch assessment results.' }, 500);
  }
}

/**
 * GET /api/assessments/team
 * Return all assessment results for the company (admin/manager only).
 */
async function handleGetTeamResults(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  /* Role check: only admin or manager */
  if (user.role !== 'admin' && user.role !== 'manager') {
    return jsonResponse({ error: 'Insufficient permissions. Admin or manager role required.' }, 403);
  }

  const companyId = user.company_id || 1;

  if (!env || !env.DB) {
    return jsonResponse({ results: [] });
  }

  try {
    const { results } = await env.DB.prepare(
      'SELECT ar.id, ar.assessment_type, ar.score_json, ar.total_score, ar.completed_at, ar.user_id FROM assessment_results ar WHERE ar.company_id = ? ORDER BY ar.completed_at DESC'
    ).bind(companyId).all();

    return jsonResponse({ results: results || [] });
  } catch (e) {
    console.error('Get team results error:', e);
    return jsonResponse({ error: 'Failed to fetch team results.' }, 500);
  }
}

/* ================================================================
   CONTENT LIBRARY ENDPOINTS (Sprint 3)
   ================================================================ */

/**
 * POST /api/library/access
 * Log a content library access event (view or download).
 * Body: { item_id, item_name, category }
 */
async function handleLibraryAccess(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { item_id, item_name, category } = body;

  if (!item_name) {
    return jsonResponse({ error: 'item_name is required.' }, 400);
  }

  const companyId = user.company_id || 1;

  if (!env || !env.DB) {
    return jsonResponse({ logged: true });
  }

  try {
    await env.DB.prepare(
      'INSERT INTO sop_access_log (user_id, company_id, sop_name, action, accessed_at) VALUES (?, ?, ?, ?, ?)'
    ).bind(user.id, companyId, item_name, 'download', new Date().toISOString()).run();

    return jsonResponse({ logged: true });
  } catch (e) {
    console.error('Library access log error:', e);
    return jsonResponse({ error: 'Failed to log access.' }, 500);
  }
}

/**
 * GET /api/library/stats
 * Return access counts grouped by item name (admin/manager only).
 */
async function handleLibraryStats(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin' && user.role !== 'manager') {
    return jsonResponse({ error: 'Insufficient permissions. Admin or manager role required.' }, 403);
  }

  const companyId = user.company_id || 1;

  if (!env || !env.DB) {
    return jsonResponse({ stats: [] });
  }

  try {
    const { results } = await env.DB.prepare(
      'SELECT sop_name, COUNT(*) as access_count FROM sop_access_log WHERE company_id = ? GROUP BY sop_name ORDER BY access_count DESC'
    ).bind(companyId).all();

    return jsonResponse({ stats: results || [] });
  } catch (e) {
    console.error('Library stats error:', e);
    return jsonResponse({ error: 'Failed to fetch library stats.' }, 500);
  }
}

/* ================================================================
   POLICY ACKNOWLEDGMENT ENDPOINTS (Sprint 3)
   ================================================================ */

/**
 * POST /api/policies/acknowledge
 * Acknowledge a policy for the authenticated user.
 * Body: { policy_name, policy_version }
 */
async function handlePolicyAcknowledge(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { policy_name, policy_version } = body;

  if (!policy_name) {
    return jsonResponse({ error: 'policy_name is required.' }, 400);
  }

  const version = policy_version || '1.0';
  const companyId = user.company_id || 1;
  const now = new Date().toISOString();
  const ipAddress = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || 'unknown';

  if (!env || !env.DB) {
    /* No database: return a mock response */
    return jsonResponse({
      id: 'mock-' + Date.now(),
      policy_name,
      policy_version: version,
      acknowledged_at: now
    });
  }

  try {
    /* Check if already acknowledged (same user + policy + version) */
    const existing = await env.DB.prepare(
      'SELECT id, acknowledged_at FROM policy_acknowledgments WHERE user_id = ? AND policy_name = ? AND policy_version = ?'
    ).bind(user.id, policy_name, version).first();

    if (existing) {
      return jsonResponse({
        id: existing.id,
        policy_name,
        policy_version: version,
        acknowledged_at: existing.acknowledged_at,
        already_acknowledged: true
      });
    }

    /* Insert new acknowledgment */
    const result = await env.DB.prepare(
      'INSERT INTO policy_acknowledgments (user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(user.id, companyId, policy_name, version, now, ipAddress).run();

    return jsonResponse({
      id: result.meta.last_row_id,
      policy_name,
      policy_version: version,
      acknowledged_at: now
    }, 201);
  } catch (e) {
    console.error('Policy acknowledge error:', e);
    return jsonResponse({ error: 'Failed to acknowledge policy.' }, 500);
  }
}

/**
 * GET /api/policies/status
 * Return all policy acknowledgments for the authenticated user.
 */
async function handlePolicyStatus(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (!env || !env.DB) {
    return jsonResponse({ acknowledgments: [] });
  }

  try {
    const { results } = await env.DB.prepare(
      'SELECT id, policy_name, policy_version, acknowledged_at FROM policy_acknowledgments WHERE user_id = ? ORDER BY acknowledged_at DESC'
    ).bind(user.id).all();

    return jsonResponse({ acknowledgments: results || [] });
  } catch (e) {
    console.error('Policy status error:', e);
    return jsonResponse({ error: 'Failed to fetch policy status.' }, 500);
  }
}

/**
 * GET /api/policies/team
 * Return all policy acknowledgments for the company (admin/manager only).
 */
async function handlePolicyTeam(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin' && user.role !== 'manager') {
    return jsonResponse({ error: 'Insufficient permissions. Admin or manager role required.' }, 403);
  }

  const companyId = user.company_id || 1;

  if (!env || !env.DB) {
    return jsonResponse({ acknowledgments: [] });
  }

  try {
    const { results } = await env.DB.prepare(
      'SELECT pa.id, pa.policy_name, pa.policy_version, pa.acknowledged_at, pa.user_id FROM policy_acknowledgments pa WHERE pa.company_id = ? ORDER BY pa.acknowledged_at DESC'
    ).bind(companyId).all();

    return jsonResponse({ acknowledgments: results || [] });
  } catch (e) {
    console.error('Policy team error:', e);
    return jsonResponse({ error: 'Failed to fetch team policy status.' }, 500);
  }
}

/* ================================================================
   ONBOARDING ENDPOINTS (Sprint 4)
   ================================================================ */

/**
 * POST /api/onboarding/start
 * Start onboarding for a user with a specific playbook type.
 * Auth required, admin/manager only.
 * Body: { user_id, checklist_type }
 */
async function handleOnboardingStart(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin' && user.role !== 'manager') {
    return jsonResponse({ error: 'Insufficient permissions. Admin or manager role required.' }, 403);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { user_id, checklist_type } = body;

  if (!checklist_type) {
    return jsonResponse({ error: 'checklist_type is required.' }, 400);
  }

  const targetUserId = user_id || user.id;
  const companyId = user.company_id || 1;
  const now = new Date().toISOString();

  /* Playbook total item counts */
  const playbookTotals = {
    'manufacturing': 67,
    'professional-services': 54,
    'tech-saas': 54,
    'general-smb': 52
  };

  const totalItems = playbookTotals[checklist_type] || 52;

  if (!env || !env.DB) {
    return jsonResponse({
      id: 'mock-' + Date.now(),
      user_id: targetUserId,
      playbook_type: checklist_type,
      items_completed_json: '[]',
      signoffs_json: '{}',
      total_items: totalItems,
      started_at: now
    });
  }

  try {
    const result = await env.DB.prepare(
      'INSERT INTO onboarding_progress (user_id, company_id, playbook_type, phase, task_name, is_complete, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(targetUserId, companyId, checklist_type, '_tracker', '_tracker', 0, now).run();

    /* We also store as a single-row tracker using a new approach:
       For MVP, we use a single row with items_completed_json stored in the notes column */
    await env.DB.prepare(
      'UPDATE onboarding_progress SET notes = ? WHERE id = ?'
    ).bind(JSON.stringify({
      items_completed_json: [],
      signoffs_json: {},
      total_items: totalItems,
      started_at: now
    }), result.meta.last_row_id).run();

    return jsonResponse({
      id: result.meta.last_row_id,
      user_id: targetUserId,
      playbook_type: checklist_type,
      items_completed_json: '[]',
      signoffs_json: '{}',
      total_items: totalItems,
      started_at: now
    }, 201);
  } catch (e) {
    console.error('Onboarding start error:', e);
    return jsonResponse({ error: 'Failed to start onboarding.' }, 500);
  }
}

/**
 * GET /api/onboarding/me
 * Get the authenticated user's onboarding progress.
 */
async function handleOnboardingMe(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (!env || !env.DB) {
    return jsonResponse({ onboarding: null });
  }

  try {
    const row = await env.DB.prepare(
      "SELECT id, user_id, playbook_type, notes, created_at FROM onboarding_progress WHERE user_id = ? AND phase = '_tracker' ORDER BY created_at DESC LIMIT 1"
    ).bind(user.id).first();

    if (!row) {
      return jsonResponse({ onboarding: null });
    }

    let data = {};
    try {
      data = JSON.parse(row.notes || '{}');
    } catch (e) { /* ignore parse errors */ }

    return jsonResponse({
      onboarding: {
        id: row.id,
        user_id: row.user_id,
        playbook_type: row.playbook_type,
        items_completed_json: JSON.stringify(data.items_completed_json || []),
        signoffs_json: JSON.stringify(data.signoffs_json || {}),
        total_items: data.total_items || 0,
        started_at: data.started_at || row.created_at,
        updated_at: data.updated_at || row.created_at
      }
    });
  } catch (e) {
    console.error('Onboarding me error:', e);
    return jsonResponse({ error: 'Failed to fetch onboarding progress.' }, 500);
  }
}

/**
 * PUT /api/onboarding/update
 * Update the authenticated user's onboarding progress.
 * Body: { items_completed_json, percent_complete }
 */
async function handleOnboardingUpdate(request, env) {
  if (request.method !== 'PUT') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { items_completed_json, percent_complete } = body;
  const now = new Date().toISOString();

  if (!env || !env.DB) {
    return jsonResponse({ updated: true, percent_complete: percent_complete || 0 });
  }

  try {
    /* Find user's active onboarding tracker row */
    const row = await env.DB.prepare(
      "SELECT id, notes FROM onboarding_progress WHERE user_id = ? AND phase = '_tracker' ORDER BY created_at DESC LIMIT 1"
    ).bind(user.id).first();

    if (!row) {
      return jsonResponse({ error: 'No active onboarding found.' }, 404);
    }

    let data = {};
    try {
      data = JSON.parse(row.notes || '{}');
    } catch (e) { /* ignore */ }

    /* Update the completed items */
    const completedItems = typeof items_completed_json === 'string'
      ? JSON.parse(items_completed_json)
      : (items_completed_json || []);

    data.items_completed_json = completedItems;
    data.updated_at = now;

    await env.DB.prepare(
      'UPDATE onboarding_progress SET notes = ? WHERE id = ?'
    ).bind(JSON.stringify(data), row.id).run();

    return jsonResponse({
      updated: true,
      percent_complete: data.total_items > 0
        ? Math.round((completedItems.length / data.total_items) * 100)
        : 0
    });
  } catch (e) {
    console.error('Onboarding update error:', e);
    return jsonResponse({ error: 'Failed to update onboarding progress.' }, 500);
  }
}

/**
 * GET /api/onboarding/team
 * Get all onboarding progress for the company (admin/manager only).
 */
async function handleOnboardingTeam(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin' && user.role !== 'manager') {
    return jsonResponse({ error: 'Insufficient permissions. Admin or manager role required.' }, 403);
  }

  const companyId = user.company_id || 1;

  if (!env || !env.DB) {
    return jsonResponse({ progress: [] });
  }

  try {
    const { results } = await env.DB.prepare(
      "SELECT op.id, op.user_id, op.playbook_type, op.notes, op.created_at FROM onboarding_progress op WHERE op.company_id = ? AND op.phase = '_tracker' ORDER BY op.created_at DESC"
    ).bind(companyId).all();

    const progress = (results || []).map(function(row) {
      let data = {};
      try { data = JSON.parse(row.notes || '{}'); } catch (e) { /* ignore */ }
      const completed = data.items_completed_json || [];
      const total = data.total_items || 0;
      return {
        id: row.id,
        user_id: row.user_id,
        playbook_type: row.playbook_type,
        percent_complete: total > 0 ? Math.round((completed.length / total) * 100) : 0,
        total_items: total,
        items_completed: completed.length,
        started_at: data.started_at || row.created_at,
        updated_at: data.updated_at || row.created_at
      };
    });

    return jsonResponse({ progress });
  } catch (e) {
    console.error('Onboarding team error:', e);
    return jsonResponse({ error: 'Failed to fetch team onboarding progress.' }, 500);
  }
}

/**
 * POST /api/onboarding/signoff
 * Record supervisor sign-off at a milestone.
 * Auth required, admin/manager only.
 * Body: { onboarding_id, milestone }
 */
async function handleOnboardingSignoff(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin' && user.role !== 'manager') {
    return jsonResponse({ error: 'Insufficient permissions. Admin or manager role required.' }, 403);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { onboarding_id, milestone } = body;

  if (!milestone) {
    return jsonResponse({ error: 'milestone is required.' }, 400);
  }

  const now = new Date().toISOString();

  if (!env || !env.DB) {
    return jsonResponse({
      signed_off: true,
      milestone,
      signed_by: user.name,
      signed_at: now
    });
  }

  try {
    /* Find the onboarding tracker row - use onboarding_id if provided, else user's own */
    let row;
    if (onboarding_id) {
      row = await env.DB.prepare(
        "SELECT id, notes FROM onboarding_progress WHERE id = ? AND phase = '_tracker'"
      ).bind(onboarding_id).first();
    } else {
      row = await env.DB.prepare(
        "SELECT id, notes FROM onboarding_progress WHERE user_id = ? AND phase = '_tracker' ORDER BY created_at DESC LIMIT 1"
      ).bind(user.id).first();
    }

    if (!row) {
      return jsonResponse({ error: 'Onboarding record not found.' }, 404);
    }

    let data = {};
    try { data = JSON.parse(row.notes || '{}'); } catch (e) { /* ignore */ }

    /* Add signoff */
    if (!data.signoffs_json) data.signoffs_json = {};
    data.signoffs_json[milestone] = {
      signed_by: user.name,
      signed_by_id: user.id,
      signed_at: now
    };
    data.updated_at = now;

    await env.DB.prepare(
      'UPDATE onboarding_progress SET notes = ? WHERE id = ?'
    ).bind(JSON.stringify(data), row.id).run();

    return jsonResponse({
      signed_off: true,
      milestone,
      signed_by: user.name,
      signed_at: now
    });
  } catch (e) {
    console.error('Onboarding signoff error:', e);
    return jsonResponse({ error: 'Failed to record sign-off.' }, 500);
  }
}

/* ================================================================
   DASHBOARD ACTIVITY ENDPOINT (Sprint 4)
   ================================================================ */

/**
 * GET /api/dashboard/activity
 * Return recent activity across all tracked actions for the company.
 * Auth required.
 */
async function handleDashboardActivity(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  const companyId = user.company_id || 1;

  if (!env || !env.DB) {
    return jsonResponse({ activities: [] });
  }

  try {
    /* UNION query across assessment_results, policy_acknowledgments, sop_access_log */
    const { results } = await env.DB.prepare(
      "SELECT user_id, 'assessment' as type, assessment_type as detail, completed_at as timestamp FROM assessment_results WHERE company_id = ? " +
      "UNION ALL " +
      "SELECT user_id, 'policy' as type, policy_name as detail, acknowledged_at as timestamp FROM policy_acknowledgments WHERE company_id = ? " +
      "UNION ALL " +
      "SELECT user_id, 'download' as type, sop_name as detail, accessed_at as timestamp FROM sop_access_log WHERE company_id = ? " +
      "ORDER BY timestamp DESC LIMIT 10"
    ).bind(companyId, companyId, companyId).all();

    /* Enrich with user names from DEMO_USERS */
    const activities = (results || []).map(function(row) {
      const demoUser = DEMO_USERS.find(function(u) { return u.id === row.user_id; });
      return {
        user_id: row.user_id,
        user_name: demoUser ? demoUser.name : ('User #' + row.user_id),
        type: row.type,
        detail: row.detail,
        timestamp: row.timestamp
      };
    });

    return jsonResponse({ activities });
  } catch (e) {
    console.error('Dashboard activity error:', e);
    return jsonResponse({ activities: [] });
  }
}

/* ================================================================
   USER MANAGEMENT ENDPOINTS (Sprint 4)
   ================================================================ */

/**
 * GET /api/users
 * Return all users for the company (admin only).
 */
async function handleGetUsers(request, env) {
  if (request.method !== 'GET') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin') {
    return jsonResponse({ error: 'Insufficient permissions. Admin role required.' }, 403);
  }

  /* For MVP, return DEMO_USERS without passwords */
  const users = DEMO_USERS.map(function(u) {
    return {
      id: u.id,
      name: u.name,
      email: u.email,
      role: u.role,
      company: u.company,
      status: 'active'
    };
  });

  return jsonResponse({ users });
}

/**
 * POST /api/users
 * Create a new user (admin only).
 * Body: { name, email, role, password }
 * For MVP: adds to DEMO_USERS array (in-memory, not persisted).
 */
async function handleCreateUser(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin') {
    return jsonResponse({ error: 'Insufficient permissions. Admin role required.' }, 403);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const { name, email, role, password } = body;

  if (!name || !email) {
    return jsonResponse({ error: 'name and email are required.' }, 400);
  }

  /* Check for duplicate email */
  const existing = DEMO_USERS.find(function(u) {
    return u.email.toLowerCase() === email.toLowerCase();
  });
  if (existing) {
    return jsonResponse({ error: 'A user with that email already exists.' }, 409);
  }

  /* Generate next ID */
  const nextId = Math.max.apply(null, DEMO_USERS.map(function(u) { return u.id; })) + 1;

  const newUser = {
    id: nextId,
    email: email,
    password: password || 'password123',
    name: name,
    role: role || 'employee',
    company: user.company || 'Pure Technology'
  };

  DEMO_USERS.push(newUser);

  return jsonResponse({
    id: newUser.id,
    name: newUser.name,
    email: newUser.email,
    role: newUser.role,
    company: newUser.company,
    status: 'active'
  }, 201);
}

/**
 * PUT /api/users/:id
 * Update a user (admin only).
 * Body: { name, role, status }
 */
async function handleUpdateUser(request, env, userId) {
  if (request.method !== 'PUT') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  const token = extractToken(request);
  const user = validateToken(token);

  if (!user) {
    return jsonResponse({ error: 'Authentication required.' }, 401);
  }

  if (user.role !== 'admin') {
    return jsonResponse({ error: 'Insufficient permissions. Admin role required.' }, 403);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid request body. Expected JSON.' }, 400);
  }

  const targetUser = DEMO_USERS.find(function(u) { return u.id === parseInt(userId); });
  if (!targetUser) {
    return jsonResponse({ error: 'User not found.' }, 404);
  }

  /* Update allowed fields */
  if (body.name) targetUser.name = body.name;
  if (body.role) targetUser.role = body.role;

  return jsonResponse({
    id: targetUser.id,
    name: targetUser.name,
    email: targetUser.email,
    role: targetUser.role,
    company: targetUser.company,
    status: body.status || 'active'
  });
}

/* ================================================================
   SEED DATA ENDPOINT (Sprint 5 - Development Only)
   ================================================================ */

/**
 * POST /api/seed
 * Populate the D1 database with demo seed data for sales demonstrations.
 * No authentication required (development/demo only).
 * In production, this endpoint should be removed or protected.
 */
async function handleSeed(request, env) {
  if (request.method !== 'POST') {
    return jsonResponse({ error: 'Method not allowed' }, 405);
  }

  if (!env || !env.DB) {
    return jsonResponse({ error: 'Database not available. Seed requires D1 binding.' }, 500);
  }

  try {
    /* Seed company */
    await env.DB.prepare(
      "INSERT OR IGNORE INTO companies (id, name, slug, plan, settings) VALUES (1, 'Acme Manufacturing Inc.', 'acme', 'professional', '{\"industry\":\"manufacturing\",\"size\":\"50-100\",\"region\":\"Ontario, Canada\"}')"
    ).run();

    /* Seed 5 users */
    const userInserts = [
      { id: 1, email: 'admin@demo.com', name: 'Sarah Mitchell', role: 'admin' },
      { id: 2, email: 'manager@demo.com', name: 'James Rodriguez', role: 'manager' },
      { id: 3, email: 'employee@demo.com', name: 'Alex Chen', role: 'employee' },
      { id: 4, email: 'lisa@demo.com', name: 'Lisa Thompson', role: 'employee' },
      { id: 5, email: 'marcus@demo.com', name: 'Marcus Williams', role: 'employee' }
    ];

    for (const u of userInserts) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO users (id, company_id, email, password_hash, name, role, is_active) VALUES (?, 1, ?, ?, ?, ?, 1)'
      ).bind(u.id, u.email, 'password123', u.name, u.role).run();
    }

    /* Seed assessment results (8 total) */
    const assessments = [
      { id: 1, userId: 1, type: 'disc', score: 82.0, date: '2026-06-15T10:30:00Z',
        json: '{"dimensions":{"Dominance":78,"Influence":85,"Steadiness":62,"Conscientiousness":90},"primary_style":"C/I"}' },
      { id: 2, userId: 1, type: 'manager-readiness', score: 88.0, date: '2026-06-18T14:15:00Z',
        json: '{"dimensions":{"Communication":92,"Delegation":85,"Conflict Resolution":88,"Performance Management":90,"Strategic Thinking":84,"Team Development":91},"readiness_level":"Ready"}' },
      { id: 3, userId: 1, type: 'culture-fit', score: 91.0, date: '2026-06-20T09:45:00Z',
        json: '{"dimensions":{"Integrity":95,"Accountability":92,"Transparency":88,"Growth Mindset":90,"Innovation":86,"Persistence":93,"Love":94},"alignment":"Strong"}' },
      { id: 4, userId: 2, type: 'disc', score: 75.0, date: '2026-06-12T11:00:00Z',
        json: '{"dimensions":{"Dominance":88,"Influence":72,"Steadiness":58,"Conscientiousness":70},"primary_style":"D"}' },
      { id: 5, userId: 2, type: 'safety-competency', score: 94.0, date: '2026-06-14T08:30:00Z',
        json: '{"dimensions":{"Hazard Identification":96,"Emergency Procedures":92,"PPE Knowledge":98,"Incident Reporting":90,"Regulatory Awareness":88,"Safety Leadership":95},"competency_level":"Expert"}' },
      { id: 6, userId: 2, type: 'sales-aptitude', score: 72.0, date: '2026-06-22T16:00:00Z',
        json: '{"dimensions":{"Prospecting":68,"Relationship Building":74,"Needs Analysis":70,"Presentation Skills":78,"Negotiation":75,"Closing":65},"aptitude_level":"Developing"}' },
      { id: 7, userId: 3, type: 'disc', score: 68.0, date: '2026-06-25T13:20:00Z',
        json: '{"dimensions":{"Dominance":55,"Influence":60,"Steadiness":85,"Conscientiousness":72},"primary_style":"S"}' },
      { id: 8, userId: 3, type: 'culture-fit', score: 79.0, date: '2026-06-27T10:10:00Z',
        json: '{"dimensions":{"Integrity":88,"Accountability":82,"Transparency":72,"Growth Mindset":76,"Innovation":70,"Persistence":85,"Love":80},"alignment":"Good"}' }
    ];

    for (const a of assessments) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO assessment_results (id, user_id, company_id, assessment_type, score_json, total_score, completed_at) VALUES (?, ?, 1, ?, ?, ?, ?)'
      ).bind(a.id, a.userId, a.type, a.json, a.score, a.date).run();
    }

    /* Seed policy acknowledgments (21 total) */
    const policies = [
      'Workplace Harassment Policy (Ontario)', 'AI Use Policy', 'Working Alone Policy (Ontario)',
      'Health & Safety Policy (Ontario)', 'Social Media Policy', 'Travel & Expense Policy',
      'Personal Days Policy (Ontario)', 'Progressive Discipline Policy (Ontario)',
      'Remote Work Policy', 'Confidentiality & IP Policy'
    ];

    /* Sarah: all 10 */
    let policyId = 1;
    for (let i = 0; i < 10; i++) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES (?, 1, 1, ?, ?, ?, ?)'
      ).bind(policyId++, policies[i], '1.0', '2026-06-10T09:' + String(i * 5).padStart(2, '0') + ':00Z', '192.168.1.100').run();
    }
    /* James: 7 (indices 0-5 and 7) */
    const jamesPolicies = [0, 1, 2, 3, 4, 5, 7];
    for (const pi of jamesPolicies) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES (?, 2, 1, ?, ?, ?, ?)'
      ).bind(policyId++, policies[pi], '1.0', '2026-06-11T10:' + String(pi * 8).padStart(2, '0') + ':00Z', '192.168.1.101').run();
    }
    /* Alex: 3 (Harassment, AI Use, H&S) */
    const alexPolicies = [0, 1, 3];
    for (const pi of alexPolicies) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES (?, 3, 1, ?, ?, ?, ?)'
      ).bind(policyId++, policies[pi], '1.0', '2026-06-20T14:' + String(pi * 10).padStart(2, '0') + ':00Z', '192.168.1.102').run();
    }
    /* Lisa: 1 (Harassment only) */
    await env.DB.prepare(
      'INSERT OR IGNORE INTO policy_acknowledgments (id, user_id, company_id, policy_name, policy_version, acknowledged_at, ip_address) VALUES (?, 4, 1, ?, ?, ?, ?)'
    ).bind(policyId++, policies[0], '1.0', '2026-06-28T11:00:00Z', '192.168.1.103').run();

    /* Seed onboarding progress (2 users) */
    await env.DB.prepare(
      "INSERT OR IGNORE INTO onboarding_progress (id, user_id, company_id, playbook_type, phase, task_name, is_complete, assigned_to, notes) VALUES (1, 4, 1, 'manufacturing', '_tracker', '_tracker', 0, 'James Rodriguez', ?)"
    ).bind(JSON.stringify({
      items_completed_json: [
        'pre-start-1','pre-start-2','pre-start-3','pre-start-4','pre-start-5','pre-start-6','pre-start-7','pre-start-8',
        'day1-1','day1-2','day1-3','day1-4','day1-5','day1-6','day1-7','day1-8','day1-9','day1-10',
        'week1-1','week1-2','week1-3','week1-4','week1-5'
      ],
      signoffs_json: {
        'pre-start': { signed_by: 'James Rodriguez', signed_at: '2026-06-25T16:00:00Z', notes: 'All pre-start items completed.' },
        'day1': { signed_by: 'James Rodriguez', signed_at: '2026-06-28T17:30:00Z', notes: 'Orientation complete.' }
      },
      total_items: 50,
      started_at: '2026-06-24T08:00:00Z',
      updated_at: '2026-07-02T15:30:00Z'
    })).run();

    await env.DB.prepare(
      "INSERT OR IGNORE INTO onboarding_progress (id, user_id, company_id, playbook_type, phase, task_name, is_complete, assigned_to, notes) VALUES (2, 5, 1, 'general-smb', '_tracker', '_tracker', 0, 'Sarah Mitchell', ?)"
    ).bind(JSON.stringify({
      items_completed_json: ['pre-start-1','pre-start-2','pre-start-3','pre-start-4','pre-start-5','pre-start-6'],
      signoffs_json: {},
      total_items: 40,
      started_at: '2026-07-01T08:00:00Z',
      updated_at: '2026-07-03T11:00:00Z'
    })).run();

    /* Seed content access log */
    const accessLogs = [
      { id: 1, userId: 1, sop: 'SOP Master Template', action: 'download', date: '2026-06-10T08:30:00Z' },
      { id: 2, userId: 1, sop: 'Manufacturing SOP Pack', action: 'view', date: '2026-06-10T08:45:00Z' },
      { id: 3, userId: 1, sop: 'Manufacturing SOP Pack', action: 'download', date: '2026-06-10T08:46:00Z' },
      { id: 4, userId: 2, sop: 'Safety SOP Pack', action: 'download', date: '2026-06-11T10:00:00Z' },
      { id: 5, userId: 2, sop: 'Manufacturing Onboarding Playbook', action: 'download', date: '2026-06-24T07:45:00Z' },
      { id: 6, userId: 3, sop: 'AI Use Policy', action: 'view', date: '2026-06-20T14:05:00Z' },
      { id: 7, userId: 3, sop: 'Operations Roles (7 JDs)', action: 'download', date: '2026-06-22T09:30:00Z' },
      { id: 8, userId: 4, sop: 'Manufacturing Onboarding Playbook', action: 'view', date: '2026-06-28T08:00:00Z' },
      { id: 9, userId: 4, sop: 'Safety SOP Pack', action: 'view', date: '2026-06-28T08:20:00Z' },
      { id: 10, userId: 5, sop: 'General SMB Onboarding Playbook', action: 'download', date: '2026-07-01T08:10:00Z' },
      { id: 11, userId: 1, sop: 'Benchmarking Methodology Guide', action: 'view', date: '2026-07-02T11:00:00Z' },
      { id: 12, userId: 1, sop: 'Compensation Source Guide', action: 'download', date: '2026-07-02T11:15:00Z' }
    ];

    for (const log of accessLogs) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO sop_access_log (id, user_id, company_id, sop_name, action, accessed_at) VALUES (?, ?, 1, ?, ?, ?)'
      ).bind(log.id, log.userId, log.sop, log.action, log.date).run();
    }

    return jsonResponse({
      seeded: true,
      company: 'Acme Manufacturing Inc.',
      users: 5,
      assessments: assessments.length,
      policies: policyId - 1,
      onboarding: 2,
      access_logs: accessLogs.length
    });

  } catch (e) {
    console.error('Seed error:', e);
    return jsonResponse({ error: 'Seed failed: ' + e.message }, 500);
  }
}

/* ================================================================
   MAIN ROUTER
   ================================================================ */

export default {
  /**
   * Main fetch handler for the Cloudflare Worker.
   * Routes API requests and serves static assets.
   */
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    /* Handle CORS preflight for all API routes */
    if (request.method === 'OPTIONS' && path.startsWith('/api/')) {
      return handleOptions();
    }

    /* API Routes */
    if (path === '/api/auth/login') {
      return handleLogin(request);
    }

    if (path === '/api/auth/me') {
      return handleAuthMe(request);
    }

    if (path === '/api/dashboard') {
      return handleDashboard(request, env);
    }

    if (path === '/api/dashboard/activity') {
      return handleDashboardActivity(request, env);
    }

    /* Seed endpoint (Sprint 5 - development/demo only) */
    if (path === '/api/seed' && request.method === 'POST') {
      return handleSeed(request, env);
    }

    /* Assessment endpoints (Sprint 2) */
    if (path === '/api/assessments/results' && request.method === 'POST') {
      return handleSaveAssessmentResult(request, env);
    }

    if (path === '/api/assessments/results' && request.method === 'GET') {
      return handleGetAssessmentResults(request, env);
    }

    if (path === '/api/assessments/team') {
      return handleGetTeamResults(request, env);
    }

    /* Content Library endpoints (Sprint 3) */
    if (path === '/api/library/access' && request.method === 'POST') {
      return handleLibraryAccess(request, env);
    }

    if (path === '/api/library/stats') {
      return handleLibraryStats(request, env);
    }

    /* Policy Acknowledgment endpoints (Sprint 3) */
    if (path === '/api/policies/acknowledge' && request.method === 'POST') {
      return handlePolicyAcknowledge(request, env);
    }

    if (path === '/api/policies/status') {
      return handlePolicyStatus(request, env);
    }

    if (path === '/api/policies/team') {
      return handlePolicyTeam(request, env);
    }

    /* Onboarding endpoints (Sprint 4) */
    if (path === '/api/onboarding/start' && request.method === 'POST') {
      return handleOnboardingStart(request, env);
    }

    if (path === '/api/onboarding/me' && request.method === 'GET') {
      return handleOnboardingMe(request, env);
    }

    if (path === '/api/onboarding/update' && request.method === 'PUT') {
      return handleOnboardingUpdate(request, env);
    }

    if (path === '/api/onboarding/team' && request.method === 'GET') {
      return handleOnboardingTeam(request, env);
    }

    if (path === '/api/onboarding/signoff' && request.method === 'POST') {
      return handleOnboardingSignoff(request, env);
    }

    /* User Management endpoints (Sprint 4) */
    if (path === '/api/users' && request.method === 'GET') {
      return handleGetUsers(request, env);
    }

    if (path === '/api/users' && request.method === 'POST') {
      return handleCreateUser(request, env);
    }

    /* Match /api/users/:id for PUT */
    const userMatch = path.match(/^\/api\/users\/(\d+)$/);
    if (userMatch && request.method === 'PUT') {
      return handleUpdateUser(request, env, userMatch[1]);
    }

    /* Catch-all for unknown API routes */
    if (path.startsWith('/api/')) {
      return jsonResponse({
        error: 'Not found',
        message: 'The requested API endpoint does not exist.',
        path: path
      }, 404);
    }

    /* For non-API routes, Cloudflare Pages serves static assets from /public/ */
    /* This catch-all returns index.html for SPA routing */
    return env.ASSETS
      ? env.ASSETS.fetch(request)
      : jsonResponse({ error: 'Static assets not configured.' }, 500);
  }
};
