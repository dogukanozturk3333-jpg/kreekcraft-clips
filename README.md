# Zeipan — KreekCraft GTA 6 clips

Vertical clips of KreekCraft's GTA 6 livestream moments for the ClipLaunch "KreekCraft GTA 6 Clipping" campaign on Content Rewards.
Watch KreekCraft live: https://twitch.tv/kreekcraft

## Layout
- `NN-*.mp4` — first batch (01–10), titles/descriptions in `POSTING.md`
  (all branded with the ZEIPAN kit except 04 and 06, which were uploaded before it existed)
- `lacy/` — Lacy GTA 6 marathon clips (branded)
- `daily/<YYYY-MM-DD>/` — clips made by the daily job, each with its own `POSTING.md`
- `brand/` — ZEIPAN brand kit: logo bug, end card, sounds, intros, channel art (see `brand/README.md`)
- `tools/render.py` — renderer (facecam + overlay top, gameplay bottom, hook, captions, profanity bleeps,
  twitch.tv/kreekcraft end card, ZEIPAN brand layers)
- `tools/brand.py` — builds the brand kit; `apply` brands an already-rendered clip
- `tools/processed.txt` — Twitch clip slugs already reviewed
