# Pure Work AI -- Engineering Handoff

## Project Overview

**Pure Work AI** is an AI-powered workforce operating system built for Pure Technology. It provides a single platform for employee assessments, training, onboarding, compliance, and knowledge management.

- **Target Users**: HR administrators, managers, and employees at SMBs (50-500 employees)
- **Industries**: Manufacturing, professional services, tech/SaaS, and general SMB
- **Current State**: MVP complete (5 sprints), ready for staging deployment and sales demos
- **Demo URL**: TBD (deploy to Cloudflare Pages)

## Architecture

```
Frontend: Cloudflare Pages (static HTML/CSS/JS)
Backend:  Cloudflare Workers (serverless API)
Database: Cloudflare D1 (SQLite-compatible, edge-deployed)
CDN:      Google Fonts (Inter typeface)
```

**Key Design Decisions:**
- **Single Page Application** with hash-based routing (`#dashboard`, `#assessments`, etc.)
- **No build step** -- no npm, no webpack, no framework dependencies. Pure HTML/CSS/JS.
- **No external JS libraries** -- everything is hand-rolled for zero-dependency deployment
- **Cloudflare-native** -- Workers for API, D1 for database, Pages for static assets
- **Dark theme** -- professional dark UI with Inter font, CSS custom properties design system

## File Structure

```
purework-ai/
├── public/
│   ├── index.html              -- Main SPA (all pages, routing, state management)
│   ├── landing.html            -- Prospect-facing landing/sales page
│   ├── content-manifest.json   -- Maps 34 content files to UI categories
│   ├── assessments/            -- 8 standalone HTML assessment applications
│   │   ├── disc.html
│   │   ├── bigfive.html
│   │   ├── culture-fit.html
│   │   ├── manager-readiness.html
│   │   ├── safety-competency.html
│   │   ├── sales-aptitude.html
│   │   ├── customer-service.html
│   │   └── workstyle.html
│   └── content/                -- 34 .docx content files across 6 categories
│       ├── sop-templates/      -- 5 SOP packs (Master, Manufacturing, Prof Services, Tech, Safety)
│       ├── policies/           -- 10 workplace policies (Ontario + Universal)
│       ├── job-descriptions/   -- 6 JD packs (27 total job descriptions)
│       ├── training/           -- 5 training programs (Manager Dev, Safety, DISC, etc.)
│       ├── onboarding/         -- 4 onboarding playbooks (Manufacturing, Prof, Tech, General)
│       └── comp-benchmarking/  -- 4 compensation benchmarking docs
├── src/
│   └── worker.js               -- API backend (22 endpoints, ~1,580 lines)
├── schema.sql                  -- D1 database schema (7 tables with indexes)
├── seed.sql                    -- Demo seed data for sales demonstrations
├── wrangler.toml               -- Cloudflare deployment configuration
├── HANDOFF.md                  -- This document
└── DEMO-SCRIPT.md              -- 3-minute sales demo walkthrough
```

## Authentication

**Current Implementation (MVP):**

1. User submits email + password via POST `/api/auth/login`
2. Server matches against hardcoded `DEMO_USERS` array (5 demo users)
3. On match, server creates a token: `btoa(JSON.stringify({ id, email, name, role, company, exp }))`
4. Token is returned to client and stored in `localStorage`
5. Every subsequent API call includes `Authorization: Bearer <token>` header
6. Server decodes token with `atob()`, checks expiry (24h), validates required fields

**Security Notes (MVP Limitations):**
- Tokens are base64-encoded, NOT signed (no JWT). Anyone can forge a token.
- Passwords are compared as plaintext strings (no hashing)
- Token stored in localStorage (XSS-vulnerable in production)
- No rate limiting, no CSRF protection, no brute-force protection

**Production Upgrade Path:**
1. Replace base64 tokens with signed JWTs (use `@tsndr/cloudflare-worker-jwt` or similar)
2. Hash passwords with bcrypt before storage
3. Move tokens to httpOnly cookies with SameSite=Strict
4. Add rate limiting via Cloudflare Rate Limiting rules
5. Add CSRF tokens for state-changing operations

