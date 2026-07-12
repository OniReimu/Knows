# Knows for Students — the 3-minute quickstart

You searched a pile of papers. Now you want the two things that actually matter: **what should I work on, and is my idea any good?** That's exactly what Knows is for.

You do **not** need to learn any commands or setup jargon. Once it's installed, just talk to your AI assistant in plain English. Here are the only three things you ever need to say.

---

## Before you start (30 seconds)

Knows is a "skill" your AI assistant loads. **If your instructor already set it up for you, skip this.** Otherwise, in your terminal:

```
npx skills add OniReimu/Knows
```

Then open your assistant (e.g. Claude Code) and just talk to it — everything below is plain English, no commands.

## What Knows actually searches (read this once)

Knows works off a **shared online library of research papers** (the "hub" at knows.academy), where each paper is pre-structured so your assistant can reason about it fast. You give it a **topic**; it finds the relevant papers *there*.

It does **not** read the PDFs sitting in your local folder — so if you already collected papers somewhere else, you don't feed them in; you just point Knows at the same topic. And if your specific niche is thinly covered on the hub, Knows will **tell you** rather than make things up — that's your cue to also search Google Scholar / arXiv by hand.

---

## 1. Find papers

> **Say:** *"find papers about diffusion model watermarking"*  *(works for any field — use your own topic)*

You get a ranked list of relevant papers, each already structured (claims, numbers, limitations) so the assistant can work with them without re-reading full PDFs.

## 2. Get research directions worth pursuing

> **Say:** *"what should I work on next in diffusion model watermarking?"*
> or *"where are the open gaps in this area?"*

You get a short list of candidate directions. The important part: **every direction is tied to a real paper that said this was open or unsolved** — not the assistant free-associating. Each is tagged with the kind of move it makes (e.g. *remove a load-bearing assumption*, *swap the operator*, *reframe the problem*) so you can see the shape of the idea at a glance.

## 3. Check whether an idea is novel ← the step most people miss

> **Say:** *"is this idea novel: give per-phase credit in long-context RL instead of one score per rollout, so the training signal survives at 128K context"*

This is the one your assistant couldn't really do before. It takes **your idea** (yours, or one from step 2), breaks it into four parts — **problem** (what you're tackling), **mechanism** (the actual technical move), **insight** (why it works), **domain** (where it applies) — finds the closest existing papers, and tells you how much of your idea is already out there:

| Verdict | Novelty level | What it means | What to do |
|---|---|---|---|
| **PURSUE** | 4–5 | no close prior work found | go — and it names the part that makes you novel |
| **DIFFERENTIATE** | 3 | someone's nearby, but you're distinct | keep going, but sharpen the one part it flags |
| **ALREADY DONE** | 1–2 | a paper already does this | it names the paper — read it; you can often still **pivot** (change the mechanism) rather than drop it |

*(Level 5 = nothing like it found; level 1 = one paper matches all four parts, i.e. you'd be scooped.)*

Two things PURSUE does **not** mean: it doesn't mean your idea is automatically **important or publishable** — it's a green light to dig, not a guarantee. And **checking an idea doesn't publish it anywhere** — it's just a search, so your unpublished idea stays yours.

---

## Put it together (one sentence)

> **Say:** *"find me a research idea in <topic> and check that it's novel"*

That runs all three steps in a row and hands you ranked idea cards — direction + the move it makes + novelty verdict — so you can pick one and start.

---

## The one mistake to avoid

Students often ask *"is **this paper** novel enough?"* — but a published paper's novelty tells you nothing about **your** project. Ask about **your own idea** instead:

- ❌ *"is this ICLR paper novel?"* → not useful; it's already published.
- ✅ *"has anyone already done <my idea>?"* → this is the question that saves you months.

## The one rule that makes it work

Describe a **mechanism** (the concrete technical move you'd make), not just a topic. The tool needs something specific to check against prior work.

- ❌ *"something about long-context RL"* → too vague; Knows will tell you it can't check a topic and ask for the actual mechanism.
- ✅ *"reweight the RL advantage per reasoning phase instead of one score per rollout"* → a real mechanism it can collide against prior work.

## An honest caveat (read this once)

Knows checks your idea against the papers **it can see** on the hub. A "novel / PURSUE" verdict means *no scoop was found in that coverage* — not a guarantee that none exists anywhere. For a high-stakes decision (your thesis topic, a paper you're about to write), do one more manual pass on Google Scholar / arXiv before you commit. Knows narrows the risk; it doesn't erase it.

---

### That's the whole thing

Three phrases — *find papers* → *what should I work on* → *is my idea novel* — cover 95% of what you'll do. Everything else Knows can do (summarize a paper, draft related work, compare two papers) works the same way: just ask in plain English.
