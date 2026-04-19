# Verdaca — Service Provisioning & Brand Registration Guide

**Brand:** Verdaca (pronunciation: **ver-DAH-kuh, like *verdict***)
**Effective:** Stage 7 kickoff, 2026-04-17
**Context:** See `docs/rename-praxis-to-verdaca.md` for the brand-decision record.

## The Golden Rule: Domain First, Everything Derives

The domain IS your brand identity. Every account, repo, and service name should match it. Register the domain first, then cascade.

---

## Step 1: Register the Brand Domain

**Decision (ratified):** `verdaca.ai` (primary) + `verdaca.com` (secondary).

Also lock these typo/mishear defensives same session:
- `verdica.ai` — most common `a/i` slot typo (`.ai`, ~$80/yr, 2-yr min)
- `verdaka.ai` — Verkada mishear deflection (`.ai`, ~$80/yr, 2-yr min)
- `verdaca.co` — phonetic-spelling fallback (`.co`, ~$10–30/yr)

**Where:** **Cloudflare Registrar** (https://dash.cloudflare.com) — at-cost pricing, built-in DNS, no upsells. Confirmed by 30-agent registrar sweep (2026-04-17) as best-fit for the integrated infrastructure story: honest about `.ai` pricing, single platform for DNS/Workers/Pages.

### Critical `.ai` market context (April 2026)

- **`.ai` registry raised wholesale prices +$10/yr effective 2026-03-05.** Current Cloudflare at-cost `.ai` rate: **~$80/yr**.
- **2-year minimum registration is mandatory** for all `.ai` domains (registry rule, not a registrar upsell).
- **`.ai` TLD does NOT support WHOIS privacy** at the registry level. Cloudflare applies redaction as a service, but the raw contact data is registry-visible. Honest registrars disclose this; avoid any that advertise "free privacy on `.ai`" without caveat.

### Expected total bundle cost (first registration period, Cloudflare)

| Item | Period | Cost |
|---|---|---|
| `verdaca.ai` primary | 2 yr | ~$160 |
| `verdica.ai` defensive | 2 yr | ~$160 |
| `verdaka.ai` defensive | 2 yr | ~$160 |
| `verdaca.com` secondary | 1 yr | ~$10 |
| `verdaca.co` defensive | 1 yr | ~$10–30 |
| **Total** | | **~$500–520** |

Renewals at the same rates (Cloudflare has no markup drift); total annual cost post year-1 cascade: ~$250–260/yr.

### Before paying

Final availability confirmation via `whois verdaca.ai` + `whois verdaca.com` + the 3 defensives — the due-diligence sweep was done 2026-04-17 but registration drift is fast (especially after a decision is logged in a doc like this one).

### Fallback registrars

If Cloudflare has an issue at checkout, or you want to compare:

| Registrar | `.ai`/yr | 2-yr bundle est. | Notes |
|---|---|---|---|
| **Cloudflare** ⭐ | $80.00 | ~$500 | At-cost; integrated DNS/CDN/Workers |
| **Spaceship** | $68.98 | ~$417 | Namecheap spin-off; cheapest single-registrar; free WHOIS redaction |
| **Porkbun** | $82.70 | ~$496 | Trustpilot 4.9; multi-code promos |
| **Namecheap** | $71.98 | ~$445 | 2-yr min forced; no `.ai`-eligible promos |

**Active `.ai` promo codes (verified 2026-04-17)** — only useful if routing any domain through a non-Cloudflare registrar:

- Cosmotown `AI23` → $72.20/yr (limit 1, new customers)
- NameSilo `LEONID10` → $67.49/yr (one-time use)
- Porkbun `NPSAVINGS26` → $81.70/yr (April-specific, rotating)

### Registrars to AVOID

30-agent sweep flagged these for renewal-shock, premium markup, or poor reputation: **GoDaddy** (renewal 3× initial), **Domain.com** ($299.98/yr renewal, `.ai` excluded from promos), **Network Solutions** (2–3× market), **EasyDNS** ($251.96/yr renewal), **NameBright** (Trustpilot 1.8), **Sav.com** (Trustpilot 2.1), **WebNames.ca** ($160/yr).

---

## Step 2: Create a Shared Brand Email First

Before registering on ANY service, create a brand email. Everything signs up under this, not your personal email.

**Option A (cheap, immediate):** Register the domain → set up email forwarding to `andrey_popov@epam.com`. Most registrars (Cloudflare, Namecheap) offer free email forwarding. You get `hello@verdaca.ai` that forwards to your inbox.

**Option B (proper, 5 min extra):** Use Google Workspace ($6/mo) or Zoho Mail (free tier) on your domain. You get `andrey@verdaca.ai` as a real mailbox.

**The addresses you'll want:**
- `hello@verdaca.ai` — public contact, Stripe customer-facing emails
- `andrey@verdaca.ai` — your admin account for all services
- `noreply@verdaca.ai` — transactional emails (Clerk invitations, session results)
- `support@verdaca.ai` — error message CTAs in the shell

---

## Step 3: Registration Order (with naming)

### 3a. Domain registrar
**Where:** Cloudflare Registrar
**Names:** `verdaca.ai`, `verdaca.com`, plus 3 defensives (`verdica.ai`, `verdaca.co`, `verdaka.ai`).
**Set up:** Email forwarding for `hello@`, `andrey@`, `support@`, `noreply@` on `verdaca.ai`.

### 3b. GitHub organization
**Where:** https://github.com/organizations/new
**Name:** `verdaca`
**Then:** Transfer the repo from `vospr/PRAXIS` to `verdaca/verdaca` (Settings → Transfer ownership). The URL becomes `github.com/verdaca/verdaca` — clean and branded. The internal Python package namespace stays `src/praxis/` as codename (see `docs/rename-praxis-to-verdaca.md`).
**Team:** Add your account as Owner.

### 3c. Vercel
**Where:** https://vercel.com
**Sign up with:** GitHub (it sees the org). Create a Vercel team named `verdaca`.
**Connect:** The transferred `verdaca/verdaca` repo, root directory `shell/web`.
**Domain:** Add `verdaca.ai` in Vercel project settings. Vercel auto-provisions SSL.
**Result:** `verdaca.ai` serves the Next.js frontend.

### 3d. Neon Postgres
**Where:** https://neon.tech
**Sign up with:** GitHub (same org account).
**Project name:** `verdaca`
**Branches:** `main` (production), `dev` (development).
**Result:** Connection string for `DATABASE_URL`.

### 3e. Clerk
**Where:** https://clerk.com
**Sign up with:** The brand email (`andrey@verdaca.ai`).
**Application name:** `Verdaca`
**Set up:**
- Enable Google + GitHub OAuth providers
- Set the application domain to `verdaca.ai` (Clerk branded pages show your domain, not clerk.com)
- Customize the sign-in/sign-up pages with Verdaca branding (logo, colors)
**Result:** `CLERK_PUBLISHABLE_KEY` + `CLERK_SECRET_KEY`.

### 3f. Stripe
**Where:** https://dashboard.stripe.com/register
**Sign up with:** Brand email.
**Business name:** "Verdaca" (or your legal entity name if different).
**Set up:**
- Create Products: "Verdaca Studio Quick" ($29), "Verdaca Studio Deep" ($149)
- Set up webhook endpoint: `https://api.verdaca.ai/api/webhooks/stripe`
- Customize the Customer Portal (billing settings page) with Verdaca branding
- Upload logo, set brand colors
**Note:** Stay in test mode until 8.8 Launch. Switch to live mode only when ready for real charges.
**Result:** `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET`.

### 3g. Sentry
**Where:** https://sentry.io
**Sign up with:** GitHub (sees the org).
**Organization:** `verdaca`.
**Projects:** `verdaca-api` (Python), `verdaca-web` (Next.js).
**Result:** Two `SENTRY_DSN` strings.

### 3h. (Optional) Plausible Analytics
**Where:** https://plausible.io ($9/mo) or self-host (free).
**Site:** `verdaca.ai`.
**Why not Google Analytics:** Privacy-friendly, no cookie banners needed, aligns with the muted-operator-realism brand direction. Verdaca customers are privacy-conscious founders/COOs.

---

## Step 4: DNS Layout

Once the domain and services are set up, your DNS should look like:

| Record | Type | Value | Purpose |
|---|---|---|---|
| `@` | CNAME | `cname.vercel-dns.com` | Frontend (Next.js) |
| `api` | A/CNAME | Railway/Fargate IP | Backend (FastAPI) |
| `dashboard` | CNAME | same as `@` | Could be a route, not separate subdomain |
| MX records | MX | Per email provider | Email |

**Result:**
- `verdaca.ai` → landing page + app
- `api.verdaca.ai` → FastAPI backend
- `andrey@verdaca.ai` → your inbox

Also: set up `verdaca.com` as a 301-redirect to `verdaca.ai`. The typo defensives (`verdica.ai`, `verdaca.co`, `verdaka.ai`) similarly 301 to `verdaca.ai`.

---

## Step 5: Environment Variables Inventory

After all registrations, you'll have these. Store them in a `.env.local` (gitignored) and in each deployment platform's env config:

```
# Neon Postgres
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/verdaca

# Clerk
CLERK_SECRET_KEY=sk_live_xxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxx

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx (-> sk_live_xxx at launch)
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Sentry
SENTRY_DSN_API=https://xxx@o123.ingest.sentry.io/456
SENTRY_DSN_WEB=https://xxx@o123.ingest.sentry.io/789

# App
API_URL=https://api.verdaca.ai
FRONTEND_URL=https://verdaca.ai
```

---

## Checklist (one sitting, ~45 min)

- [ ] Confirm `verdaca.ai` + `verdaca.com` + 3 defensives still available (whois check)
- [ ] Register all 5 domains (Cloudflare, **~$500–520 total**: 3× `.ai` @ 2-yr min + `.com` + `.co` defensive)
- [ ] Set up 301 redirects from secondaries to `verdaca.ai`
- [ ] Set up email forwarding (`hello@`, `andrey@`, `support@`, `noreply@`) on `verdaca.ai`
- [ ] Create GitHub org `verdaca` -> transfer `vospr/PRAXIS` to `verdaca/verdaca`
- [ ] Sign up Vercel with GitHub -> connect repo -> add `verdaca.ai`
- [ ] Sign up Neon with GitHub -> create project "verdaca"
- [ ] Sign up Clerk with brand email -> create app "Verdaca" -> configure OAuth
- [ ] Sign up Stripe with brand email -> create products (Verdaca Studio Quick/Deep) -> stay in test mode
- [ ] Sign up Sentry with GitHub -> create 2 projects (`verdaca-api`, `verdaca-web`)
- [ ] Commission paid TM clearance search -- USPTO classes 9/42, EU TMview
- [ ] Collect all env vars into a secure note (1Password, Bitwarden, etc.)

Once done, hand the env vars to the Stage 8 context window at step 8.1.
