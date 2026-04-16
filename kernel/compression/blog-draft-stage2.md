# We Built the Compression Layer. Here's What We Measured.

*Praxis Build Log — Stage 2*

---

When you're paying per token, compression isn't a nice-to-have. It's arithmetic.

We just finished Stage 2 of the Praxis build: a four-layer compression pipeline sitting between your agents and the Claude API. This post documents what we built, how we measured it, and what the numbers actually mean.

## The Problem We're Solving

Multi-agent systems are verbose by nature. Conversation history grows. Tool call outputs bloat. Repeated data structures repeat. Every token you send is a token you pay for — twice: once on input, once when the model reads it back in the next turn.

Stage 1 (Pi-Mono) gave us exact per-request cost tracking in `decimal.Decimal`. Stage 2 gives us compression so those numbers go down.

## What We Built

Four compression layers, each with a different target:

**TONL** (Token-Optimized Notation Language) handles structured data — message arrays, tool call schemas, JSON payloads. It encodes repetitive fields into a tabular wire format that LLMs read correctly but that's significantly shorter than JSON. This is the workhorse for conversation history and agent-to-agent data passing.

**Forge** handles long conversations — it compacts old turns into semantic summaries using Claude itself, preserving the meaning without the verbatim history. Think of it as lossy compression with an LLM-powered codec. It fires at configurable token and turn thresholds.

**Caveman** handles LLM output — it strips grammatical overhead from agent-to-agent messages where prose polish is wasted. "User wants file sorted by date" compresses better than "The user has expressed a preference for sorting the file by date in descending order." Caveman ships feature-flagged off by default; it's a P1 activation item once we have production quality data.

**RTK** handles tool output — shell commands, git logs, file diffs. It routes command output through a Rust compactor that removes whitespace-heavy formatting before the text reaches the context window. Binary not on our dev host yet; stub mode passes through cleanly.

## The Architecture Principle: Cascade Isolation

None of these layers can crash the pipeline. If TONL fails on a malformed payload, the original payload continues to Forge. If Forge's LLM call fails, Caveman still runs. If RTK binary isn't present, tool output passes through raw.

We verified this with a deliberate TONL crash injection test. Pipeline completes, tags report the fallback, cost tracking continues uninterrupted. This is the property that matters for production: compression is strictly additive. Turning it on cannot break agent execution.

## What We Measured

We ran an A/B harness: every workload processed once with compression ON, once with compression OFF, same seed, same config hash.

**TONL on a 50-message uniform conversation array: 30.34% token reduction.**

That's not a projection. That's what we measured on a realistic conversation replay with alternating user/assistant turns. From 1,862 tokens down to 1,297.

Across all four workloads (including prose, which TONL doesn't compress, and a placeholder Forge fixture): **14.32% compound token reduction**.

The compound number is deliberately conservative — the Forge and Caveman workloads aren't fully wired yet. The ceiling is higher. But 30% on structured payloads is the repeatable result, and structured payloads are the majority of multi-agent traffic.

## Every Token Tracked From Inception

Because Stage 1 (Pi-Mono) is already running, every compressed request emits tags into the cost record:

```
compression.mode = on
compression.tokens.before = 1862
compression.tokens.after = 1297
compression.bytes.saved = 2263
```

This means the savings aren't an estimate. They're in the database, per-request, queryable, attributable to sessions and workflows. When we run a multi-agent workflow, we can report exact dollar savings from compression alongside exact total cost.

## What's Next

Stage 3: Memory & Cross-Session Learning.

Similar tasks should get cheaper over time. The first time an agent solves a problem type, Praxis pays full price. The second time, the memory layer retrieves the relevant context and skips the warm-up. Our target: 30–50% token reduction on repeated task patterns.

We're building this on a combination of Beads (versioned state), Mem0 (hybrid vector + graph retrieval), and Atelier (decision pattern extraction). The compression layer feeds directly into the memory write path — when we store experience, we store it compressed.

---

*Praxis is a multi-agent deliberation engine built on a measure-first philosophy. Every architectural decision is preceded by a cost baseline and validated against it.*
