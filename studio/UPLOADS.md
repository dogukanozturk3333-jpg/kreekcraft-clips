# Upload budget and queue (all channels)

Zapier lets the account upload about 5 YouTube videos per rolling 24 hours, shared by every connection.
Each batch starts right after the previous batch's first upload + 24 h; the next batch is scheduled with
send_later at the end of each run. Stop at the first "throttled" answer; what is left moves to the next day.

## Connections
- Zeipan (GTA 6 clips) — 021d0c65-10fe-8b4f-ab96-07df20937cb2 ("YouTube", default)
- Lantern Rain Room (ambience) — 0288fac3-da80-8ed6-8011-d7ad183241cf ("YouTube #3"), category 10
- Brain Warp Lab (puzzles) — 02b64918-4742-8527-9d26-eacc99111817 ("YouTube #4"), category 24

## Daily mix (5 slots)
1. Lantern Rain Room: new long video (on long-video days) — otherwise a Short
2. Lantern Rain Room: Short (links to its long video)
3. Brain Warp Lab: puzzle Short
4. Brain Warp Lab: puzzle Short (from day 2, when the starter pack is ready)
5. Zeipan: best GTA 6 clip of the day (compilation first)

## Queue (oldest first; take the first unused item per channel)
Lantern Rain Room: ambient/01-cozy-cabin-rain-fireplace-1h.mp4, ambient/shorts/s01-rain-outside-fire-inside.mp4
Brain Warp Lab: channel2/oddone2/odd-001.mp4 … odd-010.mp4 (v2, motion-designed) (titles in channel2/POSTING.md)
Zeipan: compilations/2026-11-22-top3-gta6-fails.mp4, daily/2026-11-23/14-kreekcraft-insurance-fraud.mp4,
  compilations/2026-11-23-streamers-found-bigfoot.mp4, daily/2026-11-23/16-top3-gta6-moments.mp4,
  daily/2026-11-23/15-kreekcraft-plane-hijack.mp4
Uploaded items are listed in tools/uploaded.tsv; skip anything already there.
