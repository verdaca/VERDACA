# EPAM AI Special Approval Request — Email Draft

**Purpose:** Submit a Special Approval request to **WFTAICompliance@epam.com** under EPAM's *Mandatory Process Guidelines — Acceptable Use of AI at EPAM*, **Section C — Configuring an AI Module or AI Tool for Clients or EPAM — Special Approvals**, for running a locally-hosted AI assistant (OpenClaw) that reads MS Teams + Outlook in draft-only mode and routes inference exclusively through the corporate EPAM DIAL endpoint.

**Why this matters:** Without written approval, wiring the EPAM-side agent (Atlas) to corporate channels would be a Section-C policy non-compliance. Atlas is configured to refuse activation until the approval file is on disk (`~/.openclaw/workspace-epam/clearance-on-file.md`).

**Send to:** `WFTAICompliance@epam.com`
**CC:** Your line manager.

**Policy reference:** EPAM KB → *Acceptable Use of AI at EPAM* → Section C *(`kb.epam.com/pages/viewpage.action?pageId=2781613369&spaceKey=EPMCOECGAM`)*.

**Tone:** Formal, specific, demonstrates that the proposed configuration already satisfies the spirit of Section C (DIAL-only inference, draft-only execution, audit logging, local-only operation). Not asking for permission to do something risky — describing a controlled, policy-aligned configuration that needs the formal Section-C sign-off.

**Note for Andrey before sending:** The body below is a *first-pass* draft built from the URL itself (which referenced Section C). The actual EPAM policy page is auth-gated and I couldn't read it. **Before you send, paste the Section-C content + any required submission template/questionnaire from the KB page into this conversation** — I'll incorporate the exact field names, mandatory disclosures, and any approval-form fields the policy requires. The draft below is structurally complete but the specific questions Section C asks may need to be answered verbatim.

---

## Draft email — copy-paste below the line

---

**To:** WFTAICompliance@epam.com
**CC:** [your line manager]
**Subject:** Section C Special Approval request — local AI Module (OpenClaw + DIAL) for personal productivity, draft-only Teams/Outlook access

Hello WFT AI Compliance team,

I am submitting a Special Approval request under the *Mandatory Process Guidelines — Acceptable Use of AI at EPAM*, **Section C — Configuring an AI Module or AI Tool for Clients or EPAM — Special Approvals**, for a locally-hosted AI Module I have configured for personal productivity on my EPAM-managed workstation.

The configuration is described in full below. I have already aligned the design with what I believe Section C expects (DIAL-only inference, draft-only enforcement, no external egress, full audit), but I want your formal sign-off before activating the module against any real corporate data.

### 1. AI Module summary

