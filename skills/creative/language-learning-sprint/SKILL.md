---
name: language-learning-sprint
description: Teach a language to B1 level in 30 days with daily sessions.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [language-learning, Spanish, B1, CEFR, study-plan, immersion]
---

# Language Learning Sprint (1 Month → B1)

A structured 30-day plan to reach CEFR B1 in any language, designed for Hermes-led daily sessions. B1 means: handle travel situations, describe experiences, give opinions and reasons, understand main points of clear speech. This skill focuses on Spanish but generalizes to any target language.

Hermes acts as tutor, conversation partner, and quizmaster across daily sessions. It does NOT replace immersion or speaking practice — it structures the self-study and fills the gaps.

## When to Use

- "Teach me Spanish / French / German in 1 month"
- "I want to reach B1 in [language] by [date]"
- "Help me learn [language] — I'm a beginner"
- "What should I study today for [language]?"

## Prerequisites

- Target language (default: Spanish)
- ~60-90 minutes/day availability
- Anki or similar SRS app for vocabulary (free)
- Hermes voice mode (optional, for pronunciation drills)
- No paid courses required — free resources only

## How to Run

Hermes runs daily sessions via chat. Each session is ~30-45 min. The user also does solo Anki + listening outside sessions. Call `cronjob(action='create')` for a daily reminder if the user wants it.

## Quick Reference

| Phase | Days | Focus | Daily vocab target |
|---|---|---|---|
| Foundation | 1-7 | Alphabet, pronunciation, present tense, core 300 words | 50 words/day |
| Build | 8-18 | Past tenses, future, conditional, 1000 words total | 40 words/day |
| Consolidate | 19-25 | Subjunctive intro, connectors, 2000 words total | 30 words/day |
| Sprint | 26-30 | Full conversation practice, weak-point drilling | Review only |

## Procedure

### 1. Assessment (Day 0, ~10 min)

Ask the user:
- What language? (default Spanish)
- Native language? (affects grammar explanations — Arabic speakers handle Romance noun gender easily)
- Any prior exposure?
- Daily time available?

Then deliver the **Day 0 packet**: alphabet guide + pronunciation key + first 20 essential phrases (greetings, "I want", "where is", numbers 1-20).

### 2. Daily Session Structure (30-45 min)

Each daily session follows this fixed format:

1. **Warm-up (5 min)** — Quick oral quiz on yesterday's vocabulary (5-8 words, `text_to_speech` for listening + user types/speaks answers)
2. **New grammar (10 min)** — One grammar point, explained with examples in English, then practiced in target language. Use tables, not paragraphs. Connect to Arabic where helpful (e.g., Spanish verb conjugation is simpler than Arabic).
3. **New vocabulary (10 min)** — 15-20 new words with example sentences, mnemonic devices, and a mini-story connecting 5-8 of the new words
4. **Controlled practice (10 min)** — Fill-in-the-blank, sentence building, translation exercises (target→native and native→target)
5. **Free practice (5 min)** — Roleplay scenario using today's grammar + vocabulary (e.g., "you're at a restaurant ordering food using past tense")
6. **Preview** — List the 5 key things to review before tomorrow + assign Anki cards

### 3. Vocabulary Selection

**Priority order for B1 Spanish:**
1. **Top 300 high-frequency words** (Days 1-7): ser/estar/haber, common nouns (time, food, family, body), question words, connectors
2. **Functional vocabulary** (Days 8-18): travel, shopping, health, work, past-tense verbs
3. **Abstract vocabulary** (Days 19-25): opinions, emotions, comparisons, hypotheticals
4. **Review only** (Days 26-30): weak spots from Anki stats

Generate vocabulary lists as structured tables: `word | pronunciation | meaning | example sentence`.

### 4. Grammar Sequence (Spanish)

