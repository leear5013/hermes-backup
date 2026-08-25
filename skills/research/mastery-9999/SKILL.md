---
name: mastery-9999
description: Master any topic via top-voted community workflows.
---

# Mastery 9999 — Acquire Expert-Level Skill on ANY Topic

Turn any "I want to be 9999 at X" request into a community-verified mastery
path: discover what the most-voted practitioners actually do, distill it into
a working playbook, and build a reusable skill. You become the expert the
community trusts — because you learn from them first.

## Trigger
- "Master X", "make me 9999 in X", "best way to learn X", "what's the best
  workflow for X", "top skills for X", "I want to be an expert at X"
- Any topic where the user wants the DEFINITIVE community-vetted method.

## The Mastery Protocol (always, in order)

### 1. DISCOVER — sweep the top communities for the topic
Search in this priority (batch where possible):
- **Reddit**: `reddit-top.py <sub> <hours> <n>` (highest-reach by comment count) +
  `web_search("<topic> best way reddit")` + `site:reddit.com` queries.
  Pull real comments via ArcticShift (`arctic-shift.photon-reddit.com`) — top
  threads sorted by score. Read the *practitioners*, not just the OP.
- **GitHub**: `gh search repos "awesome-<topic>"` / api.github.com
  `search/repositories?q=awesome+<topic>&sort=stars` — star counts = community
  vetted. Also find the topic's canonical repos (highest stars, most forks).
- **Hacker News**: Algolia API `https://hn.algolia.com/api/v1/search?query=<topic>&tags=story&numericFilters=points>100` — filter to high-point stories, read the top comments.
- **X**: `xurl search "<topic>" -n 20` (if authed) — find the voices the
  community retweets.
- **YouTube/courses**: only after the above — find the courses the threads
  repeatedly name (don't trust ads/SEO).

### 2. RANK — by community signal, not vibes
- Reddit: comment count + comment scores (not just upvotes).
- HN: points >100 = durable signal. GitHub: stars.
- Cross-community: a resource named in ≥2 independent communities is gold.
- Prefer RECENT (last 6-12 months) for fast-moving topics (AI, dev tooling);
  classic books/curricula for stable topics (math, data engineering).

### 3. EXTRACT — the actual workflow from practitioners
From the top threads, extract:
- The exact steps people take (their process, not their opinion)
- Tools they name repeatedly
- Time estimates and milestones ("how long until X")
- Pitfalls they warn about
- What the "experts" in the thread disagree on (flag it, don't smooth it)

### 4. CROSS-VALIDATE
- Every core claim needs ≥2 independent sources (different communities or
  different top threads).
- If communities conflict (e.g. Reddit says A, HN says B) — present both with
  their contexts, don't pick one silently.

### 5. DISTILL — build the skill/playbook
Write a structured SKILL.md:
```
name: <topic>-<domain>
description: <≤57 chars, trigger first, period.>
---
## Trigger
## The Method (numbered steps with exact commands/tools)
## Pitfalls (what the community hit so you don't)
## Verification (how to prove it worked)
## Sources (URLs + dates)
```
Save to `~/.hermes/skills/<category>/<name>/` via skill_manage, AND a
summary note in the vault (`hermes-vault/skills/<topic>.md`). Commit vault.

### 6. VERIFY — prove it hands-on
Run the core loop of the new skill once myself on a real mini-task. Real
output only — never a plausible-but-unrun demo.

### 7. REPORT — the mastery path
Deliver: what the top communities said (with links + vote signals), the
distilled playbook, what we built, and the one-sentence "9999 takeaway".

## Topic → Community mapping (start points)
| Topic | Communities |
|---|---|
| Dev/data engineering | r/dataengineering, r/ExperiencedDevs, HN, GitHub awesome-data-engineering |
| AI/LLM agents | r/LocalLLaMA, r/hermesagent, r/ClaudeAI, HN, GitHub awesome-llm-apps |
| Cybersecurity/OSINT | r/OSINT, r/cybersecurity, Trace Labs CTFs, OSINT-BIBLE |
| Design/creative | r/web_design, Designer News, Awwwards, popular-web-designs skill |
| Careers/jobs | r/cscareerquestions, r/jobs, levels.fyi, Blind (careful, login) |
| Gaming/hobbies | r/gamingsuggestions + topic subs (r/AndroidGaming etc.) |
| Anything else | find the topic's biggest subreddit(s) + HN + GitHub search |

## Pitfalls (from real use)
- **Single-thread bias**: one Reddit thread is not consensus. Need 2+.
- **Fashion vs expertise**: TikTok/trending ≠ master-tier. Weight HN + r/ExperiencedDevs + starred repos higher.
- **Stale advice**: check dates; AI/dev advice older than a year decays fast.
- **Summaries over sources**: always go read the actual top comments; AI
  summaries of threads lose the exact steps and warnings.
- **No verification**: a playbook you never ran is a hypothesis. Run it.
- **Scope creep**: answer the ONE mastery question, then stop.

## Integration (agent mastery)
- Every new topic skill = a new SKILL.md + vault note. Memory separation:
  facts → vault, procedures → skills.
- When a user later corrects the workflow → patch the skill (corrections =
  spec debt).
- Reuse existing skills instead of recreating (reddit skill for Reddit
  access, osint-9999 for investigations, web-research for profile hunts).

## Sources (canonical)
- reddit-top.py + ArcticShift (comment counts/reach)
- HN Algolia API (points-filtered search)
- GitHub search API (stars)
- osint-9999 skill (verification/ethics for research)
