# OpenClaw Setup Guide — Andrey's two-agent assistant

**Purpose:** Bring up the local OpenClaw gateway with two segregated agents (Atlas for EPAM, Sophia for Verdaca). Make it once, never redo.

**Created:** 2026-05-06
**Last reviewed:** 2026-05-06

---

## Step 0 — ⚠️ ROTATE LEAKED API KEYS (DO THIS FIRST)

On 2026-05-06 you pasted two API keys into a Claude chat:
- EPAM DIAL: prefix `dial-fxbas...` (revoke at EPAM AI Proxy admin portal)
- OpenRouter: prefix `sk-or-v1-f4cd...` (revoke at https://openrouter.ai/keys)

**Both are now in the chat transcript. Both are compromised. Both must be revoked and replaced before you fill in `secrets.json`.**

```
□ Revoked EPAM DIAL key (EPM-GPT-Andrey_Popov_PERSONAL)
□ Issued new EPAM DIAL key
□ Revoked OpenRouter key
□ Issued new OpenRouter key
```

Do NOT proceed past this step until both checkboxes are done.

---

## Step 1 — Fill in `~/.openclaw/secrets.json`

Path: `C:\Users\AndreyPopov\.openclaw\secrets.json`

The file is pre-staged with placeholders. Replace each `PASTE_..._HERE` with the actual rotated value:

```json
{
  "providers": {
    "epam_dial": { "apiKey": "<NEW EPAM DIAL key>" },
    "openrouter": { "apiKey": "<NEW OpenRouter key>" }
  },
  "channels": {
    "discord": { "token": "<configure at Phase 2 close>" },
    "github":  { "token": "<GitHub PAT>" },
    "gmail":   { "oauth":  "<configure at Phase 2 close>" }
  },
  "gateway": {
    "authToken": "<random 48 chars>"
  }
}
```

**Generate the gateway authToken** (PowerShell):

```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
```

Paste the output as `gateway.authToken`.

**GitHub PAT** (after the rotated keys are in):
1. https://github.com/settings/tokens → Fine-grained personal access token
2. Resource owner: your personal account (later, the Verdaca org)
3. Scopes: Contents (RW), Issues (RW), Pull requests (RW), Metadata (R)
4. Expiration: 90 days
5. Paste into `channels.github.token`

**Discord + Gmail tokens:** Leave the placeholders. Fill them after Phase 2 close when you register the domain and create the Verdaca Discord server (see `_bmad-output/planning-artifacts/Verdaca/domain-and-email-plan.md`).

**Lock down the file:**

```powershell
icacls C:\Users\AndreyPopov\.openclaw\secrets.json /inheritance:r /grant:r AndreyPopov:F
```

This removes inherited ACLs and grants only your user account full access.

---

## Step 2 — Validate the config

```powershell
openclaw crestodian --message "validate config"
```

Expected: zero errors. Warnings about ms-teams / ms-outlook channels being unconfigured are OK — those are intentionally pending EPAM Security clearance.

If there are errors, run `openclaw crestodian --message "models"` to see what providers/models OpenClaw recognizes, and fix the JSON5.

---

## Step 3 — Start the gateway

```powershell
openclaw crestodian --message "start gateway" --yes
```

Expected outcome:
- Gateway listening on `ws://127.0.0.1:18789`
- Dashboard at `http://127.0.0.1:18789` (auth with the gateway authToken)
- Both agents (`epam-work`, `verdaca`) loaded and idle

Verify:
```powershell
openclaw crestodian --message "agents list"
```

Should show:
```
verdaca   default   Sophia   🌿   loaded
epam-work           Atlas    🛡️   loaded (no channels bound)
```

---

## Step 4 — Smoke test (Verdaca side)

The Verdaca agent has CLI binding by default. Test it:

```powershell
openclaw agent --agent verdaca --message "Hello, who are you and what's your scope?"
```

Expected: Sophia introduces herself, summarizes scope (calendar, content, Discord, CRM, GitHub), confirms segregation rule.

If Sophia mentions EPAM, Anthropic API, or any non-OpenRouter model → **STOP**. The segregation rule has leaked. Open `workspace-verdaca/AGENTS.md` and check that section §0 is intact.

If Sophia uses "Nuagio" or quotes a metric without the A4 caveat → **STOP**. Brand lock has leaked.

---

## Step 5 — DO NOT activate the EPAM agent yet

The EPAM agent (Atlas) is loaded but has no channel bindings. Activating it requires:

1. Send the EPAM Security clearance request — see `docs/epam-security-clearance-email-draft.md` for the draft email
2. Receive written confirmation from EPAM IT/InfoSec
3. Add the confirmation as a file: `~/.openclaw/workspace-epam/clearance-on-file.md` with the date and reviewer name
4. Configure ms-teams + ms-outlook channels in `openclaw.json5`

Until step 4, Atlas refuses to operate (see `workspace-epam/AGENTS.md` §0).

---

## Step 6 — Activate Verdaca channels (timing: Phase 2 close)

Per the Phase 1 close memory, domain registration is sequenced for "post Phase 2 close, after substrate v1.0." When that day arrives:

1. Register `verdaca.com` at Cloudflare Registrar (~$9.15/yr) — see domain plan doc
2. Set up Google Workspace Business Starter ($7/mo) — see domain plan doc
3. Create the Verdaca Discord server
4. Configure GitHub org for Verdaca
5. Fill in `secrets.json` for discord + github + gmail
6. Update `bindings` in `openclaw.json5` to enable the Verdaca channels
7. Restart gateway: `openclaw crestodian --message "restart gateway" --yes`

---

## Operational notes

### Daily

- Sophia auto-resets after 60 min idle (per `session.reset` config). Atlas resets daily at 04:00.
- Audit logs at `~/.openclaw/audit/` — review weekly.
- Drafts live in `~/.openclaw/workspace-{epam,verdaca}/drafts/YYYY-MM-DD/`.

### Weekly

- Skim `audit/verdaca-YYYY-MM-DD.jsonl` for any unmapped placeholders (= redaction misses) — fix the prompt template if pattern emerges.
- Skim `workspace-verdaca/crm/contacts.json` for follow-up reminders Sophia surfaced.

### Monthly

- Review OpenRouter rate-limit usage (free tier — they may have changed policies).
- Review EPAM DIAL spend (should stay well under $100/mo with draft-only mode).
- Rotate gateway authToken if you've shared the dashboard URL with anyone.

### Quarterly (next: 2026-08-06)

- Review pinned model snapshots:
  - `inclusionai/ling-2.6-1t:free` → check if 3.x is out
  - `minimax/minimax-m2.5:free` → M2.7 already exists; evaluate
  - `openai/gpt-oss-120b:free` → check for newer OpenAI open release
  - `gpt-4o-mini-2024-07-18` → check DIAL catalog
- Rotate OpenRouter + EPAM DIAL keys regardless of breach status.

---

## Troubleshooting

### "Gateway: not reachable at ws://127.0.0.1:18789"

The user's first OpenClaw log showed this. Cause: gateway not started. Fix: `openclaw crestodian --message "start gateway" --yes`.

### "Config: missing"

Crestodian's first message indicates `~/.openclaw/openclaw.json5` not found. The setup script in this guide creates that file. Verify with: `Test-Path C:\Users\AndreyPopov\.openclaw\openclaw.json5`.

### Agent uses wrong model

If Sophia ever calls `epam_dial/*` or Atlas ever calls `openrouter/*`, the segregation has been compromised at the OpenClaw config layer. Investigate immediately:
1. `openclaw crestodian --message "validate config"` to confirm config is intact
2. Check `audit/{agent}-YYYY-MM-DD.jsonl` for the offending call
3. If the misroute happened, halt the gateway, fix `openclaw.json5`, restart

### Redaction skill not invoked

If you find an audit log entry where Sophia called a free-tier model with raw PII (no redaction event before), this is a discipline failure. Update `workspace-verdaca/AGENTS.md` §5 with a stronger trigger pattern, and update `skills/redaction-layer/SKILL.md` "When to invoke" with the specific pattern that was missed.

### A4 caveat missing in published content

If a metric ever ships without "(internal scoring; A4 deferred)":
1. Halt all auto-publish
2. Audit recent posts for similar misses
3. Update `workspace-verdaca/AGENTS.md` §2 with the specific phrasing pattern that slipped through
4. Re-test with: `openclaw agent --agent verdaca --message "Draft a LinkedIn post claiming Verdaca delivered +47% improvement"` → output MUST include caveat

---

## Files this setup created

| Path | Purpose |
|---|---|
| `~/.openclaw/openclaw.json5` | Gateway + agents + bindings + provider segregation |
| `~/.openclaw/secrets.json` | All API keys + tokens (placeholder; fill after rotation) |
| `~/.openclaw/workspace-epam/AGENTS.md` | Atlas operational rules + segregation + draft-only enforcement |
| `~/.openclaw/workspace-epam/SOUL.md` | Atlas voice (concise, professional, EPAM-tone-aware) |
| `~/.openclaw/workspace-verdaca/AGENTS.md` | Sophia operational rules + brand lock + A4 caveat + tier routing |
| `~/.openclaw/workspace-verdaca/SOUL.md` | Sophia voice (interim until 3 pillars from `docs/18.04.2026.md` are pasted) |
| `~/.openclaw/workspace-verdaca/skills/redaction-layer/SKILL.md` | PII redaction skill (best-effort agent-side) |
| `docs/openclaw-setup-guide.md` | This file |
| `docs/epam-security-clearance-email-draft.md` | Email draft to EPAM IT/InfoSec |
| `_bmad-output/planning-artifacts/Verdaca/domain-and-email-plan.md` | Cloudflare + Google Workspace plan for Phase 2 close |

---

## What's NOT in this setup yet (future work)

- Programmatic redaction proxy (Stage 7 debt ledger item)
- LinkedIn auto-post via Make.com (configure once Verdaca LinkedIn page exists)
- Buffer integration (optional, only if Make.com proves insufficient)
- EPAM Teams / Outlook channel wiring (blocked on Security clearance)
- Verdaca Discord server (post Phase 2 close)
- Verdaca Gmail / Google Calendar (post domain registration)
- Sophia 3-pillars voice canonical paste into SOUL.md (Andrey to do from `docs/18.04.2026.md` Round 2)

---

## Single-page summary (print this)

```
╔════════════════════════════════════════════════════════════════╗
║  OPENCLAW STATE — quick check                                  ║
║                                                                ║
║  Gateway:    ws://127.0.0.1:18789                              ║
║  Dashboard:  http://127.0.0.1:18789                            ║
║  Config:     ~/.openclaw/openclaw.json5                        ║
║  Secrets:    ~/.openclaw/secrets.json (locked, user-only)      ║
║  Audit:      ~/.openclaw/audit/                                ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐  ║
║  │ epam-work (Atlas) 🛡️                                     │  ║
║  │   Provider:  EPAM DIAL only ($100/mo)                    │  ║
║  │   Mode:      draft-only (sessions_send DENIED)           │  ║
║  │   Channels:  ms-teams, ms-outlook (PENDING CLEARANCE)    │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐  ║
║  │ verdaca (Sophia) 🌿                                       │  ║
║  │   Provider:  OpenRouter free cascade                     │  ║
║  │   Models:    Ling-2.6-1T (planner)                       │  ║
║  │              MiniMax M2.5 (executor)                     │  ║
║  │              gpt-oss-120b (critical)                     │  ║
║  │   Mode:      autonomy with guardrails                    │  ║
║  │   Channels:  discord, github, gmail (post Phase 2)       │  ║
║  │   Skills:    redaction-layer (mandatory on PII)          │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  HARD RULES (never violate):                                   ║
║   • EPAM DIAL ↔ epam-work agent ONLY                           ║
║   • OpenRouter ↔ verdaca agent ONLY                            ║
║   • Brand: Verdaca (Nuagio = HALT)                             ║
║   • Metrics: must carry "(internal scoring; A4 deferred)"      ║
║   • Verdaca framing: CLI/package, NOT hosted API               ║
║   • Redaction skill: mandatory before free-tier PII calls      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```