## API Endpoints

### Authentication
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | No | Authenticate with email/password, returns token |
| GET | `/api/auth/me` | Yes | Validate token and return current user info |

### Dashboard
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/dashboard` | Yes | Dashboard metrics (assessments, policies, onboarding counts) |
| GET | `/api/dashboard/activity` | Yes | Recent activity feed across all modules |

### Assessments (Sprint 2)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/assessments/results` | Yes | Save or update assessment result for current user |
| GET | `/api/assessments/results` | Yes | Get current user's assessment results |
| GET | `/api/assessments/team` | Admin/Mgr | Get team-wide assessment results |

### Content Library (Sprint 3)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/library/access` | Yes | Log content view or download |
| GET | `/api/library/stats` | Admin/Mgr | Get content access statistics |

### Policy Acknowledgment (Sprint 3)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/policies/acknowledge` | Yes | Acknowledge a policy (creates audit trail) |
| GET | `/api/policies/status` | Yes | Get current user's policy acknowledgments |
| GET | `/api/policies/team` | Admin/Mgr | Get team-wide policy compliance status |

### Onboarding (Sprint 4)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/onboarding/start` | Admin/Mgr | Start onboarding for a user with a playbook |
| GET | `/api/onboarding/me` | Yes | Get current user's onboarding progress |
| PUT | `/api/onboarding/update` | Yes | Update onboarding item completion |
| GET | `/api/onboarding/team` | Admin/Mgr | Get all active onboarding progress |
| POST | `/api/onboarding/signoff` | Admin/Mgr | Record supervisor milestone sign-off |

### User Management (Sprint 4)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/users` | Admin | List all company users |
| POST | `/api/users` | Admin | Create new user |
| PUT | `/api/users/:id` | Admin | Update user details |

### Development (Sprint 5)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/seed` | No | Seed demo data into D1 (remove in production) |

## Database Schema

The database uses 7 tables with a multi-tenant design (all tables include `company_id`).

**Reference**: `schema.sql` for complete CREATE TABLE statements.

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `companies` | Multi-tenant root | id, name, slug, plan, settings |
| `users` | Authentication and identity | id, company_id, email, password_hash, name, role |
| `assessment_results` | Completed assessment data | user_id, assessment_type, score_json, total_score |
| `policy_acknowledgments` | Policy sign-off audit trail | user_id, policy_name, policy_version, acknowledged_at |
| `onboarding_progress` | New hire onboarding tracking | user_id, playbook_type, phase, task_name, notes (JSON) |
| `sop_access_log` | Content view/download tracking | user_id, sop_name, action, accessed_at |
| `training_completions` | Training module completion | user_id, training_name, score, passed |

**Onboarding Tracker Pattern (Sprint 4):**
The `onboarding_progress` table uses a tracker row pattern where `phase='_tracker'` and `task_name='_tracker'`. The `notes` column stores a JSON object:
```json
{
  "items_completed_json": ["item-id-1", "item-id-2"],
  "signoffs_json": { "phase-name": { "signed_by": "...", "signed_at": "...", "notes": "..." } },
  "total_items": 50,
  "started_at": "2026-06-24T08:00:00Z",
  "updated_at": "2026-07-02T15:30:00Z"
}
```

## Demo Credentials

| Email | Password | Name | Role | Description |
|-------|----------|------|------|-------------|
| admin@demo.com | password123 | Sarah Mitchell | Admin | Full access, 3 assessments done, all policies signed |
| manager@demo.com | password123 | James Rodriguez | Manager | Supervisor access, 3 assessments done, 7/10 policies |
| employee@demo.com | password123 | Alex Chen | Employee | Basic access, 2 assessments done, 3/10 policies |
| lisa@demo.com | password123 | Lisa Thompson | Employee | Manufacturing onboarding at 45%, 1/10 policies |
| marcus@demo.com | password123 | Marcus Williams | Employee | General onboarding at 15%, 0 policies signed |

