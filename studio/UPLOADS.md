# Upload budget and queue (all channels)

Zapier lets the account upload about 5 YouTube videos per rolling 24 hours, shared by every connection.
Each batch starts right after the previous batch's first upload + 24 h; the next batch is scheduled with
send_later at the end of each run. Stop at the first "throttled" answer; what is left moves to the next day.

## Connections
- Zeipan (GTA 6 clips) — 021d0c65-10fe-8b4f-ab96-07df20937cb2 ("YouTube", default)
- Lantern Rain Room (ambience) — 0288fac3-da80-8ed6-8011-d7ad183241cf ("YouTube #3"), category 10
- Brain Warp Lab (puzzles) — 02b64918-4742-8527-9d26-eacc99111817 ("YouTube #4"), category 24

## Daily mix (5 slots) — Brain Warp Lab is the PRIORITY (user, 2026-11-23); Zeipan paused
1–4. Brain Warp Lab: rotate formats so no two in a row are the same:
     emoji → color → illusion → text → emoji → color → text → …
5. Lantern Rain Room: next long video or Short (one per day)

## Queue (oldest first; take the first unused item per channel)
Lantern Rain Room: ambient/01-cozy-cabin-rain-fireplace-1h.mp4, ambient/shorts/s01-rain-outside-fire-inside.mp4,
  ambient/02-snowy-night-window-45m.mkv, ambient/shorts/s02-snowfall.mp4
Brain Warp Lab (uploaded: odd-001, lilac-01, odd-002, spiral-01, odd-003). Next, in this order:
  ZAPIER pool (formats odd / col / txt + the first illusion set): col-001, afterimage-01, txt-001, odd-004,
  col-002, spiral-02, txt-002, odd-005, col-003, troxler-01, txt-003, odd-006, col-004, afterimage-02,
  txt-004, odd-007, then keep rotating col / txt / odd (lowest number first).
  METRICOOL #2 pool (never via Zapier): emoji math, spot the difference, the new illusions (flag-*,
  hermann-01, lines-01) and the long-form episodes — see the Metricool #2 schedule below.
  Files: channel2/oddone2/odd-NNN.mp4, channel2/text/txt-NNN.mp4, channel2/color/col-NNN.mp4,
  channel2/math/math-NNN.mp4, channel2/spotdiff/diff-NNN.mp4,
  channel2/illusions/*.mp4; titles in channel2/POSTING.md (add #shorts to every title).
Zeipan: compilations/2026-11-23-streamers-found-bigfoot.mp4 (last one; then paused — the other prepared
  GTA clips stay in the repo unused)
Uploaded items are listed in tools/uploaded.tsv; skip anything already there.

## Instagram (@brainwarplab) via Metricool — brand blogId 7879434, timezone Europe/Istanbul
BUDGET: Metricool's free plan publishes at most 20 posts per CALENDAR MONTH (help.metricool.com; counter
resets on the 1st). Count rows in studio/instagram.tsv for the month and never schedule past 20.
November 2026: all 20 used (last ones 11-24 00:15–03:15, US prime time). Next Reels from 2026-12-01.
From December: 20 a month ≈ one Reel a day at 19:30 Istanbul, best formats first (math, color, diff).
If the user connects Instagram in Zapier (Instagram for Business, publish_video), use that for extra Reels.
Raw GitHub URL as media, type REEL, isAiGenerated false; never post a video that is not pushed yet.
Caption: hook line with emojis (the YouTube title idea, no #shorts) / comment prompt / a share or tag prompt
("send this to a friend who…") / "Follow @brainwarplab for a new brain puzzle every day." / 12 hashtags:
format-specific (e.g. #mathpuzzle #emojimath #orderofoperations) + broad (#brainteaser #puzzle #braingames
#iqtest #challenge) + #explore #reels. No invented statistics. Log scheduled Reels in studio/instagram.tsv.
Scheduled so far: odd-001 (2026-11-23 22:00), lilac-01 (11-24 13:00), odd-002 (11-24 19:30),
spiral-01 (11-25 13:00), odd-003 (11-25 19:30).

## Metricool account #2 (YouTube) — brand blogId 8317957, YouTube = Brain Warp Lab (UCBTjlne2r4zjd9zkFuIPQ6g)
Free plan: 20 published posts per calendar month on this account too. Use it for the long-form episodes
(studio/LONGFORM.md) first, then extra Brain Warp Lab Shorts — so Zapier's 5 a day stay for Shorts.
youtubeData: {title, type "short" | "video", privacy public, tags, category ENTERTAINMENT, madeForKids false}.
NOTE (2026-11-23): the Metricool connector here now logs in as account #2, so the Instagram brand 7879434
(account #1) is not visible any more. Its 20 November Reels stay scheduled on Metricool's side. For
December Instagram posting the user shares brand 7879434 with account #2 (or reconnects account #1).
Metricool YouTube log: math-001 published 2026-11-23 22:55 Istanbul as vzQNZnXVZsY (test OK, 1/20 for November).

### Metricool #2 schedule, November 2026 (20/20 planned)
math-001 published 11-23 · Ep.1 11-24 20:00 · math-002 11-24 14:00 · diff-001 11-24 23:30 · math-003 11-25 23:30 ·
diff-002 11-26 14:00 · math-004 11-27 14:00 · diff-003 11-28 14:00 · math-005 11-29 14:00 · diff-004 11-30 14:00 ·
Ep.2 11-27 20:00 · Ep.3 11-30 20:00 · illusions (flag-us, hermann-01, lines-01, flag-tr, flag-br, flag-jp, flag-gb,
flag-de) in the free 14:00 / 23:30 slots 11-25 … 11-30 — scheduled once rendered and pushed.

## Selection rule (user, 2026-11-24): fewer, better — "don't break what works"
- Before each daily batch: pull the last 7 days of stats (videos.list statistics for tools/uploaded.tsv IDs:
  views, likes, comments) and rank formats by views per video and comments per 1k views.
- Upload only what passed tools/qa.py AND the visual check, and prefer the formats/variants that are
  winning; mix in at most one new or experimental idea per day, never a near-copy of yesterday's video.
- Don't flood: 3–5 Brain Warp Lab Shorts a day, spaced at least 2 hours apart; one episode every 3–4 days.
- Never re-upload or near-duplicate a video; vary flags/scenes/colours/puzzles.
