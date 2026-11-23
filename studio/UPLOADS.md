# Upload budget and queue (all channels)

Zapier lets the account upload about 5 YouTube videos per rolling 24 hours, shared by every connection.
Each batch starts right after the previous batch's first upload + 24 h; the next batch is scheduled with
send_later at the end of each run. Stop at the first "throttled" answer; what is left moves to the next day.

## Connections
- Zeipan (GTA 6 clips) — 021d0c65-10fe-8b4f-ab96-07df20937cb2 ("YouTube", default)
- Lantern Rain Room (ambience) — 0288fac3-da80-8ed6-8011-d7ad183241cf ("YouTube #3"), category 10
- Brain Warp Lab (puzzles) — 02b64918-4742-8527-9d26-eacc99111817 ("YouTube #4"), category 24

## Daily mix (5 slots) — Zeipan (GTA) is PAUSED after the Bigfoot compilation (user's decision, 2026-11-23)
1. Lantern Rain Room: new long video (on long-video days) — otherwise a Short
2. Lantern Rain Room: Short (links to its long video)
3. Brain Warp Lab: puzzle / illusion Short
4. Brain Warp Lab: puzzle / illusion Short
5. Brain Warp Lab: puzzle / illusion Short (or a 3rd ambience item when one is ready)

## Queue (oldest first; take the first unused item per channel)
Lantern Rain Room: ambient/01-cozy-cabin-rain-fireplace-1h.mp4, ambient/shorts/s01-rain-outside-fire-inside.mp4
Brain Warp Lab: alternate formats — odd-001, lilac-01, odd-002, spiral-01, odd-003, afterimage-01, odd-004,
  troxler-01, then odd-005 … odd-010 (oddone files in channel2/oddone2/, illusions in channel2/illusions/;
  titles in channel2/POSTING.md)
Zeipan: compilations/2026-11-23-streamers-found-bigfoot.mp4 (last one; then paused — the other prepared
  GTA clips stay in the repo unused)
Uploaded items are listed in tools/uploaded.tsv; skip anything already there.
