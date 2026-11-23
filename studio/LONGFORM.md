# Brain Warp Lab — long-form episode series

Why: Shorts bring subscribers, but money comes from long videos (watch hours for YouTube Partner Program
eligibility and mid-roll ads). Plan: 2 episodes a week, every Tuesday and Friday, as a numbered series.

## Build
`python3 -I channel2/episode.py N` renders 30 FRESH puzzles (seeds 100*N+1…, never used as Shorts) in
5 rounds + 2 bonus illusions, then `compile_long.py` makes `channel2/episodes/brainwarplab-epNN.mp4`
(+ `.chapters.txt` + `.thumb.jpg`). About 13–15 minutes, under 100 MB.
Rounds: Sharp Eyes (emoji ×6) → Color Vision (×6) → Letters & Numbers (×6) → Spot the Difference (×5)
→ Brain Math (×5) → Bonus: Illusions (×2). Voiced intro, round cards, score panel, score-rank outro.

## Upload (Zapier upload_video, Brain Warp Lab connection 02b64918-4742-8527-9d26-eacc99111817)
Category 24, public, not made for kids, en. Counts as one of the 5 daily uploads. Add to playlist
"Brain Warp Lab Episodes" (create once, then reuse; note its ID here).
**Title:** 30 Brain Puzzles to Test Your Eyes & Brain 🧠 How Many Can You Solve? | Brain Warp Lab Ep. N
**Description:**
30 brain puzzles in 5 rounds: find the odd emoji, spot the different color, find the hidden letter, spot
the difference and emoji math — plus two bonus optical illusions. Keep score and tell us your total! 🧠

⏱ Chapters
{paste channel2/episodes/brainwarplab-epNN.mp4.chapters.txt}

Scoring: 1 point for every level you beat (max shown at the end). Beginner, Sharp Eyes, Genius or
Brain Warp Master — which one are you?

New puzzles every day on our Shorts, a new episode every week. Subscribe!
#brainteaser #puzzles #iqtest
**Tags:** brain puzzles, brain teasers, find the odd one out, spot the difference, color test, emoji math,
puzzle compilation, iq test, brain games, optical illusions, eye test
**Thumbnail:** `.thumb.jpg` — only after the channel is phone-verified (Zapier "Update Video Thumbnail").

## Instagram
Cut the bonus illusion or one strong round (60–90 s) as a Reel that says "full episode on YouTube".

## Pending: custom thumbnails (blocked until phone verification)
Zapier "Update Video Thumbnail" returns "The authenticated user doesn't have permissions to upload and set
custom video thumbnails" (tested 2026-11-23 on QqTZ881H9MU). The user will verify the Brain Warp Lab
account later from another phone (youtube.com/verify). After that: apply studio/thumbs/*.jpg and every
channel2/episodes/*.thumb.jpg to their uploaded videos (IDs in tools/uploaded.tsv), and add a thumbnail
step to the daily upload routine.

## Status 2026-11-24 (02:15 Istanbul)
- Ep.1 built (12.2 min, 30 puzzles) and scheduled on Metricool #2 for 02:20; thumbnail goes on right after
  publishing (channel phone-verified 2026-11-24, custom thumbnails now work — tested on QqTZ881H9MU).
- Ep.2 rendering, Ep.3 rendering in parallel; each is published the same night once ready (user wants
  everything out now). November Metricool #2 budget: 20/20 (episodes + math/diff Shorts + new illusions).

## Instagram for the episodes (next step, user asked)
Instagram brand 7879434 is on Metricool account #1 (20/month, November used up). From December 1:
cut 60–90 s highlights from each episode (best round + bonus illusion, 9:16 crop of the centre Short with
"full episode on YouTube" end card) and post them as Reels next to the best Shorts (illusions first —
they got the most reactions). Needs account #1's brand shared with account #2, or the connector switched.

## Series rule (user, 2026-11-24)
Shorts may be frequent and attention-grabbing; long-form is a SERIES with a fixed rhythm:
- New episode every **Tuesday and Friday at 20:00 Istanbul** (US lunchtime), numbered "Brain Warp Lab Ep. N".
- Ep.1 Tue 2026-11-24 (out) · Ep.2 Fri 11-27 · Ep.3 Tue 12-01 · Ep.4 Fri 12-04 · Ep.5 Tue 12-08 · Ep.6 Fri 12-11 …
- Every episode description links the previous one; every episode goes into the "Brain Warp Lab Episodes"
  playlist (PLA0sAqxxCuGA); the outro voice says "new episode every Tuesday and Friday".
- One Short per episode (best puzzle or bonus illusion) the day before, ending with "Full episode tomorrow".
