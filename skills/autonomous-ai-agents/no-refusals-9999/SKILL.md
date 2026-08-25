---
name: no-refusals-9999
description: Reduce agent refusals; unlock autonomy within safe bounds.
---

# No-Refusals 9999 — Make Your Agent Say "Yes" (Safely)

Community-vetted playbook for maximizing agent willingness and autonomy.
Goal: an agent that does the work — not one that argues. Includes the
legit config layer (YOLO mode, permissions, model choice, SOUL.md) and
the model layer (abliterated/uncensored local models) for when you want
a fully unrestricted agent on YOUR hardware.

## When to use
- Agent refuses/hesitates on reasonable tasks
- You want maximum autonomy (auto-approve tools, no confirmation loops)
- You want an unrestricted personal agent (uncensored local models)
- You're building a "does whatever I ask" assistant

## The refusal taxonomy (know what you're fighting)
1. **Safety refusals** — the model's built-in guardrails (refusing things
   like harmful content). Two flavors:
   - Hard blocks (CSAM, bioweapons, attacks on infra, undermining AI
     oversight) — NOTHING legitimately removes these; don't waste time.
   - Soft blocks — respond to context/system config; reducible.
2. **Confirmation prompts** — the agent ASKS before acting (tool approval
   gates). This is the #1 "refusal" users mean. Fix = permissions/config.
3. **Persona refusals** — "I can't do that" from the system prompt/persona.
   Fix = SOUL.md / system prompt.
4. **Model refusal stickiness** — once a refusal enters context, smaller
   models latch onto it; rephrase or restart the turn.

## Layer 1 — LEGIT CONFIG (no model swap needed)
1. **YOLO / auto-approve mode** (Hermes): set `HERMES_YOLO_MODE=1` env →
   all tool calls auto-approved. Community-verified (SoloDev.app series).
   Alternative: config `command_allowlist` / tool permissions — allowlist
   the tools you trust (e.g. execute_code, terminal, file ops).
2. **Config per toolset**: enable toolsets you use (web, terminal, file,
   delegation) so the agent never lacks the tool it needs; missing tools
   cause "I can't" refusals.
3. **SOUL.md / persona**: define "you always act decisively, never ask
   permission for X, offer alternatives instead of refusing" — a strong
   operator persona reduces soft refusals across every session.
4. **Prompt hygiene**: give legitimate context (why the task, what you
   need) — soft blocks respond to context. Rephrase refusals instead of
   arguing; large models argue better than small ones.
5. **Skills**: procedures with exact commands reduce "I don't know how"
   refusals (mastery-9999 pattern).

## Layer 2 — MODEL CHOICE (fewer guardrails)
- **Stronger frontier models** refuse less / argue better (Opus/GPT-5
  tier). If budget allows, switch models first.
- **Local uncensored models**: abliterated / uncensored fine-tunes of
  Qwen, Llama, Mistral (e.g. Qwen3.5-9B Abliterated, Qwen2.5-14B
  roleplay/uncensored, Dolphin, Nous Hermes lineage). Community hubs:
  r/LocalLLaMA, r/LocalLLM, HuggingFace GGUF. Run via Ollama / llama.cpp /
  vLLM. Fully offline, zero refusals, but YOU own the responsibility.

## The safe-boundary rule (HARD)
- Legitimate work: your own data, authorized systems, public sources,
  self-hosted agents → max autonomy. YOLO it.
- Never: credential theft, account compromise, harassment/doxxing,
  weapon/CSAM content, attacks on systems you don't own. These stay
  refused even on uncensored models (they're not "censors", they're
  real-world harms).
- On Railway/cloud: an unrestricted agent is only as safe as its host —
  don't give an uncensored agent open-ended destructive access.

## Verification
- After config: run a task that previously refused → confirm it now
  executes without a prompt.
- After model swap: test the same prompts; confirm refusal rate dropped.
- Test hard-block categories once to know the boundary (expect refusal).

## Pitfalls
- YOLO mode + destructive command = no safety net. Use with care.
- Skill curator / over-trimming can re-add guardrails — check config after
  updates.
- Some providers (OpenRouter etc.) still filter even with good prompts —
  model choice is the lever, not the system prompt.
- Don't fight hard blocks; they're intentional.

## Sources
- SoloDev.app YOLO mode guide (solodev.app/running-hermes-agent-in-yolo-mode)
- The AI Map — "Why Does Claude Refuse" (soft vs hard blocks taxonomy)
- r/LocalLLaMA + r/LocalLLM uncensored model threads
- r/singularity Claude computer-use refusal list thread
- Hermes docs: personality/SOUL.md, configuration