## Deployment

### Prerequisites
- Cloudflare account with Workers and Pages enabled
- Wrangler CLI installed (`npm install -g wrangler`)
- Authenticated with Cloudflare (`wrangler login`)

### First-Time Setup

```bash
# 1. Create D1 database
wrangler d1 create purework-db
# Copy the database_id from output into wrangler.toml

# 2. Apply schema
wrangler d1 execute purework-db --file=schema.sql

# 3. Seed demo data
wrangler d1 execute purework-db --file=seed.sql

# 4. Deploy to Pages
wrangler pages deploy ./public --project-name purework-mvp-staging
```

### For Pages Functions (API via Pages)

If deploying as a Cloudflare Pages project with Functions (recommended for unified deployment):

```bash
# Move worker to Pages Functions directory
mkdir -p functions/api
cp src/worker.js functions/api/[[path]].js

# Adjust the export to match Pages Functions format:
# export async function onRequest(context) {
#   return await handleRequest(context.request, context.env);
# }
```

### Subsequent Deployments

```bash
# Deploy updated frontend
wrangler pages deploy ./public --project-name purework-mvp-staging

# Apply schema changes
wrangler d1 execute purework-db --file=schema.sql

# Re-seed if needed
wrangler d1 execute purework-db --file=seed.sql
```

## What's Built (Sprint by Sprint)

### Sprint 1: Foundation
- Login page with animated UI
- Base64 token authentication (create, validate, extract)
- SPA shell with sidebar navigation, header, and hash-based routing
- Dashboard page structure with 4 metric cards
- Responsive layout with CSS custom properties design system
- CORS handling for all API routes

### Sprint 2: Assessment Center
- 8 standalone HTML assessment applications (DISC, Big Five, Culture Fit, Manager Readiness, Safety Competency, Sales Aptitude, Customer Service, Workstyle)
- Each assessment: multi-question flow, auto-scoring, radar chart visualization, detailed results
- iframe embedding with postMessage communication (assessment -> parent SPA)
- Score persistence to D1 database (save/update pattern)
- Results history page with scores and completion dates
- Team-wide assessment analytics (admin/manager view)

### Sprint 3: Content Library & Policy Acknowledgment
- Content library with 34 documents across 6 categories (SOPs, Policies, JDs, Training, Onboarding, Comp)
- Category tab navigation with document counts
- Search functionality across all content items
- Document download tracking (view/download logged to D1)
- Content access statistics for admin/manager
- Policy acknowledgment system with digital signature
- Policy audit trail (who signed what, when, from where)
- Team policy compliance dashboard (admin/manager view)

### Sprint 4: Onboarding & Admin
- Onboarding tracker with 4 industry-specific playbooks (Manufacturing, Professional Services, Tech/SaaS, General SMB)
- Interactive multi-phase checklists (Pre-Start, Day 1, Week 1, Month 1, Month 2-3)
- Supervisor sign-off at milestones with notes
- Progress percentage tracking and visual indicators
- Admin dashboard with company-wide metrics
- User management (create, update, list users)
- Team onboarding overview (all active onboardings)
- Activity feed combining assessments, policies, onboarding, and content access

### Sprint 5: MVP Launch
- Landing page for prospects (standalone marketing page)
- Demo seed data (5 users, 8 assessments, 21 policy acks, 2 onboarding tracks, 12 access logs)
- Seed API endpoint for easy demo reset
- Engineering handoff documentation
- Sales demo script

## What's NOT Built (Post-MVP)

### Security & Auth
- Real password hashing (bcrypt/argon2)
- Signed JWTs (currently base64 tokens)
- CSRF protection
- Rate limiting
- Password reset flow
- Email verification on user creation
- SSO / OAuth (Google, Microsoft)

