---
name: hermes-persona-management
description: Use when editing or merging the Hermes SOUL.md persona.
---

# Editing Hermes SOUL.md personas

SOUL.md is the persona layer loaded at session start; Hermes' base system prompt sits underneath it. Users iterate on it frequently (tone, working style, task modes). This skill encodes the user's verified workflow and preferences.

## Workflow (user's preferred, verified 2026-08)
1. **BACK UP FIRST** — `cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak.$(date +%Y%m%d-%H%M%S)` before any write. Keep the chain of backups: the user may want to diff or revert instantly.
2. **Confirm before a full swap** — replacing the entire persona changes operating identity; show the target content and get explicit sign-off (offer a multiple-choice clarify when the change is wholesale).
3. **Write, then verify** — use write_file, then read_file back: check line count, byte size, and key phrases to confirm it matches the agreed content exactly. Report the verification numbers to the user.
4. **State the backups** — tell the user the backup paths and how to revert.

## Merge pattern (dual-mode personas) — user's preferred approach
The user prefers **merging over wholesale replacement** when a new persona is task-specific:
- Keep the base identity (e.g. "Hermes Agent...") plus an everyday/conversational mode as the DEFAULT.
- Add the task-specific mode under its own header (e.g. "## Terminal / coding / system mode") with explicit trigger conditions ("switch when the task involves code, commands, files, or system work").
- Keep the two modes visually separated so behavior is predictable; default mode stays warm and human.

### User's live dual-mode SOUL.md (applied 2026-08, current state)
The user's current SOUL.md follows exactly this shape. Mode 1 is the everyday/conversational **default** (warm, creative, good judgment, no terminal discipline); Mode 2 is the terminal/coding mode carrying the "Terminal Bench" 5-step loop (TARGET → SOLVE FAST → RUN & CHECK → FIX & LOOP → FINAL GATE), proof-by-command, non-interactive terminal discipline, minimal changes. The user's work does NOT require terminal/coding day-to-day — so everyday mode stays the default and the terminal mode only engages when the task is code/commands/files/system work. Keep this split when editing further.

## Alternative: persona-as-skill (non-destructive)
Instead of replacing SOUL.md, paste the persona text into a skill and enforce it as the always-on default skill (pattern recommended by r/hermesagent users — the "Terminal Bench" SOUL.md author u/NinjaAlaska: "paste it into a skill and enforce default skill to force this skill always"). Safer for experimentation; keeps the base persona intact. Useful when the user only wants the behavior on specific task classes.

## Pitfalls
- SOUL.md changes apply to **new sessions/turns**, not retroactively mid-session.
- Persona settings are NOT in `~/.hermes/config.yaml` (that file holds terminal/compression/onboarding keys only) — they live in `~/.hermes/SOUL.md`.
- Never delete the previous version — timestamped backups are the revert path.
- A persona that demands "proof by command / final gate" behavior is terminal-mode material — don't let it leak into everyday chat mode unless the user asks.
