# Funded-Master's Research: One-Shot Workflow

Session-proven workflow for answering "is there a funded master's abroad for X (Egyptian student)?" — including when triggered by an X/Twitter post. Verified 2026-08-11 on an Egyptian AI-master's thread (Turkey/Italy/France/Spain + Netherlands), user profile = Data Engineering grad June 2026.

## Extraction of the trigger post (Twitter/X)
1. `web_extract` on x.com URLs **fails** with a ddsg search-only backend error — don't retry it.
2. Use the hermes-web-search-stack helper:
   `/opt/venv/bin/python /data/.hermes/skills/research/hermes-web-search-stack/scripts/extract_url.py "https://x.com/<user>/status/<id>"`
   Layer 1 (trafilatura) is usually enough (~785 chars for a photo post, includes Arabic text + quoted content). Returns JSON-ish text with `# layerN:` markers.
3. Read the Arabic text yourself — it often carries the actionable ask and community warnings (e.g. "don't do a master's in Turkey, jobs impossible for non-speakers; Fulbright best").
4. Skip xurl entirely for reading public posts — it's for authenticated engage actions, and it wasn't installed here anyway.

## One-shot research sequence (batch searches, no follow-up loops)
Single parallel batch (4–6 queries) covering: the flagship EU program (Erasmus Mundus), the reliable country-specific ones in the ask (DAAD/Germany, Sweden SI), and the explicit country add-on (Netherlands/Holland Scholarship). Then ONE verification batch for the less-known or newly-mentionable programs (VLIR-UOS/Belgium, IYT/Italy, Eiffel/France). Then deliver.

Because ddgs returns only titles/descriptions/URLs (no content), the searches themselves supply the dates:
- Erasmus Mundus 2027 entry: per-program deadlines Oct 2026–Jan 2027; July 2026 call added 37 new EMJM programs.
- NL Scholarship: €5k one-time, university-set deadline Feb 1–May 1; applications open ~Nov 1.
- SI Sweden: university apps by ~mid-Jan, then SI portal Feb 9–25.
- IYT Italy: ~April–May window (2026 cycle deadline was May 11, 2026).
- Eiffel: university nomination by ~Nov 22–Dec 5 for the following year.
- DAAD EPOS: ~Aug–Sep window.

## Pitfalls that mattered
- **Program name years ≠ application time.** "SI 2026/27" apps closed Feb 2026; the actionable cycle for a June-2026 grad is the 2027-entry one. Anchor everything to the user's graduation month.
- **Aggregator dates conflict** (scholars4dev vs scholarshipscorner vs official). Quote the official-domain date; cite aggregator only as "opened Nov 1" style signals.
- **Germany tuition-free is the real headline**, not DAAD: ~€0 tuition, €11,904 blocked account, 140 work days. Frame it as self-funded-cheap, not scholarship-only.
- **NL costs real money** — €5k scholarship vs €15–20k tuition. NL's pitch is the Orientation Year visa → ASML/Booking/NXP/Philips job outcomes.
- **Rank odds, not funding.** Fully-funded flagship (Erasmus ~1–5%) vs bilateral slots (Stipendium Hungaricum, dedicated Egyptian quota).
- User asked "all Europe countries if better opportunities + Netherlands" → the deliverable must include a job-outcome lens, not just a scholarship list.

## Deliverable shape (what landed well)
Ranked shortlist, each with funding / application window / the catch / official URL, a bottom-line recommendation tailored to the profile, and a closing offer (application calendar or SOP template). Keep it one message — no clarification round-trips.