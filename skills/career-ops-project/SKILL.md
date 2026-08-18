---
name: career-ops-project
description: Use when user asks for Portfolio project evaluation — 6 dimensions (role signal, uniqueness, demoability, metrics, time to MVP, STAR potential), interview pack requirements.
version: 1.0.0
author: Hermes Agent (ported from santifer/career-ops)
license: MIT
metadata:
  hermes:
    tags: [career-ops, job-search, career, ai]
    related_skills: [career-ops-shared]
    upstream: https://github.com/santifer/career-ops
---

# Career Ops Project — Career-Ops for Hermes

> **Ported from [santifer/career-ops](https://github.com/santifer/career-ops) v1.9.0.**
> This skill runs on Hermes Agent. Tool references are adapted for Hermes native tools.
> Original copyright: Santiago Fernández de Valderrama, MIT License.

**URL:** {project-url}
**Legitimacy:** {High Confidence | Proceed with Caution | Suspicious}

Scoring matrix with 6 dimensions (1–5):

| Dimension | Weight | 5 = ... | 1 = ... |
|-----------|------|---------|---------|
| Signal for target roles | 25% | Directly demonstrates JD skill | Not related |
| Uniqueness | 20% | Nobody has done this | Very common |
| Demo ability | 20% | Live demo in 2 min | Code only, not visual |
| Metrics potential | 15% | Clear metrics (latency, cost, accuracy) | No metrics possible |
| Time to MVP | 10% | 1 week | 3+ months |
| STAR story potential | 10% | Rich story with trade-offs | Implementation only |

## "Interview Pack" Requirements

For each approved project:
1. **One-pager**: product + architecture + metrics + evaluation plan
2. **Demo**: live URL or 2 min recorded walkthrough
3. **Postmortem**: what worked, what didn’t, mitigations

## 80/20 Plan

- Week 1 → MVP with core metric
- Week 2 → polish + interview pack

## Verdicts

- **BUILD** → plan with weekly milestones
- **SKIP** → why and what to do instead
- **PIVOT TO [alternative]** → more impactful variant

