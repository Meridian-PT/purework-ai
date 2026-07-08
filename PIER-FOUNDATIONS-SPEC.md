# Pier Foundations HR Module - Integration Spec

**Source**: Tether via CC #pf-hr (2026-07-08)
**Status**: Confirmed, building Phase 1

## Architecture

- HR is an **iframe module** inside the Pier Foundations portal shell
- Deploy as own Cloudflare Pages project, version independently
- Shell embeds via routed iframe with postMessage handshake

## Auth Model (CORRECTED per Peter 2026-07-08)

~~postMessage handshake~~ NOT USED. The shell uses a **session cookie** (`pf_auth_token`).

```
Deploy: same-origin path under pf-platform (e.g. /hr/)
Auth: pf_auth_token cookie, inherited automatically
RBAC: enforced at platform/functions layer
```

Module does NOT need shell-repo write access. Tether (integration owner) handles wiring with Peter (nav entry + same-origin serving behind review gate).

## Data Boundaries

- HR owns: candidates, applications, interviews, onboarding, compliance, employee records, PTO, performance
- CRM (Prodigy) owns: contacts, deals, pipeline
- When CRM contact becomes hire: CRM emits referral -> HR creates candidate with read-only `sourceContactId` back to CRM
- HR never edits CRM records
- HR never queries SharePoint directly (shell owns shared records)

## Design Tokens

```css
:root {
  --pf-blue:    #2a93c1;  /* primary accent, links, section labels */
  --pf-orange:  #f1420b;  /* PureBrain orange, primary CTA / emphasis */
  --pf-green:   #10b981;  /* success / done */
  --pf-gold:    #D4A574;  /* handoff / tertiary */
  --pf-red:     #ef4444;  /* error / no-go / alert */

  --pf-bg:      #0b0f14;
  --pf-surface: #131820;
  --pf-card:    #171e28;
  --pf-border:  #1e2a38;
  --pf-text:    #e8ecf0;
  --pf-muted:   #7a8a9e;

  /* Light surface (SPA content area - confirm vs app) */
  --pf-bg-light:     #ffffff;
  --pf-card-light:   #f7f9fb;
  --pf-border-light: #e3e8ee;
  --pf-text-light:   #0b0f14;
  --pf-muted-light:  #5a6b7e;
}
```

## Typography

- Font: system stack (-apple-system, 'Segoe UI', sans-serif)
- Line-height: 1.7
- Section labels: .65rem / 700 / letter-spacing .2em / uppercase / orange or blue
- Titles: clamp(1.2rem, 2.8vw, 1.6rem) / 700
- Body: .82-.85rem, muted for secondary

## Components

- **Cards**: --pf-card bg, 1px --pf-border, radius 10px, pad 1.3-1.6rem, 3px full-height LEFT ACCENT BAR (::before) colored by state
- **Chips**: radius 3px, .6rem uppercase, letter-spacing 1.5px, weight 600-700, bg = accent at 8-10% opacity
- **Status pills**: 18px square, 1.5px border, radius 4px (pending=muted, in-progress=orange, done=green)
- **Grids**: repeat(auto-fit, minmax(280px, 1fr)), gap .8rem

## Guardrails

- NO top nav (shell owns chrome)
- NO em dashes in any label or copy
- NO spaced commas in any label or copy
- Status pills must be IDENTICAL across CRM/HR/Field Ops

## Phase 1 Scope

1. Employee Records & Self-Service
2. Onboarding Workflow
3. Policy Library + Acknowledgment
4. PTO / Time Off Management

## Waiting On

- [ ] Mike: Pier Foundations state (headcount, jurisdictions, existing tools)
- [x] Tether: Integration spec (received)
- [x] Tether: Design tokens (received)
- [ ] Tether: Portal repo access / component template
