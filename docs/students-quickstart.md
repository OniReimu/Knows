# Knows for Students — the 3-minute quickstart

You searched a pile of papers. Now you want the two things that actually matter: **what should I work on, and is my idea any good?** That's exactly what Knows is for.

You do **not** need to learn any commands, flags, or "sub-skills." Just talk to your AI assistant in plain English while the Knows skill is installed. Here are the only three things you ever need to say.

---

## 1. Find papers

> **Say:** *"find papers about diffusion model watermarking"*

You get a ranked list of relevant papers, each already structured so the assistant can reason about it (claims, numbers, limitations) without re-reading the whole PDF. Grab 10–20 on your topic — they become the raw material for steps 2 and 3.

---

## 2. Get research directions worth pursuing

> **Say:** *"what should I work on next in diffusion model watermarking?"*
> or *"where are the open gaps in this area?"*

You get a short list of candidate directions. The important part: **every direction is tied to a real paper that said this was open or unsolved** — it is not the assistant free-associating. Each one comes tagged with the kind of move it makes (e.g. *remove a load-bearing assumption*, *swap the operator*, *reframe the problem*) so you can see the shape of the idea at a glance.

If a topic is too thin on the hub, it will **tell you** instead of inventing directions. That "I don't have enough here" answer is a feature — trust it and widen your search.

---

## 3. Check whether an idea is novel ← the step most people miss

> **Say:** *"is this idea novel: give per-phase credit in long-context RL instead of one score per rollout, so the training signal survives at 128K context"*

This is the one your assistant couldn't really do before. It takes **your idea** (yours, or one from step 2), breaks it into four parts —

- **problem** (what you're tackling)
- **mechanism** (the actual technical move)
- **insight** (why it works)
- **domain** (where it applies)

— finds the closest existing papers, and tells you how much of your idea is already out there. You get a **novelty level** and a one-word **verdict**:

| Verdict | What it means | What to do |
|---|---|---|
| **PURSUE** | no close prior work found | go — and it names the part that makes you novel |
| **DIFFERENTIATE** | someone's nearby, but you're distinct | keep going, but sharpen the one part it flags |
| **ALREADY DONE** | a paper already does this | it names the paper — read it before you spend a month |

**Novelty level 1–5**: 5 = nothing like it found, 3 = same area but your mechanism is distinct (the common "defensible" zone), 1 = a single paper matches all four parts (you're scooped).

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

Describe a **mechanism**, not just a topic. The tool needs something concrete to check.

- ❌ *"something about long-context RL"* → too vague; it collides with nothing because it says nothing, so it will ask you to be specific.
- ✅ *"reweight the RL advantage per reasoning phase instead of one score per rollout"* → a real mechanism it can check against prior work.

## An honest caveat (read this once)

Knows checks your idea against the papers **it can see** on the hub. A "novel / PURSUE" verdict means *no scoop was found in that coverage* — not a guarantee that none exists anywhere. For a high-stakes go/no-go (your thesis topic, a paper you're about to write), do one more manual pass on Google Scholar / arXiv before you commit. Knows narrows the risk; it doesn't erase it.

---

### That's the whole thing

Three phrases — *find papers* → *what should I work on* → *is my idea novel* — cover 95% of what you'll do. Everything else Knows can do (summarize a paper, draft related work, compare two papers) works the same way: just ask in plain English.
