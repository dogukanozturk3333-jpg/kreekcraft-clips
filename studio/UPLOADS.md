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
  col-001, afterimage-01, txt-001, odd-004, math-001, diff-001, col-002, spiral-02, txt-002, math-002,
  diff-002, odd-005, col-003, troxler-01, math-003, diff-003, txt-003, odd-006, col-004, afterimage-02,
  math-004, diff-004, txt-004, odd-007, then keep rotating math / diff / col / txt / odd (lowest number first).
  Files: channel2/oddone2/odd-NNN.mp4, channel2/text/txt-NNN.mp4, channel2/color/col-NNN.mp4,
  channel2/math/math-NNN.mp4, channel2/spotdiff/diff-NNN.mp4,
  channel2/illusions/*.mp4; titles in channel2/POSTING.md (add #shorts to every title).
Zeipan: compilations/2026-11-23-streamers-found-bigfoot.mp4 (last one; then paused — the other prepared
  GTA clips stay in the repo unused)
Uploaded items are listed in tools/uploaded.tsv; skip anything already there.