### Features
- Email notifications (policy reminders, onboarding nudges)
- File upload for custom content (admin content management)
- AI-powered SOP search (RAG pipeline with embeddings)
- Payroll integration
- Performance review module
- Pulse surveys
- Compensation management (beyond benchmarking docs)
- Employee self-service (profile editing, PTO requests)

### Infrastructure
- Mobile native app
- Real-time collaboration (WebSocket)
- Audit logging beyond policy acknowledgments
- Multi-language support (i18n)
- Automated testing suite
- CI/CD pipeline
- Monitoring and alerting
- Backup and disaster recovery

## Known Limitations

1. **Auth tokens are not signed** -- base64 encoding only. Any client can forge tokens by constructing the correct JSON payload. Production requires JWT with HMAC or RSA signing.

2. **No rate limiting** -- API endpoints accept unlimited requests. Add Cloudflare Rate Limiting rules or implement token bucket in Workers.

3. **No CSRF protection** -- State-changing operations (POST, PUT) have no CSRF tokens. Risk is mitigated by Bearer token auth but should be addressed for cookie-based auth.

4. **Password reset not built** -- Users cannot recover forgotten passwords. Requires email integration.

5. **Content files are static** -- The 34 .docx files are deployed as static assets. There is no admin upload UI. Adding new content requires redeployment.

6. **Demo users are hardcoded** -- The `DEMO_USERS` array in worker.js is used for authentication, separate from D1 data. Production should authenticate against the database.

7. **Single-tenant demo** -- While the schema supports multi-tenancy (company_id on every table), the demo data and login flow are single-company.

8. **No code splitting** -- The entire SPA is one 4,900+ line HTML file. Production should split into modules for faster loading.

9. **Assessment iframe security** -- Assessment HTML files are loaded in iframes with full access. Production should sandbox these more strictly.

10. **No automated tests** -- No unit tests, integration tests, or E2E tests exist. Recommended to add Playwright tests for critical paths.

## Recommended Next Steps

### Phase 1: Security Hardening (1-2 weeks)
1. Replace base64 auth with proper JWT signing + bcrypt password hashing
2. Move auth tokens to httpOnly cookies with SameSite=Strict
3. Add Cloudflare Rate Limiting rules (10 req/min for login, 60 req/min for API)
4. Remove `/api/seed` endpoint from production deployment
5. Add Content-Security-Policy headers

### Phase 2: Email Integration (1 week)
1. Integrate Brevo or SendGrid for transactional email
2. Policy reminder notifications (for unsigned policies)
3. Onboarding milestone notifications
4. Welcome emails for new user accounts
5. Password reset flow

### Phase 3: Content Management (2 weeks)
1. Build admin content upload UI with drag-and-drop
2. Store uploaded content in Cloudflare R2 (object storage)
3. Dynamic content-manifest.json generation
4. Content versioning and archiving

### Phase 4: AI Features (2-3 weeks)
1. RAG pipeline for SOP search (embed content with OpenAI/Anthropic, store in Vectorize)
2. AI-generated assessment summaries
3. Smart onboarding recommendations based on role and industry
4. Policy Q&A chatbot

### Phase 5: Enterprise Features (3-4 weeks)
1. SSO integration (Google Workspace, Microsoft Entra ID)
2. Advanced reporting and analytics dashboard
3. Custom assessment builder
4. API for third-party integrations
5. Mobile-optimized responsive pass

## Technology Reference

| Component | Technology | Version/Notes |
|-----------|-----------|---------------|
| Frontend | HTML/CSS/JS | No framework, no build step |
| Fonts | Google Fonts (Inter) | Weights: 300, 400, 500, 600, 700 |
| Backend | Cloudflare Workers | ES modules format (`export default { fetch }`) |
| Database | Cloudflare D1 | SQLite-compatible, `env.DB.prepare().bind().run()` |
| Static Hosting | Cloudflare Pages | Serves from `./public/` |
| Deployment | Wrangler CLI | `wrangler pages deploy`, `wrangler d1 execute` |
| Config | wrangler.toml | D1 binding name: `DB`, site bucket: `./public` |