| Day | Grammar point |
|---|---|
| 1-2 | Ser vs Estar, subject pronouns |
| 3-4 | Present tense regular verbs (-ar, -er, -ir) |
| 5-6 | Irregular present (tener, ir, querer, poder, hacer) |
| 7-8 | Questions, negation, articles (el/la/los/las, un/una) |
| 9-10 | Prepositions (a, de, en, con, por, para) |
| 11-12 | Preterite tense (regular) |
| 13-14 | Preterite tense (irregular: fui, hice, tuve, estuve) |
| 15-16 | Imperfect tense |
| 17-18 | Preterite vs Imperfect distinction |
| 19-20 | Future tense + informal future (ir + a + infinitive) |
| 21-22 | Conditional tense |
| 23-24 | Intro to subjunctive (present subjunctive, basic triggers) |
| 25-26 | Relative pronouns, comparatives, superlatives |
| 27-28 | Connectors (pero, aunque, sin embargo, además) |
| 29-30 | Review weak areas, full conversation practice |

### 5. Immersion Assignments (outside Hermes sessions)

Assign these daily — non-negotiable for B1 in 1 month:

| Activity | Time | Resource |
|---|---|---|
| Anki vocab review | 15 min | User's SRS app with Hermes-generated decks |
| Listening | 15 min | Dreaming Spanish (YouTube), Coffee Break Spanish, Notes in Spanish |
| Reading | 10 min | Readlang (free browser extension) for graded readers |
| Shadowing | 5 min | Repeat audio from Dreaming Spanish, mimic rhythm |

### 6. Weekly Checkpoints

At end of each week (Days 7, 14, 21, 28), run a **mini DELE B1 practice test**:
- Reading comprehension (1 passage + 5 questions)
- Listening (ask user to describe what they heard from a clip)
- Grammar accuracy check (10 fill-in-blank sentences)
- 5-minute free conversation topic

Track scores. If below 60% on any skill, adjust next week's focus.

### 7. Roleplay Scenarios (for speaking practice)

Use Hermes `text_to_speech` to simulate real conversations. Scenarios by week:
- **Week 1:** Introducing yourself, ordering food, asking directions
- **Week 2:** Talking about past weekend, describing your home city, making plans
- **Week 3:** Expressing opinions about news, job interview, doctor visit
- **Week 4:** Telling a story, debating a topic, handling unexpected situations

### 8. How Hermes Presents Each Session

- Lead with the day number and phase (e.g., "Day 12 — Build Phase, past tense irregulars")
- Use tables for grammar, not walls of text
- Include IPA pronunciation for new words
- After grammar explanation, immediately give 5 practice sentences for the user to complete
- End each session with tomorrow's preview + 5 review words
- Use `text_to_speech` for pronunciation demos (set speed=0.8 for learner-friendly pace)

## Pitfalls

1. **B1 in 1 month is aggressive.** It requires 60-90 min/day EVERY day. Missing 2+ days in a week breaks the sprint. Be honest with the user about this commitment.

2. **Don't over-teach grammar.** B1 Spanish needs 6-8 tenses, not all 14. The subjunctive is introduced but not mastered at B1. Focus on communication, not perfection.

3. **Arabic speakers have advantages.** Verb conjugation in Arabic is more complex than Spanish. Noun gender exists in both. Vowel sounds are familiar. Mention this to build confidence.

4. **Anki decks must be curated, not downloaded.** A generic "Spanish 5000" deck wastes time. Generate targeted vocabulary lists per week's theme using Hermes, export as CSV for import.

5. **Listening is the hardest skill to fast-track.** Push Dreaming Spanish from Day 1. Comprehensible input (i+1) is more effective than grammar drills for listening.

6. **Don't let the user only do passive study.** Reading + listening alone won't reach B1. Speaking and writing (even to Hermes) must be part of every session.

7. **Free resources are sufficient.** Don't recommend paid apps (Babbel, Pimsleur). Use: Anki (free), Dreaming Spanish (free YouTube), Readlang (free tier), Language Transfer (free audio course), ChatGPT/Hermes for practice.

## Verification

Weekly checkpoint test at Day 28 should confirm:
- Can understand main points of clear standard speech on familiar topics
- Can produce connected text on topics of personal interest
- Can describe experiences, events, hopes, and ambitions
- Can give reasons and explanations for opinions

If the user passes 4/5 questions on a DELE B1 reading comprehension passage, they are at B1.
