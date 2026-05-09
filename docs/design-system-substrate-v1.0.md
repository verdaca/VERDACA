# Verdaca — Design System Substrate v1.0

**Version:** v1.0 (git-tracked at `docs/`)
**Status:** Ratified — binding for design substance
**Authored:** 2026-05-03 (substrate cycle close — halt-point #3 of design-agent kickoff cycle)
**Ratified:** 2026-05-09 (v1.0 ceremony — Option B, team-lead facilitated)
**Ratification basis:** D-9 second clean cycle confirmed — Phase 1 thin-slice (2026-05-04) + Phase 2 landing + docs (2026-05-08) shipped without halt-class amendment
**Revision:** 2026-05-03 halt-point #4 advisor-review patches applied — (1) §4.1 single-opacity-per-role principle added; dark caption + secondary unified to 80% on charcoal, no size conditional; (2) §5.1 `type.narrative-deck` role added at `font.size.49` for conference-room deck pull-quotes; (3) §9 R6 supplier-credit placement-list expanded (permitted: in-flow/sidebar/right-rail/compact column; forbidden: collapsed/behind-tab/footer/interaction-required); (4) §9 R10 added (font-loading per-surface responsibility, `font-display: swap` default); (5) §Appendix-B D-9 promotion criterion softened (per-token amendment → halt-class amendment). Appendix-B retained as original-10 substrate-authoring deferral log; #4 advisor-review refinements documented here in frontmatter for revision-history clarity.
**Authority sources:** `docs/pipeline-stage9.md` §1.7 (Caravaggio rule), `docs/18.04.2026.md` Round 2 (Sophia pillars + Caravaggio Slides 1–3 specs), `docs/rename-praxis-to-verdaca.md` (brand identity), `docs/brand-comparison-verdaca-vs-nuagio.md` §3 (typography + visual register findings)
**Promotion path:** COMPLETE — this file is the ratified v1.0; supersedes workshop-binding v0.1
**Brand-name posture:** Verdaca binding for substrate. Substrate is name-agnostic by construction; logo serial-numbering halts pending Verdaca-vs-Nuagio team-lead disposition (`docs/brand-comparison-verdaca-vs-nuagio.md`)
**Caveat scope:** Any metric citation downstream of this substrate must carry "(internal scoring; A4 deferred)" until Stage 7 ratifies ρ ≥ 0.6 (per memory `project_praxis_stage5_6`); see §10 for caveat templates

---

## §0 — How to read this doc

The substrate defines what every downstream Verdaca surface inherits. Three layers:

1. **Tokens** (§3 / §4 / §5) — atomic / semantic / role; W3C Design Tokens spec, Style Dictionary compile chain
2. **Components** (§6) — primitives composed from role tokens; specs for slot dimensions and content rules, not rendered art
3. **Rules** (§8 / §9) — forbidden patterns + per-surface inheritance discipline; substrate-enforced

Per-surface specs (marketing site, deck, product-shell UIs, docs site, sales collateral) inherit by reference — they consume role tokens by name; they MUST NOT redefine atomic tokens locally.

---

## §1 — Substrate scope (A1–A15)

| # | Layer | Pinned at substrate | Deferred to per-surface |
|---|---|---|---|
| A1 | Color tokens | Atomic palette + supplier-line + caveat-footnote treatment | Per-surface accent picks |
| A2 | Type system | Family stacks, scale, caps treatment for marque, supplier-cite mono pattern | Per-surface body-vs-display-vs-headline picks |
| A3 | Spacing + grid | 8px base, modular scale, 12-col / 8-col / 4-col grid | Per-surface composition |
| A4 | Component primitives | Wordmark slot, supplier-cite block, eyebrow, pull-quote, station-sequence, patent-drawing, metric+caveat unit, product-shell badge, glyph slot | Per-surface placement + content |
| A5 | Iconography rules | Supplier-line-art rule, product-shell glyph slot character spec | Glyph designs (per-shell cycle) |
| A6 | Photography / illustration register | Patent-drawing canon, instrument-macro acceptable, anti-stock catalog | Specific commissions |
| A7 | Mode posture | Light-canonical for marketing first-touch + dark-canonical for deck + product UI; surface-intent rule | Per-surface mode pick |
| A8 | Metric + A4-caveat treatment | Composite primitive; substrate-enforced caveat presence | Per-surface placement |
| A9 | Semantic color layer | `--color-text-primary` / `--color-bg-canvas` / `--color-accent-cta` / etc.; mode-aware remap | Per-surface composition |
| A10 | Motion principles | 3 sanctioned patterns; explicit anti-pattern catalog; `prefers-reduced-motion` rule | Per-component transitions |
| A11 | Data-viz palette | 4-series cap (oxblood/bronze/steel/graphite); gridline rule | Per-chart series picks |
| A12 | Accessibility floor | WCAG AA minimum substrate-wide; opacity/size rules; contrast verification | Per-surface QA |
| A13 | Form / input register | Instrument-panel: square corners, sub-1px structural shadow sanctioned | Per-surface form composition |
| A14 | Interaction-state slots | Default / hover / focus / active / disabled — principles pinned, values per-component | Per-component values |
| A15 | Mobile compression rule | Breakpoints + collapse rule; hero illustration stack ≤768px | Per-surface mobile QA |

---

## §2 — Family layer (font stacks)

```json
{
  "font": {
    "family": {
      "sans": {
        "$value": ["Inter Tight", "Söhne", "ui-sans-serif", "system-ui"],
        "$type": "fontFamily",
        "$description": "Primary sans. Inter Tight (OFL, free) is canonical render-truth. Söhne (Klim Type Foundry, paid) documented as paid-upgrade variant — substitutes seamlessly when license is purchased; substrate authors against Inter Tight to prevent silent register-drift on unlicensed renders."
      },
      "mono": {
        "$value": ["Söhne Mono", "JetBrains Mono", "ui-monospace", "Menlo", "Consolas"],
        "$type": "fontFamily",
        "$description": "Monospace. Söhne Mono canonical for Caravaggio Slide 1 VERDACA chassis label and Slide 2 BOM cite block. JetBrains Mono (OFL, free) as render-truth fallback. NOTE: family.mono polarity differs from family.sans because the marque chassis treatment is the most visually-load-bearing single use of the substrate; Söhne Mono is the design-target even though Inter Tight is the sans render-truth."
      },
      "serif": {
        "$value": ["GT Sectra", "Source Serif 4", "ui-serif", "Georgia"],
        "$type": "fontFamily",
        "$description": "Italic-only narrative use. GT Sectra Book Italic (GrilliType, paid) primary; Source Serif 4 Italic (OFL, free) free fallback. Asymmetric polarity vs family.sans intentional: italic-serif use is volume-low (≤1 narrative pull-quote per surface) so the register cost of free-only fallback is judged too high. Caravaggio Slide 1 / Slide 3 italic-serif treatments target GT Sectra contrast curve."
      }
    }
  }
}
```

**Canonical CSS-build output:**

```css
--font-family-sans:  'Inter Tight', 'Söhne', ui-sans-serif, system-ui;
--font-family-mono:  'Söhne Mono', 'JetBrains Mono', ui-monospace, Menlo, Consolas;
--font-family-serif: 'GT Sectra', 'Source Serif 4', ui-serif, Georgia;
```

**Forbidden faces (anti-tokens):** Circular Std, Greycliff, GT Walsheim, any "rounded-friendly" face (consumer-SaaS register); Tiempos *Headline* italic at hero (magazine-luxe register); display serifs at body sizes; any face with significant variable-width counterforms (Cooper Black, Lobster, Pacifico class).

---

## §3 — Atomic tokens

### §3.1 Color (raw palette)

```json
{
  "color": {
    "verdaca": {
      "oxblood":  { "$value": "#6B1F25", "$type": "color", "$description": "Verdaca brand primary; chassis fill; CTA. Pick mid-band; avoids bright red, retains auto-marque burgundy register." },
      "charcoal": { "$value": "#1F2226", "$type": "color", "$description": "Canonical canvas (dark mode); secondary type / line-art base on cream. Matte, slightly cool-neutral." },
      "cream":    { "$value": "#F2EDE2", "$type": "color", "$description": "Light-mirror canvas; paper register. Warm off-white; never pure #FFFFFF." },
      "graphite": { "$value": "#42454A", "$type": "color", "$description": "Body type on cream; secondary line-art on charcoal." },
      "bronze":   { "$value": "#967853", "$type": "color", "$description": "Accent metallic, sparingly; instrument-tier surfaces (medallion, version-pin, seal)." },
      "steel":    { "$value": "#979CA3", "$type": "color", "$description": "Accent metallic mirror; cool companion to bronze." }
    }
  }
}
```

**WCAG verification (substrate-binding, computed at v0.1 commit):**

| Foreground | Background | Ratio | AA body (4.5:1) | AAA body (7:1) | Notes |
|---|---|---|---|---|---|
| oxblood `#6B1F25` | cream `#F2EDE2` | 10.2:1 | ✅ | ✅ | Body type permitted on cream |
| oxblood `#6B1F25` | charcoal `#1F2226` | 2.1:1 | ❌ | ❌ | **Oxblood-on-charcoal restricted to ≥3:1 non-text use** (chassis fills, accent shapes); never type, never UI control perimeters. Caravaggio Slide 1 VERDACA chassis label on charcoal is a filled marque, not running type — compliant. |
| cream `#F2EDE2` | charcoal `#1F2226` | 13.8:1 | ✅ | ✅ | Body type on dark canvas |
| graphite `#42454A` | cream `#F2EDE2` | 7.5:1 | ✅ | ✅ | Body type on cream (secondary) |
| graphite-80% on cream | (effective `#585A60`) | 6.0:1 | ✅ | ✅ | Caption / footnote rule (see A12 §3.4) |
| bronze `#967853` | cream `#F2EDE2` | 3.4:1 | ❌ body / ✅ large (3:1) | ❌ | Bronze permitted at ≥18.66px or as accent shape; never body type |
| steel `#979CA3` | cream `#F2EDE2` | 2.6:1 | ❌ | ❌ | Steel permitted as accent shape only; never type on cream |
| steel `#979CA3` | charcoal `#1F2226` | 5.3:1 | ✅ | ❌ AAA | Steel may bear ≥14px caption type on charcoal |

**Forbidden color families (anti-tokens):**
- Linear gradients between two hues (purple→blue, teal→green, red→orange) — banned
- Neon / fluorescent: any S > 90, L > 60 — banned
- Pastel: any S < 30, L > 80 — banned
- Pure `#000000` or `#FFFFFF` for canvas use — banned (always charcoal-warm or cream-warm)
- Tableau / D3 categorical / rainbow / viridis palette — banned for charts (see A11)

### §3.2 Type size scale (modular, 1.250 ratio, 16px base)

```json
{
  "font": {
    "size": {
      "12":  { "$value": "0.8rem",   "$type": "dimension", "$description": "Caption / footnote / micro-copy" },
      "16":  { "$value": "1rem",     "$type": "dimension", "$description": "Body base" },
      "20":  { "$value": "1.25rem",  "$type": "dimension", "$description": "Body-emphasis" },
      "25":  { "$value": "1.563rem", "$type": "dimension", "$description": "Section subheads" },
      "31":  { "$value": "1.953rem", "$type": "dimension", "$description": "Headlines" },
      "39":  { "$value": "2.441rem", "$type": "dimension", "$description": "Display" },
      "49":  { "$value": "3.052rem", "$type": "dimension", "$description": "Hero display / marque-header" },
      "61":  { "$value": "3.815rem", "$type": "dimension", "$description": "Hero marque (Slide 1 / marketing hero)" }
    }
  }
}
```

**Scale decision:** 1.250 (major-third). Rationale: industrial-editorial restraint. 1.333+ ratios produce magazine-headline drama (Tiempos Headline territory) which the register forbids.

### §3.3 Tracking, weight, line-height

```json
{
  "font": {
    "weight": {
      "regular":  { "$value": 400, "$type": "fontWeight" },
      "medium":   { "$value": 500, "$type": "fontWeight" },
      "semibold": { "$value": 600, "$type": "fontWeight" }
    },
    "tracking": {
      "marque-hero":  { "$value": "0.02em", "$type": "dimension", "$description": "VERDACA hero (Slide 1 chassis label, marketing hero)" },
      "marque-body":  { "$value": "0.04em", "$type": "dimension", "$description": "VERDACA in headers / nav" },
      "eyebrow":      { "$value": "0.12em", "$type": "dimension", "$description": "All-caps eyebrow labels (SOURCED, VETTED, PINNED)" },
      "body":         { "$value": "0",      "$type": "dimension" },
      "mono-cite":    { "$value": "0",      "$type": "dimension", "$description": "BOM cite block (MEM0 · memory · v2.4.1 · MIT)" }
    },
    "lineHeight": {
      "tight":   { "$value": 1.15, "$type": "number", "$description": "Display / hero" },
      "snug":    { "$value": 1.30, "$type": "number", "$description": "Headlines / subheads" },
      "normal":  { "$value": 1.55, "$type": "number", "$description": "Body" },
      "relaxed": { "$value": 1.65, "$type": "number", "$description": "Long-form body / editorial" }
    }
  }
}
```

### §3.4 Spacing scale (8px base)

```json
{
  "space": {
    "4":   { "$value": "0.25rem", "$type": "dimension" },
    "8":   { "$value": "0.5rem",  "$type": "dimension" },
    "12":  { "$value": "0.75rem", "$type": "dimension" },
    "16":  { "$value": "1rem",    "$type": "dimension" },
    "24":  { "$value": "1.5rem",  "$type": "dimension" },
    "32":  { "$value": "2rem",    "$type": "dimension" },
    "48":  { "$value": "3rem",    "$type": "dimension" },
    "64":  { "$value": "4rem",    "$type": "dimension" },
    "96":  { "$value": "6rem",    "$type": "dimension" },
    "128": { "$value": "8rem",    "$type": "dimension" },
    "192": { "$value": "12rem",   "$type": "dimension" }
  }
}
```

### §3.5 Grid + container

```json
{
  "grid": {
    "columns": {
      "desktop": { "$value": 12, "$type": "number", "$description": "≥1024px" },
      "tablet":  { "$value": 8,  "$type": "number", "$description": "768–1023px" },
      "mobile":  { "$value": 4,  "$type": "number", "$description": "<768px" }
    },
    "gutter": {
      "desktop": { "$value": "{space.32}", "$type": "dimension" },
      "tablet":  { "$value": "{space.24}", "$type": "dimension" },
      "mobile":  { "$value": "{space.16}", "$type": "dimension" }
    }
  },
  "container": {
    "max":     { "$value": "1280px", "$type": "dimension", "$description": "Industrial-editorial breathing room; not 1440 / 1600 sprawl" },
    "padding": {
      "desktop": { "$value": "{space.32}", "$type": "dimension" },
      "tablet":  { "$value": "{space.24}", "$type": "dimension" },
      "mobile":  { "$value": "{space.16}", "$type": "dimension" }
    }
  }
}
```

### §3.6 Border, radius, structural shadow (per A13)

```json
{
  "border": {
    "width": {
      "hairline":   { "$value": "1px", "$type": "dimension", "$description": "Default rule, divider" },
      "thick":      { "$value": "2px", "$type": "dimension", "$description": "Focus outline, accent rule" }
    }
  },
  "radius": {
    "sharp":   { "$value": "0",   "$type": "dimension", "$description": "Default; instrument-panel register" },
    "subtle":  { "$value": "2px", "$type": "dimension", "$description": "Maximum permitted radius for any UI surface" }
  },
  "shadow": {
    "structural-inset-cream": {
      "$value": "inset 0 1px 0 rgba(31, 34, 38, 0.18)",
      "$type": "shadow",
      "$description": "Sub-1px milled-aluminum inset for inputs / pressed states on cream surface. SANCTIONED carve-out from no-gradient anti-token (per A13 disposition): structural depth signaling, distinct from fill-gradient register pollution."
    },
    "structural-inset-charcoal": {
      "$value": "inset 0 1px 0 rgba(242, 237, 226, 0.10)",
      "$type": "shadow",
      "$description": "Cream-tinted inset for inputs / pressed states on charcoal surface."
    }
  }
}
```

**Shadow boundary (anti-token):** any shadow with blur > 2px, spread > 0, or distance > 1px = banned (consumer-app drop-shadow register). Structural shadows ONLY.

### §3.7 Motion (per A10)

```json
{
  "motion": {
    "duration": {
      "instant":  { "$value": "0ms",   "$type": "duration", "$description": "prefers-reduced-motion fallback for all sanctioned animations" },
      "fast":     { "$value": "120ms", "$type": "duration", "$description": "State transitions (hover, focus)" },
      "standard": { "$value": "200ms", "$type": "duration", "$description": "Fade-in" },
      "deliberate": { "$value": "300ms", "$type": "duration", "$description": "Pull-quote underscore wipe" }
    },
    "easing": {
      "ease-out":    { "$value": "cubic-bezier(0.0, 0.0, 0.2, 1)", "$type": "cubicBezier" },
      "ease-in-out": { "$value": "cubic-bezier(0.4, 0.0, 0.2, 1)", "$type": "cubicBezier" }
    }
  }
}
```

---

## §4 — Semantic color layer (mode-aware)

Mode-switch becomes a single semantic-layer remap; downstream surfaces consume semantic tokens, never raw `--verdaca-*` directly.

```json
{
  "color": {
    "semantic": {
      "light": {
        "bg":      { "canvas":    { "$value": "{color.verdaca.cream}",    "$type": "color" },
                     "elevated":  { "$value": "{color.verdaca.cream}",    "$type": "color" },
                     "inset":     { "$value": "{color.verdaca.cream}",    "$type": "color", "$description": "form input fill" } },
        "text":    { "primary":   { "$value": "{color.verdaca.charcoal}", "$type": "color" },
                     "secondary": { "$value": "{color.verdaca.graphite}", "$type": "color" },
                     "caption":   { "$value": "{color.verdaca.graphite}", "$type": "color", "$description": "Apply 80% opacity at composition layer; passes WCAG AAA at all sizes" },
                     "accent":    { "$value": "{color.verdaca.oxblood}",  "$type": "color" } },
        "rule":    { "default":   { "$value": "{color.verdaca.graphite}", "$type": "color", "$description": "Apply 30% opacity for hairline" },
                     "accent":    { "$value": "{color.verdaca.oxblood}",  "$type": "color" } },
        "supplier-line": { "$value": "{color.verdaca.charcoal}", "$type": "color", "$description": "Caravaggio §1.7: suppliers always monochrome" },
        "metric-headline": { "$value": "{color.verdaca.oxblood}", "$type": "color" },
        "caveat-footnote": { "$value": "{color.verdaca.graphite}", "$type": "color", "$description": "Apply 80% opacity; italic serif" }
      },
      "dark": {
        "bg":      { "canvas":    { "$value": "{color.verdaca.charcoal}", "$type": "color" },
                     "elevated":  { "$value": "{color.verdaca.charcoal}", "$type": "color" },
                     "inset":     { "$value": "{color.verdaca.charcoal}", "$type": "color" } },
        "text":    { "primary":   { "$value": "{color.verdaca.cream}",    "$type": "color" },
                     "secondary": { "$value": "{color.verdaca.cream}",    "$type": "color", "$description": "Apply 80% opacity at composition layer; passes WCAG AAA at all sizes (≈11.0:1 effective)" },
                     "caption":   { "$value": "{color.verdaca.cream}",    "$type": "color", "$description": "Apply 80% opacity at composition layer; passes WCAG AAA at all sizes including the 12px font.size.12 floor" },
                     "accent":    { "$value": "{color.verdaca.oxblood}",  "$type": "color", "$description": "Restricted to non-text use on dark canvas (chassis fill, accent shape) per §3.1 WCAG table" } },
        "rule":    { "default":   { "$value": "{color.verdaca.cream}",    "$type": "color", "$description": "Apply 20% opacity for hairline" },
                     "accent":    { "$value": "{color.verdaca.oxblood}",  "$type": "color" } },
        "supplier-line": { "$value": "{color.verdaca.cream}", "$type": "color" },
        "metric-headline": { "$value": "{color.verdaca.oxblood}", "$type": "color", "$description": "Used as filled hero treatment, not body type" },
        "caveat-footnote": { "$value": "{color.verdaca.cream}", "$type": "color", "$description": "Apply 60% opacity; italic serif" }
      }
    }
  }
}
```

**Mode binding rule:** any downstream surface declares its mode at the root (`data-mode="light"` or `"dark"`), and all `color.semantic.*` references resolve through the active mode automatically. Per-component code never hardcodes `light` or `dark`.

### §4.1 Single-opacity-per-role principle

Each text/rule role in the semantic color layer specifies a **single opacity value** computed to satisfy WCAG AAA at the smallest `font.size.*` step the role is used at. **No size-conditional opacity in semantic tokens** — simplicity beats theoretical precision. Per-surface code applies the role's single declared opacity at composition; never branches on size.

Verification at v0.1: cream `#F2EDE2` at 80% over charcoal `#1F2226` ≈ effective `#C5C1B5`, contrast ≈11.0:1 → passes AAA (7:1) at every scale step including the 12px `font.size.12` floor. Same single 80% rule applied uniformly to `color.semantic.dark.text.secondary` and `color.semantic.dark.text.caption`. Visual hierarchy (caption < secondary < primary) is preserved through type scale + role differentiation, not through opacity ladders.

---

## §5 — Role tokens (composed)

Role tokens are the consumer-facing API. Per-surface code references roles by name; never atomic tokens directly (color exception: brand chassis fill on hero may reference `color.verdaca.oxblood` directly because it's a brand-identity invariant, not a theme decision).

### §5.1 Type roles

```json
{
  "type": {
    "marque-hero": {
      "$value": {
        "fontFamily":     "{font.family.mono}",
        "fontSize":       "{font.size.61}",
        "fontWeight":     "{font.weight.semibold}",
        "letterSpacing":  "{font.tracking.marque-hero}",
        "lineHeight":     "{font.lineHeight.tight}",
        "textTransform":  "uppercase"
      },
      "$type": "typography",
      "$description": "VERDACA chassis label, hero use (Slide 1 / marketing hero)"
    },
    "marque-header": {
      "$value": {
        "fontFamily":     "{font.family.mono}",
        "fontSize":       "{font.size.31}",
        "fontWeight":     "{font.weight.semibold}",
        "letterSpacing":  "{font.tracking.marque-body}",
        "lineHeight":     "{font.lineHeight.snug}",
        "textTransform":  "uppercase"
      },
      "$type": "typography",
      "$description": "VERDACA in nav / header bar"
    },
    "display": {
      "$value": {
        "fontFamily":     "{font.family.sans}",
        "fontSize":       "{font.size.49}",
        "fontWeight":     "{font.weight.semibold}",
        "lineHeight":     "{font.lineHeight.tight}"
      },
      "$type": "typography",
      "$description": "Hero headlines (non-marque)"
    },
    "headline": {
      "$value": {
        "fontFamily":     "{font.family.sans}",
        "fontSize":       "{font.size.31}",
        "fontWeight":     "{font.weight.medium}",
        "lineHeight":     "{font.lineHeight.snug}"
      },
      "$type": "typography",
      "$description": "Section heads, deck slide titles"
    },
    "body": {
      "$value": {
        "fontFamily":     "{font.family.sans}",
        "fontSize":       "{font.size.16}",
        "fontWeight":     "{font.weight.regular}",
        "lineHeight":     "{font.lineHeight.normal}"
      },
      "$type": "typography"
    },
    "body-editorial": {
      "$value": {
        "fontFamily":     "{font.family.sans}",
        "fontSize":       "{font.size.16}",
        "fontWeight":     "{font.weight.regular}",
        "lineHeight":     "{font.lineHeight.relaxed}"
      },
      "$type": "typography",
      "$description": "Long-form marketing / editorial body"
    },
    "mono-cite": {
      "$value": {
        "fontFamily":     "{font.family.mono}",
        "fontSize":       "{font.size.16}",
        "fontWeight":     "{font.weight.regular}",
        "letterSpacing":  "{font.tracking.mono-cite}",
        "lineHeight":     "{font.lineHeight.normal}"
      },
      "$type": "typography",
      "$description": "Supplier-cite block (Caravaggio Slide 2 BOM pattern); version pins; code"
    },
    "narrative": {
      "$value": {
        "fontFamily":     "{font.family.serif}",
        "fontSize":       "{font.size.31}",
        "fontStyle":      "italic",
        "lineHeight":     "{font.lineHeight.snug}"
      },
      "$type": "typography",
      "$description": "Italic-serif pull-quotes (Sophia three-pillar surface, Slide 1/3 narrative captions)"
    },
    "narrative-hero": {
      "$value": {
        "fontFamily":     "{font.family.serif}",
        "fontSize":       "{font.size.39}",
        "fontStyle":      "italic",
        "lineHeight":     "{font.lineHeight.snug}"
      },
      "$type": "typography",
      "$description": "Hero pull-quote variant"
    },
    "narrative-deck": {
      "$value": {
        "fontFamily":     "{font.family.serif}",
        "fontSize":       "{font.size.49}",
        "fontStyle":      "italic",
        "lineHeight":     "{font.lineHeight.snug}"
      },
      "$type": "typography",
      "$description": "Deck pull-quote variant; sized for conference-room projection distance on dark-canonical deck slides; pre-empts deck-cycle substrate-bump request. Deck-only role; not subject to §5.2 mobile collapse (decks render slide-aspect, not responsive web)."
    },
    "eyebrow": {
      "$value": {
        "fontFamily":     "{font.family.sans}",
        "fontSize":       "{font.size.12}",
        "fontWeight":     "{font.weight.medium}",
        "letterSpacing":  "{font.tracking.eyebrow}",
        "lineHeight":     "{font.lineHeight.snug}",
        "textTransform":  "uppercase"
      },
      "$type": "typography",
      "$description": "Oxblood eyebrow label (SOURCED, VETTED, PINNED — Caravaggio Slide 2)"
    },
    "caption": {
      "$value": {
        "fontFamily":     "{font.family.sans}",
        "fontSize":       "{font.size.12}",
        "fontWeight":     "{font.weight.regular}",
        "lineHeight":     "{font.lineHeight.normal}"
      },
      "$type": "typography",
      "$description": "Caption, micro-copy, footnote (graphite at 80%)"
    },
    "caveat": {
      "$value": {
        "fontFamily":     "{font.family.serif}",
        "fontSize":       "{font.size.12}",
        "fontStyle":      "italic",
        "lineHeight":     "{font.lineHeight.normal}"
      },
      "$type": "typography",
      "$description": "A4-caveat footnote treatment (italic serif at 80% opacity; substrate-enforced presence)"
    }
  }
}
```

### §5.2 Mobile collapse rule (per A15)

At `<768px` (mobile breakpoint), apply one-step scale collapse to display / hero roles:

| Role | Desktop / Tablet | Mobile (<768px) |
|---|---|---|
| `type.marque-hero` | `font.size.61` | `font.size.49` |
| `type.marque-header` | `font.size.31` | `font.size.25` |
| `type.display` | `font.size.49` | `font.size.39` |
| `type.headline` | `font.size.31` | `font.size.25` |
| `type.narrative-hero` | `font.size.39` | `font.size.31` |
| `type.narrative` | `font.size.31` | `font.size.25` |

Body / mono-cite / eyebrow / caption / caveat scales are mobile-stable.

---

## §6 — Component primitives

### §6.1 Wordmark slot

**Purpose:** Reserved space + treatment for the brand wordmark. Substrate is brand-name-agnostic; the slot survives Verdaca → Nuagio rename intact.

| Spec | Value |
|---|---|
| Type role | `type.marque-hero` (hero use) or `type.marque-header` (nav use) |
| Color | `color.semantic.text.primary` (light mode) or `color.verdaca.oxblood` (hero mode override per Slide 1 spec) |
| Clear-space cushion | `space.32` minimum on all four sides |
| Vertical alignment | Optical baseline-center; ascenders are minimal in `VERDACA` (only `D`) |
| **HALT-CLASS:** | Logo serial-numbering (mark + signature locking) HELD pending Verdaca-vs-Nuagio team-lead disposition. Substrate pins SLOT only; no committed wordmark art at v0.1. |

### §6.2 Product-shell badge / lockup

**Purpose:** `VERDACA · STUDIO` lockup pattern; master mark + middle dot (U+00B7) + shell name in `type.eyebrow`.

| Spec | Value |
|---|---|
| Master mark | `type.marque-header` |
| Separator | Middle dot ` · ` (U+00B7) with `space.8` flanking |
| Shell name | `type.eyebrow` |
| Color | All `color.semantic.text.primary` |
| Accent variant | Shell name in `color.verdaca.oxblood` for active-shell context (e.g., dashboard breadcrumb) |
| Five shells (substrate-pinned) | `STUDIO`, `FACTORY`, `SHIELD`, `PIPELINE`, `OPS` |

### §6.3 Product-shell glyph slot (per A5 / D-5)

**Purpose:** Reserved iconographic slot for each of the 5 shells. Slot pinned at substrate; glyph designs deferred to per-shell cycle.

| Spec | Value |
|---|---|
| Sizes | 24×24 / 32×32 / 48×48 px (1× / 1.5× / 2×) |
| Stroke | Single weight, 1.5px at 32×32 baseline (scales proportionally) |
| Terminal style | **Square** (matches instrument-tier register) |
| Color | `color.semantic.text.primary` or `color.verdaca.oxblood` for active state |
| Reference set | Caliper, micrometer, valve, spirit-level, lathe-bit, machinist-square, dial-gauge, depth-stop, vise — precision-tool / mechanical-instrument / industrial-meter visual vocabulary |
| **Anti-set** | Material Icons / Font Awesome / Heroicons / Phosphor / generic line-icon packs; rounded-friendly icons; isometric "3D" icon style; gradient-mesh icons; emoji |
| **HALT-CLASS:** | No glyph designs at v0.1. Glyph language commits to a per-shell cycle. |

### §6.4 Supplier-cite block (BOM primitive)

**Purpose:** Generalize Caravaggio Slide 2 BOM pattern as substrate primitive. Load-bearing for Sophia pillar #2 ("supplier list = quality signal"). Substrate-enforced: any downstream surface that omits / hides the supplier list = halt-class.

**Layout (canonical):**

```
SOURCED, VETTED, PINNED                   ← type.eyebrow @ color.text.accent (oxblood)

MEM0       · memory             · v2.4.1   · MIT          ← type.mono-cite @
LETTA      · memory (substrate) · v0.6.x   · Apache-2.0      color.semantic.supplier-line
TONL       · serialization      · v0.3.0   · MIT
BEADS      · versioned-state    · v1.1.0   · MIT
FORGE      · compaction         · v2.0.0   · MIT
PI-MONO    · cost-meter         · v0.8.x   · MIT
RTK        · llm-proxy          · v1.4.0   · MIT
─────────────────────────────────────────────  ← border.hairline @ color.rule.default

"Six suppliers. One accountable brand."  ← type.narrative @ color.text.primary
```

**Field order (substrate-binding):** `NAME · ROLE · VERSION · LICENSE`. Always all four. Always `type.mono-cite`. Always monochrome (`color.semantic.supplier-line`).

**Forbidden substitutions:**
- Replacing typographic citation with full-color supplier logos
- Omitting version pin
- Omitting license field
- Using non-mono type
- Using any color other than `supplier-line`

### §6.5 Eyebrow label

| Spec | Value |
|---|---|
| Type role | `type.eyebrow` |
| Color | `color.semantic.text.accent` (oxblood) |
| Content rule | Comma-separated terms (Caravaggio Slide 2 verbatim: `SOURCED, VETTED, PINNED`); substrate pins typographic pattern; per-surface picks terms |
| Placement | Always above its anchored heading; `space.16` below |

### §6.6 Pull-quote primitive (Sophia three-pillar surface)

| Spec | Value |
|---|---|
| Type role | `type.narrative` (or `type.narrative-hero` for hero use) |
| Color | `color.semantic.text.primary` |
| Quote marks | NONE (Patek convention; the typographic distinction does the work) |
| Accent rule | Above quote: 1px line, `color.semantic.rule.accent` (oxblood), `space.48` wide, `space.16` above quote |
| Paragraph indent | None |
| Width constraint | Max 60ch line length |

**Sophia three pillars rendered through this primitive:**
1. *We own the box, not every bolt.*
2. *Our supplier list is a quality signal.*
3. *Replaceable by design, not by accident.*

(Substrate renders these verbatim; copy is Sophia's authority — never edit.)

### §6.7 Station-sequence primitive (Slide 3 CNC pattern, generalized)

**Purpose:** Generalize Caravaggio Slide 3 (PIN → TEST → RE-RATIFY → SHIP) as substrate primitive for any process-flow rendering.

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  PIN    │  ›  │  TEST   │  ›  │RE-RATIFY│  ›  │  SHIP   │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
 commit-SHA      contract        arch-doc       SBOM +
 + sha256        suite +         signed         release
                 matrix                         tag
```

| Spec | Value |
|---|---|
| Station box | Square corners (`radius.sharp`), 1px border (`color.semantic.rule.default`), `space.24` padding |
| Station label | `type.eyebrow` @ `color.semantic.text.primary` |
| Connector | Chevron `›` (U+203A) or arrow `→` (U+2192) in `color.verdaca.bronze`, `type.headline` size |
| Sub-line | 2 lines max, `type.caption` @ `color.semantic.text.secondary` |
| Caption beneath | Optional pull-quote in `type.narrative` |

### §6.8 Patent-drawing illustration treatment

Substrate pins the **register** (style language); per-surface authoring commissions specific illustrations.

| Spec | Value |
|---|---|
| Stroke | White (`color.verdaca.cream`) line-work on `color.verdaca.charcoal` canvas (dark mode); inverse on light mode (charcoal on cream) |
| Stroke weight | 1.5px primary contour; 1px secondary detail |
| Style | Patent-drawing exploded-view; mechanical-engineering technical-illustration register |
| Labels | `type.mono-cite` with leader-lines (1px, same stroke as drawing) |
| Color | Monochrome line-art ONLY; sole color exception = brand chassis fill (`color.verdaca.oxblood`) per Caravaggio Slide 1 ("VERDACA on oxblood chassis") |
| **Anti-references** | 3D rendered diagrams; isometric illustrations; gradient-mesh; "neural network" galaxy renders; cartoon mechanical illustrations; generic stock illustrations |

### §6.9 Metric + A4-caveat unit (load-bearing composite primitive)

**Purpose:** Canonical visual rendering of headline metric + A4 caveat. Load-bearing: Stage 6 self-demo headline (~$2.50/~12min Studio session, +47% vs vanilla / +21% vs enhanced) lands across marketing site / deck / case-study / product-shell self-demo. Per memory `project_praxis_stage5_6`, the A4 caveat must travel with the metric on every citation until Stage 7 ratifies ρ ≥ 0.6.

**Composite spec:**

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  ~$2.50 / ~12 min                               │  ← type.display @ color.metric-headline (oxblood)
│  ────────────────                               │
│  Verdaca Studio session                         │  ← type.caption @ color.text.secondary
│                                                 │
│  +47% vs vanilla  ·  +21% vs enhanced           │  ← type.body @ color.text.primary
│                                                 │
│  (internal scoring; A4 deferred)                │  ← type.caveat @ color.caveat-footnote
│                                                 │
└─────────────────────────────────────────────────┘
   space.48 padding · color.bg.canvas
```

**Substrate-enforced rules:**
1. The caveat string MUST appear in the same visual unit as the metric (not in a footer, not as a tooltip, not behind a `[?]` icon)
2. The caveat MUST use `type.caveat` (italic serif, distinguishes it visually from running body)
3. The caveat MUST be at minimum 80% the visual prominence of the secondary metric line (cannot be hidden in lower contrast / smaller size beyond substrate-set ratio)
4. The caveat string is templated (see §10) — never abbreviated, never paraphrased

**HALT-CLASS:** any downstream surface that prints the metric without the caveat unit = halt; any per-surface code that breaks the unit (separates metric from caveat in DOM/markup) = halt.

### §6.10 Form / input primitive (per A13)

| Spec | Value |
|---|---|
| Field shape | Rectangle, `radius.sharp` (0px) corners |
| Border | 1px `color.semantic.rule.default` |
| Inset shadow | `shadow.structural-inset-cream` (light) or `shadow.structural-inset-charcoal` (dark) — milled-aluminum tactile cue |
| Padding | `space.16` horizontal × `space.12` vertical |
| Type | `type.body` |
| Active state | 2px `color.semantic.rule.accent` (oxblood) border replaces 1px default; inset shadow remains |
| Disabled | 50% opacity on entire field; `cursor: not-allowed` |
| **Anti-pattern** | Rounded-friendly form chrome (Notion / Stripe Checkout register); floating-label patterns; oversized form fields (Stripe consumer pages); pill-shape inputs |

---

## §7 — Interaction states (per A14)

Substrate pins **principles** for all five states; per-component cycles pick concrete values within these principles.

| State | Principle |
|---|---|
| **default** | Base state, no decoration. Read as "instrument at rest." |
| **hover** | Subtle elevation cue. Permitted: color shift +5% lightness on accent; underline appearance for inline links; cursor change. **Forbidden:** transform / scale / shadow puff / "lift" effect. |
| **focus** | Required for accessibility. 2px (`border.thick`) `color.semantic.rule.accent` outline, 2px offset (visible gap between control and outline), `radius.sharp` outline corners (matches instrument-tier register). **Forbidden:** glow / halo / box-shadow-only focus rings. |
| **active** (pressed) | -5% lightness on accent; optional `shadow.structural-inset-*` to signal "depressed key" (sub-1px inset, sanctioned per A13). **Forbidden:** scale / squish transforms. |
| **disabled** | 50% opacity on entire control; `cursor: not-allowed`. **No** background color shift (background stays mode-canvas). |

**`prefers-reduced-motion: reduce` rule (substrate-enforced):** all sanctioned motion patterns (§3.7 / §6.x) collapse to `motion.duration.instant` (0ms) when this media query matches. State transitions become instant; fade-in / station-reveal / underscore-wipe become instant state changes. Substrate provides the CSS gate; per-component code MUST respect it.

---

## §8 — Forbidden tokens & forbidden patterns (anti-token catalogs)

### §8.1 Color anti-tokens

| Anti-token | Detection rule (CI candidate) |
|---|---|
| Linear gradient between two hues | Any `linear-gradient(...)` declaration that names ≥2 distinct hue stops |
| Neon / fluorescent | Any color with `S > 90 AND L > 60` in HSL |
| Pastel | Any color with `S < 30 AND L > 80` in HSL |
| Pure black canvas | `#000000` or `rgb(0,0,0)` as `background-color` |
| Pure white canvas | `#FFFFFF` or `rgb(255,255,255)` as `background-color` |
| Tableau categorical / rainbow / viridis | Any chart palette referencing these named scales |
| Supplier color leak | Mem0 / Letta / TONL / Beads / Pi-Mono / Forge / RTK / Atelier / Atomic Agents brand color hex anywhere outside designated supplier-asset folders |

### §8.2 Type anti-faces

Circular Std, Greycliff, GT Walsheim, Avenir Next Rounded, Tiempos *Headline* italic at hero, Cooper Black, Lobster, Pacifico, any Adobe Fonts "Display" rounded-friendly cut, any face explicitly designed for "consumer-friendly" register.

### §8.3 Pattern anti-references

| Anti-pattern | Why forbidden |
|---|---|
| Hexagon-tile patterns | "AI platform 2023" register |
| Neural-network 3D renders / galaxy fields | Same |
| Robot-and-human handshake illustration | Stock-AI cliché |
| Gradient-mesh blob illustrations | Consumer-SaaS register |
| Generic stock-photo people-at-laptops | Anti-instrument register |
| Lens-flare hero shots | Consumer-product register |
| Dashboard-on-laptop-screen mockups | Generic SaaS marketing |
| Page-load splash animations | Consumer-app register |
| Lottie illustrations | Consumer-app register |
| Parallax scroll | A10 anti-pattern |
| Gradient-mesh animation | A10 anti-pattern |
| Particle systems | A10 anti-pattern |
| Scroll-jacking | A10 anti-pattern |
| Pill-shape buttons / inputs | A13 anti-pattern |
| Floating-label form patterns | A13 anti-pattern |
| Drop-shadow elevation (>1px) | §3.6 anti-token |

### §8.4 Forbidden copy tokens (word-boundary enforced)

Any copy authored against this substrate MUST pass `\b(forbidden-token)\b` grep. Forbidden tokens:

```
\bAI-powered\b
\bAI[- ]first\b
\bnext[- ]generation\b
\brevolutionary\b
\bharness\b
\bunlock\b
\bsupercharge\b
\bgame[- ]changer\b
\bdisrupt\b
\bdisruptive\b
\bcutting[- ]edge\b
\bbleeding[- ]edge\b
\bstate[- ]of[- ]the[- ]art\b
\bworld[- ]class\b
\bbest[- ]in[- ]class\b   ← see exception below
\bseamless\b
\bseamlessly\b
\bblazing[- ]fast\b
```

**Documented exceptions (coincidental-collision per `feedback_hard_constraint_word_boundary`):**
- "best-in-class" appears in Sophia's ratified narrative ("best-in-class open-source components") — Sophia narrative IS load-bearing copy and substrate respects upstream authority. Token forbidden in NEW substrate-authored copy; preserved verbatim in Sophia citations.

---

## §9 — Per-surface inheritance rules

Downstream surfaces (per-surface specs in later cycles) MUST follow these inheritance rules.

| Rule | Statement |
|---|---|
| **R1 — Token reference, not redefine** | Per-surface code consumes role tokens (`type.body`, `color.semantic.text.primary`) by reference. Per-surface code MUST NOT redefine atomic tokens (`color.verdaca.oxblood`, `font.size.16`) locally. |
| **R2 — Mode declaration at root** | Per-surface declares its mode ONCE at the root (`data-mode="light"` or `"dark"`); component code never branches on mode. Mode-switch is a single root attribute change. |
| **R3 — Surface-intent rule (per A7 / D-6)** | Marketing first-touch surfaces (`verdaca.ai` / `verdaca.com` hero, landing pages, sales one-pagers, case-study pages) = **light-canonical** (cream canvas; Patek-brochure register). Charcoal-accent-bands mitigation permitted: heavy charcoal sections within light hero (read as "instrument bezel" interrupting the cream paper) preserve dark register presence in marketing without fracturing the canvas. Demo / deck / product-UI surfaces = **dark-canonical** (charcoal canvas; Caravaggio Slide 1 deck-hero precedent + tools-of-work register). Per-surface deviation requires explicit team-lead disposition. |
| **R4 — Component primitive composition only** | New visual patterns at per-surface MUST compose existing primitives (§6) before inventing. New primitives = halt-class, surface to design-substrate maintainer (substrate v0.x bump). |
| **R5 — Metric + caveat unit indivisible** | Any rendering of a Stage-1–6 metric MUST use the §6.9 unit complete with caveat. Metric without caveat = halt-class. (Per memory `project_praxis_stage5_6`.) |
| **R6 — Supplier credit cannot be hidden** | **Permitted placements:** in-flow body content, dedicated supplier-cite block (§6.4), sidebar, right-rail, compact column. **Forbidden:** collapsed-by-default, behind-tab, footer-relegated, any treatment that requires user interaction to reveal (e.g., a "show suppliers" toggle is not technically a footer but achieves the same hiding — banned). Visible-by-default in any surface that touches the BOM. Supplier list is quality signal — per Sophia pillar #2. |
| **R7 — Brand-name agnostic** | Substrate references brand by slot (`wordmark slot`, §6.1), not by literal `VERDACA` string. If Verdaca → Nuagio rename lands, only the wordmark art changes; substrate tokens, primitives, and rules survive intact. (Caveat: `marque-hero` / `marque-header` type roles are tuned for `VERDACA` letterforms — Nuagio's `g` descender would require a tracking re-pin per `docs/brand-comparison-verdaca-vs-nuagio.md` §3.) |
| **R8 — Forbidden-token grep gate** | Per-surface CI MUST run §8.4 grep gate on any copy file. Failures block commit. |
| **R9 — Accessibility floor non-negotiable** | All per-surface QA MUST verify §3.1 WCAG ratios on every text-on-background pair shipped. New combinations not in the §3.1 table MUST be computed and added. |
| **R10 — Font-loading per-surface responsibility** | Per-surface MUST set `font-display: swap` (or per-role-justified equivalent — e.g., `font-display: optional` for `type.marque-hero` if FOUT mid-render of the chassis label is brand-identity-load-bearing) to avoid FOIT. Web-font hosting strategy is per-surface implementation responsibility; substrate provides font-stacks only. |

---

## §10 — A4-caveat templates

**Pre-Stage-7 ratification (current state):**

```
metric.caveat.pre_stage7 = "(internal scoring; A4 deferred)"
```

**Post-Stage-7 ratification (future state, value-fill on ratification day):**

```
metric.caveat.post_stage7 = "(internal scoring; A4 ρ ≥ {value} validated {YYYY-MM-DD})"
```

**Substitution rule:** Until `project_praxis_stage5_6` memory transitions Stage-7 status to RATIFIED with confirmed ρ value, `metric.caveat.pre_stage7` is the only legal rendering. On ratification day, value-fill `{value}` and `{YYYY-MM-DD}`, then run `feedback_corrigendum_paired_sweep` discipline across this substrate doc + all per-surface specs that consumed the caveat.

**Sweep-target list (maintain at promotion to v1.0):**
- This substrate doc §6.9 + §10
- Every per-surface spec that includes a metric + caveat unit
- Marketing site case-study pages
- Deck slides citing the metric
- Sales one-pagers
- Product-shell self-demo dashboards

---

## §11 — Mobile compression rules (per A15)

| Breakpoint | Behavior |
|---|---|
| `≥1024px` (desktop) | Full substrate; `space.64` section gaps; 12-col grid; hero patent-drawing horizontal exploded-view |
| `768–1023px` (tablet) | `space.48` section gaps; 8-col grid; `space.24` container padding; type-display **stable** (no scale collapse); hero patent-drawing **stable** horizontal but compressed |
| `<768px` (mobile) | `space.32` section gaps; 4-col grid; `space.16` container padding; type-display / marque / headline collapse one scale step (per §5.2 table); **hero patent-drawing stacks vertically** (the exploded-view doesn't compress further horizontally — it stacks); supplier-cite block columns wrap into stacked label/value pairs |

**Threshold rationale (768px not 1024px for hero stack):** The hero exploded-view illustration includes 6 sub-assemblies above a labeled chassis. At tablet (768–1023px) the horizontal layout still holds with proportional shrink — the illustration is designed to read at deck-aspect. Below 768px (typical phone), the horizontal aspect collapses below illustration legibility threshold; vertical stack is mandatory. Pinning the stack threshold at 768 (not 1024) preserves the deck-equivalent horizontal hero across desktop AND tablet, which matters for trade-show iPad demos and tablet-bound enterprise procurement viewers.

**Generous-spacing principle preserved on mobile:** `space.32` section gaps on mobile is still wider than Linear / Notion mobile defaults (~16px). Industrial-editorial restraint scales down in absolute pixels but stays relatively-generous against consumer-SaaS mobile baselines.

---

## §12 — File outputs (Style Dictionary compile chain)

Substrate JSON tokens (§3 / §4 / §5) compile through Style Dictionary into the following per-platform outputs (build chain spec; not authored at v0.1, declared for v1.0 promotion):

| Output | Consumer |
|---|---|
| `dist/css/tokens.css` | Web (CSS custom properties) |
| `dist/scss/_tokens.scss` | Web (SCSS variables for build-time use) |
| `dist/js/tokens.js` (ESM) | Web component libraries; React / Vue / Svelte |
| `dist/json/tokens.flat.json` | Tooling integrations (Figma, etc.) |
| `dist/ios/Tokens.swift` | iOS native (if/when product-shell native apps land) |
| `dist/android/colors.xml` + `dimens.xml` | Android native (same) |

**v0.1 commitment:** JSON source-of-truth authored in this doc; Style Dictionary `config.json` + npm pipeline land at v1.0 promotion.

---

## §Appendix-A — Hex audit table

For each color token, the chosen value plus 2–3 alternates with rationale. Substrate-locked at v0.1; revisitable at v0.2 if downstream surface QA surfaces a register issue.

| Token | Chosen v0.1 | Alternates | Rationale for chosen |
|---|---|---|---|
| `color.verdaca.oxblood` | `#6B1F25` | `#5A1A1F` (deeper, closer to dried-blood; reads more sober but loses some chromatic life on charcoal); `#7A2128` (warmer, closer to Cabernet; risks bright-red drift at smaller sizes) | Mid-band; auto-marque burgundy register; passes WCAG AAA on cream (10.2:1); maintains identity on both modes without drift |
| `color.verdaca.charcoal` | `#1F2226` | `#1A1D20` (deeper, near-true matte black; risks reading as Vercel/GitHub default); `#26292C` (lighter, more "warm-gray"; loses instrument-bezel weight) | Cool-neutral matte; clearly distinct from pure black; reads as anodized aluminum / brushed steel surface |
| `color.verdaca.cream` | `#F2EDE2` | `#F5F1E8` (lighter; risks reading as default web-cream); `#EDE8DC` (warmer; risks reading as parchment / luxury-stationery register) | Mid-band warm off-white; reads as "printed brochure paper" not "web canvas" |
| `color.verdaca.graphite` | `#42454A` | `#3A3D40` (darker; loses contrast against charcoal in dark-mode use as line color); `#48494C` (lighter; loses body-type contrast on cream below AAA) | Mid-band; AAA on cream for body type; visible as line/divider on both canvases |
| `color.verdaca.bronze` | `#967853` | `#8B6F47` (deeper bronze; reads more antique/aged); `#A08862` (warmer/brassier; risks gold-luxe register) | Mid-band machined-bronze; reads as instrument-tier seal / version-pin tone |
| `color.verdaca.steel` | `#979CA3` | `#8B9099` (cooler/darker; risks gunmetal register); `#A0A5AC` (lighter; risks Apple-silver consumer-tech register) | Mid-band brushed-steel; cool companion to bronze without competing |

---

## §Appendix-B — Deferred decisions log

Decisions surfaced during substrate authoring but deferred. Maintained so they don't get lost at v1.0 promotion.

| # | Decision | Deferred to | Rationale |
|---|---|---|---|
| D-1 | Logo wordmark serial-numbered art | Post Verdaca-vs-Nuagio team-lead disposition (`docs/brand-comparison-verdaca-vs-nuagio.md`) | Brand-name lock pending; substrate slot defined, art held |
| D-2 | Söhne / Söhne Mono paid-license commission | Team-lead paid-spend authority + design-substance team request | Inter Tight + JetBrains Mono cover render-truth; Söhne is paid-upgrade variant |
| D-3 | GT Sectra Book Italic paid-license commission | Same as D-2 | Source Serif 4 covers free-tier render-truth; GT Sectra is paid-upgrade |
| D-4 | Supplier line-art logo commissions (in-house line-art versions of Mem0 / Letta / TONL / etc.) | Per-asset cycle if a downstream surface demands logo rendering beyond typographic citation | Caravaggio Slide 2 BOM precedent uses typographic citation only; substrate canonical = typographic |
| D-5 | Product-shell glyph designs (5 glyphs: Studio / Factory / Shield / Pipeline / Ops) | Per-shell cycle | Substrate pins slot + character spec only |
| D-6 | Mode-posture default for marketing | RESOLVED 2026-05-03 by team-lead: **light-canonical for marketing first-touch** (this disposition encoded in §9 R3) | — |
| D-7 | A4 caveat post-Stage-7 ρ value + validation date | Stage 7 ratification ceremony | Template defined in §10; value-fill on ratification |
| D-8 | Style Dictionary build pipeline (config + npm package + CI) | v1.0 promotion ceremony | JSON source-of-truth authored at v0.1 |
| D-9 | Promotion to `docs/design-system-substrate-v1.0.md` (git-tracked) | Separate ceremony when substrate has been consumed by ≥1 per-surface cycle **without halt-class amendment** | v0.1 is workshop register per `feedback_preload_tracking_status_verification`; v0.2 incremental refinement permitted without resetting promotion clock |
| D-10 | Per-surface specs (marketing site IA, deck slide-by-slide beyond Caravaggio Slides 1–3, per-shell UI shells, billing UI, integration-catalog UI, output templates, onboarding/empty-state) | Per-surface cycles | Substrate scope is substrate only |

---

## §Appendix-C — Provenance

| Substrate decision | Source authority |
|---|---|
| Color = ownership; suppliers as line-art | `docs/pipeline-stage9.md` §1.7 (Caravaggio rule, ratified) |
| Charcoal canvas (dark mode) for deck | `docs/18.04.2026.md` Round 2 Caravaggio Slide 1 spec ("matte charcoal background") |
| BOM cite block format (NAME · ROLE · VERSION · LICENSE) | `docs/18.04.2026.md` Round 2 Caravaggio Slide 2 spec verbatim |
| Station-sequence (PIN → TEST → RE-RATIFY → SHIP) | `docs/18.04.2026.md` Round 2 Caravaggio Slide 3 spec verbatim |
| Sophia three pillars (renderable as `type.narrative`) | `docs/18.04.2026.md` Round 2 Sophia narrative spine, ratified |
| "Toyota doesn't forge its own steel…" diffuser | `docs/18.04.2026.md` Round 2 Sophia procurement diffuser, ratified |
| Industrial-editorial register (Patek / Leica / Porsche reference set) | `docs/brand-comparison-verdaca-vs-nuagio.md` §3 |
| Anti-references (Linear / Notion / Vercel / Anthropic.com) | Same + handoff §4.3 verbatim |
| Söhne / Inter Tight type family | `docs/brand-comparison-verdaca-vs-nuagio.md` §3 + handoff §4.2 |
| A4-caveat language ("internal scoring; A4 deferred") | Memory `project_praxis_stage5_6` |
| Forbidden-token word-boundary discipline | Memory `feedback_hard_constraint_word_boundary` |
| Substrate-vs-tracked-doc placement (gitignored workshop) | Memory `feedback_preload_tracking_status_verification` |
| Light-canonical marketing default | Team-lead disposition 2026-05-03 (D-6) |
| Asymmetric type-family polarity (sans free-primary, serif paid-primary) | Team-lead disposition 2026-05-03 (D-3) |
| W3C Design Tokens spec + Style Dictionary | Team-lead disposition 2026-05-03 (token format) |
| 768px hero stack threshold | Substrate authoring 2026-05-03 (A15 clarification) |

---

**End of Verdaca Design System Substrate v0.1.**
