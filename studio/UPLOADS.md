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
Lantern Rain Room: ambient/01-cozy-cabin-rain-fireplace-1h.mp4, ambient/03-christmas-fireplace-1h.mkv (Christmas
  season: Christmas videos go first from now on), ambient/shorts/s01-rain-outside-fire-inside.mp4,
  ambient/02-snowy-night-window-45m.mkv, ambient/04-christmas-village-snowfall-1h.mkv (when rendered), ambient/shorts/s02-snowfall.mp4
Brain Warp Lab (uploaded: odd-001, lilac-01, odd-002, spiral-01, odd-003). Next, in this order:
  ZAPIER pool (formats odd / col / txt + illusions): NEW ILLUSIONS FIRST, one a day — checker-01, mib-01,
  cafe-01, ebbinghaus-01 (munker-01 went out via Metricool) (2026-11-24, new watermark, claims verified) — then col-001, afterimage-01, txt-001, odd-004,
  col-002, spiral-02, txt-002, odd-005, col-003, troxler-01, txt-003, odd-006, col-004, afterimage-02,
  txt-004, odd-007, then keep rotating col / txt / odd (lowest number first).
  METRICOOL #2 pool (never via Zapier): emoji math, spot the difference, the new illusions (flag-*,
  hermann-01, lines-01) and the long-form episodes — see the Metricool #2 schedule below.
  Files: channel2/oddone2/odd-NNN.mp4, channel2/text/txt-NNN.mp4, channel2/color/col-NNN.mp4,
  channel2/math/math-NNN.mp4, channel2/spotdiff/diff-NNN.mp4,
  channel2/illusions/*.mp4; titles in channel2/POSTING.md (add #shorts to every title).
Zeipan: NEW CONCEPT APPROVED (user, 2026-11-24): satisfying physics simulations (zeipan/README.md, zeipan/POSTING.md).
  2 Shorts a day from zeipan/shorts/ (lowest number first), spaced ~3 h. Never streamer/game clips again.
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

### Metricool #2 schedule, November 2026 — superseded 11-24 (see below)
math-001 published 11-23 · Ep.1 11-24 20:00 · math-002 11-24 14:00 · diff-001 11-24 23:30 · math-003 11-25 23:30 ·
diff-002 11-26 14:00 · math-004 11-27 14:00 · diff-003 11-28 14:00 · math-005 11-29 14:00 · diff-004 11-30 14:00 ·
Ep.2 11-27 20:00 · Ep.3 11-30 20:00 · illusions (flag-us, hermann-01, lines-01, flag-tr, flag-br, flag-jp, flag-gb,
flag-de) in the free 14:00 / 23:30 slots 11-25 … 11-30 — scheduled once rendered and pushed.

## Selection rule (user, 2026-11-24): fewer, better — "don't break what works"
- Before each daily batch: pull the last 7 days of stats (videos.list statistics for tools/uploaded.tsv IDs:
  views, likes, comments) and rank formats by views per video and comments per 1k views.
- Upload only what passed tools/qa.py AND the visual check, and prefer the formats/variants that are
  winning; mix in at most one new or experimental idea per day, never a near-copy of yesterday's video.
- Don't flood: at most 3 Brain Warp Lab Shorts go public per day, Zapier + Metricool together, spaced 3–4 hours
  apart (day 1: the first two Shorts got ~1000 views each, the burst after them got 0–8; YouTube also refused the
  channel after ~10 uploads in 24 h). Episodes are extra: Tuesday and Friday 20:00 Istanbul.
- Watermark (user, 2026-11-24): no big diagonal handle; only the small faint logo tag at the very bottom.
  Only files committed after 2026-11-24T00:10Z carry it; older renders are re-made before upload.
- Open: thumbnail for math-002 (MfKCdoVFQAo) got 429 on 11-24; retry with studio/thumbs/math-002.jpg.
- Never re-upload or near-duplicate a video; vary flags/scenes/colours/puzzles.

### Metricool #2 schedule (2026-11-24, new watermark; 17:00 and 01:00 Istanbul, Zapier's Short in between ~21:05)
flag-tr 11-24 17:00 · math-003 11-25 01:00 · lines-01 11-25 17:00 · diff-002 11-26 01:00 · flag-br 11-26 17:00 ·
math-004 11-27 01:00 · diff-003 11-27 17:00 · Ep.2 11-27 20:00 (when rendered) · flag-jp 11-28 01:00 ·
math-005 11-28 17:00 · diff-004 11-29 01:00 · diff-001 11-29 17:00. November count: 5 published + 11 + Ep.2 = 17/20.
Ep.2 scheduled 2026-11-27 20:00 Istanbul (Metricool id 439701939, uuid 2246035285246430262, QA PASS, thumb in
channel2/episodes/brainwarplab-ep02.mp4.thumb.jpg). November Metricool count: 5 published + 12 scheduled = 17/20.
Every daily run: for Metricool #2 posts that published since the last run, log them in tools/uploaded.tsv and add
them to their playlist (episodes → PLA0sAqxxCuGA).

## Long-form calendar (one long video per channel per slot; Zapier unless noted)
- Brain Warp Lab episodes: Tue + Fri 20:00 (Metricool #2). Ep.2 Fri 11-27 (scheduled). Ep.3 Tue 12-01: file ready and
  QA PASS (channel2/episodes/brainwarplab-ep03.mp4, audio peak fixed) — schedule on Metricool once December opens.
- Zeipan Color Cup: Saturday 20:00. Ep.1 READY (zeipan/episodes/zeipan-colorcup-ep01.mp4, QA PASS, points verified):
  upload it first in the Saturday 11-28 batch (zeipan/POSTING.md has title/description/tags), thumbnail from
  zeipan/episodes/zeipan-colorcup-ep01.thumb.jpg. Ep.2 is rendered on Thursdays with `zeipan/tournament.py 2 ...`.

munker-01 → Metricool #2, published 2026-11-24 07:12 Istanbul (id 439775736, uuid 2996288497648419354) at the user's
request ("upload what is tested now"). November Metricool count: 18/20. Zapier was still throttled at 04:00 UTC.
So the Zapier illusion order is now: checker-01 (11-24), mib-01, cafe-01, ebbinghaus-01.

## ZAPIER ACCOUNT CHANGE (2026-11-24 04:10 UTC)
The user opened a SECOND Zapier account and connected it here. The Zapier connector in this session now reaches
ONLY the new account: one YouTube connection 02a93cb0-1845-8833-ba71-82e0bac67ed6 = Zeipan (UCyg04V0DLhMYyEoX9TEvqIA).
The old connection ids (Brain Warp Lab 02b64918…, Lantern Rain Room 0288fac3…, old Zeipan 021d0c65…) are NOT
reachable any more until the old account is connected again (as its own connector, or by adding those channels to
the new account). Always resolve connections at run time: list_zapier_connections for YouTubeV4CLIAPI, then
find_channel per connection, and match by channel id (Brain Warp Lab UCBTjlne2r4zjd9zkFuIPQ6g, Zeipan
UCyg04V0DLhMYyEoX9TEvqIA, Lantern Rain Room = the remaining one). The new account has its own 5-a-day quota:
used ALL 5 at 04:12–04:14 UTC on 11-24 (zp-004 public, zp-001 07:15Z, zp-003 10:15Z, zp-002 13:15Z, zp-005 16:15Z); free again from 04:15 UTC on 11-25.
Account roles (user, 2026-11-24): NEW Zapier account = Zeipan only (all 5 daily uploads go to Zeipan).
OLD Zapier account = Brain Warp Lab + Lantern Rain Room (the user reconnects it for the evening batches).
Whichever account the Zapier connector currently reaches, upload only to the channels that belong to it.

## 2026-11-24 05:00 UTC decisions (user: "only viral, nothing simple")
- Zeipan pivot to COUNTRY races (data: an Algodoo "100 Countries Marble Race" video has ~11M views; country pride drives
  comments). New Shorts: zeipan/shorts/zp-0NN-country-*.mp4 (sim.py --teams). Upload country ones before colour ones.
- A third Zapier account (also Zeipan) exists: used 2 at 04:45 UTC (zp-020 → 11-25 09:00Z, zp-021 → 11-25 15:00Z).
  Keep Zeipan at ~4-5 public Shorts a day, spaced ≥3 h (YouTube stops a channel at ~10 uploads per 24 h).
- Lantern Rain Room Shorts S01/S02 are on HOLD (plain loops, no hook). Upload only the long videos until better
  Shorts exist (slow camera push-in, Christmas scenes).