- **Tool:** OpenClaw (open-source: https://github.com/openclaw/openclaw — npm-installed CLI agent runtime)
- **Hosting:** Locally on my EPAM-managed laptop only. No cloud component, no remote server, no external sharing of state.
- **Purpose:** A single agent ("Atlas") that helps me triage MS Teams threads + Outlook mail more efficiently — reads my own messages, summarizes unreads, drafts reply text into a local workspace folder, and stops there. **I review every draft and copy-paste manually if I want to send.** The module has **no send capability**.

### 2. AI Module compliance properties (mapped to my reading of Section C)

| Section C concern | How this configuration addresses it |
|---|---|
| **Inference routing** | All LLM calls go *only* to **EPAM DIAL** (`https://ai-proxy.lab.epam.com`), authenticated with my personal `EPM-GPT-Andrey_Popov_PERSONAL` key under the standard $100/mo budget. **Zero traffic to non-EPAM model providers** (no OpenAI direct, no Anthropic direct, no OpenRouter, no Chinese models). The configuration enforces this at the gateway layer — `model.primary` is locked to `epam_dial/*` and the module rejects any non-DIAL provider at config-validation time. |
| **Models used** | Only the subset of DIAL-deployed models my personal key is authorized for: `claude-haiku-4-5`, `gpt-4o`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-oss-120b`, `gemini-2.5-flash`. (Tier-restricted models like full Sonnet/Opus, GPT-5, Nova return 403 on my key — they are inaccessible by tier policy, not by my configuration.) |
| **Data handling** | Every action is logged locally to `~/.openclaw/audit/` with prompt + model called + output + action taken. Logs retained 365 days. Available to your team on request. |
| **Send capability** | **Disabled at the runtime layer**, not just by prompt instruction. The OpenClaw configuration includes `tools.deny: ["sessions_send", "exec", "browser", "post_external"]` — even if the agent's instructions were tampered with, the gateway refuses to send. The module can ONLY produce drafts to a local file. I send manually via my normal Outlook / Teams clients. |
| **External egress** | None. Module operates on `127.0.0.1` (loopback) only. The local proxy that bridges OpenClaw to DIAL (LiteLLM, also OSS) listens only on loopback. No public network exposure. |
| **Sensitive content handling** | The agent's operational rules (`AGENTS.md`) instruct it to refuse drafting on legal, HR, salary, security incidents, M&A, or client-IP material; it surfaces those threads to me with `"Sensitive content detected — drafting declined"` instead of producing a draft. Default is conservative refusal. |
| **Client-data handling** | Treats all messages as Confidential by default. Never includes client names, project codes, or NDA-covered content in any output that leaves the local workspace. Does not paste message bodies into web search, web fetch, or external tools. |
| **Audit trail** | `~/.openclaw/audit/atlas-{YYYY-MM-DD}.jsonl` logs every read, draft created, and draft updated. The log is reviewable on demand. |

### 3. What the AI Module is NOT used for

To anticipate Section C scope concerns, this module is **explicitly not used for**:

- Any client-facing deliverable production (no client documents drafted by AI)
- Any code generation, code review, or code commit (separate Section A/B scope, not relevant here)
- Any work outside EPAM corporate channels (no personal email, no personal apps)
- Any non-EPAM venture (I have a separate, fully isolated personal AI assistant for non-EPAM activities; that runs on a *separate workspace*, with *separate credentials*, *separate model providers*, and *cannot* access EPAM data — segregated by configuration)
- Any data exfiltration to non-EPAM cloud services
- Anything that commits EPAM to scope, deliverables, pricing, or contractual terms

### 4. Specific approval I am requesting

1. **Confirmation** that this configuration is acceptable under Section C of the AI Acceptable Use Policy, given the constraints above (DIAL-only inference, draft-only enforcement, local-only operation, audit logging).

2. **Any additional safeguards** you would like me to add before activation — e.g., DLP integration, narrower scope (specific Teams channels only, specific Outlook folders only), centralized log forwarding, content classification filters, AI-output review checkpoints, or any policy attestations I should accept.

3. **Anything I should NOT do** with this module that I might reasonably otherwise consider — e.g., specific client engagements, project codes, message types, or content categories that are out of scope regardless of the safeguards above.

4. **Approval format** — I assume a written email reply on this thread is sufficient. If a more formal approval artifact is required (signed form, ticketing system entry, etc.), please let me know what to submit.

### 5. Activation gate I have set on my side

Until I receive your written approval, the module is gated at the configuration layer:
- Atlas's `AGENTS.md` operational rules (loaded into its system prompt every session) include a `STATUS: BLOCKED` directive that refuses real EPAM data processing without an `~/.openclaw/workspace-epam/clearance-on-file.md` artifact present.
- The MS Teams + MS Outlook channel bindings are intentionally unconfigured — the module can be talked to via CLI for synthetic / dry-run queries but has no live channel access.

When approval arrives, I will:
- Save your reply as the `clearance-on-file.md` artifact (with the date, your team, and any conditions you specify).
- Configure the channel bindings under whatever scope you authorize.
- Restart the gateway and run a final smoke test with a synthetic thread before any real data.

### 6. Attachments / supporting information available on request

- Full module configuration files (`openclaw.json`, `AGENTS.md`, `SOUL.md`) — happy to share if you want to inspect the runtime contract directly.
- Audit log samples from synthetic-data testing (I have ~24 hours of dry-run logs from the smoke-testing phase).
- LiteLLM proxy configuration showing the DIAL-only routing + Azure-auth bridge.

I am happy to walk through the configuration on a quick call or screenshare if that's easier than email — please let me know if useful.

Thank you for the review,

Andrey Popov
[your role / project]
EPAM email: andrey_popov@epam.com
EPAM employee ID: [...]

---

## After you receive the response

If WFT AI Compliance **approves**:

1. Save the reply email as PDF or print-to-file.
2. Place at `C:\Users\AndreyPopov\.openclaw\workspace-epam\clearance-on-file.md` with these contents:

```markdown
# EPAM AI Special Approval — on file

**Approved under:** Section C — Configuring an AI Module or AI Tool for Clients or EPAM — Special Approvals
**Approving authority:** WFTAICompliance@epam.com
**Approving reviewer:** [name from response]
**Approval date:** [YYYY-MM-DD]
**Approved scope:** [exact wording from their email]
**Conditions / safeguards required:** [list any imposed conditions]
**Reference:** [reply email subject + date + any ticket ID]
**Re-review cadence:** [if specified]
```

3. Configure the MS Teams + MS Outlook channel bindings in `~/.openclaw/openclaw.json` — under whatever scope WFT AI Compliance approved.
4. Restart the gateway: `openclaw gateway run --force`
5. Smoke-test Atlas with a synthetic thread before any real data.

If WFT AI Compliance **declines or asks for changes**:

- Update Atlas's AGENTS.md to reflect their constraints (narrower scope, DLP integration, etc.)
- Re-submit a revised configuration.
- Until approved: keep using Claude Code + manual Outlook for EPAM work; Atlas remains in CLI-only synthetic-test mode.

If WFT AI Compliance **doesn't respond within 10 business days**:

- Send a polite follow-up referencing the original submission date.
- Escalate to your line manager: *"I submitted a Section C Special Approval request to WFTAICompliance@epam.com on [date]; can you nudge or advise alternate path?"*
- Until approved, the EPAM agent stays in synthetic-test-only mode.

---

## Pre-send checklist

Before you actually click Send, verify:

- [ ] You have replaced `[your role / project]` and `[your line manager]` with real values.
- [ ] You have confirmed `WFTAICompliance@epam.com` is the correct mailbox per the current KB page (it may have changed; the URL was provided 2026-05-07).
- [ ] You have **pasted the exact Section C content / submission template into our chat** so we can verify the email body answers everything Section C explicitly requires. The current draft is built from inference about what Section C likely asks; the actual policy may have a structured form / questionnaire I haven't seen.
- [ ] You're OK with disclosing the personal $100 DIAL key + Atlas configuration to the AI Compliance team. (Standard for an approval request, but worth a beat.)
- [ ] No client-confidential or NDA material referenced in the email.
- [ ] CC'd your line manager (recommended — they should know about the request even if their approval isn't required).

---

## What this email does NOT cover (out of scope)

- Customer-facing AI features inside EPAM client deliverables (separate Section A/B scope per the Mandatory Process Guidelines — this is just personal productivity)
- Code-generation use of AI inside the IDE (separate scope; covered by EPAM's developer-AI policy)
- Verdaca (the user's separate startup venture) — **explicitly out of scope**; that runs on a fully isolated stack with separate credentials, separate model providers, no EPAM data access. The segregation is baked into the OpenClaw configuration (separate workspaces, separate provider blocks, locked at config-validation time).
