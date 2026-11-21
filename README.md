# Zeipan — KreekCraft GTA 6 clips

Vertical clips of KreekCraft's GTA 6 livestream moments for the ClipLaunch "KreekCraft GTA 6 Clipping" campaign on Content Rewards.
Watch KreekCraft live: https://twitch.tv/kreekcraft

## Layout
- `NN-*.mp4` — first batch (01–10), titles/descriptions in `POSTING.md`
  (01–03, 05, 07–10 re-rendered with the ZEIPAN pro edit; 04 and 06 are the versions already uploaded)
- `lacy/` — Lacy GTA 6 marathon clips (branded)
- `daily/<YYYY-MM-DD>/` — clips made by the daily job, each with its own `POSTING.md`
- `brand/` — ZEIPAN brand kit: logo bug, end card, sounds, intros, channel art (see `brand/README.md`)
- `tools/render.py` — renderer (facecam + overlay top, gameplay bottom, animated hook + captions,
  profanity bleeps, twitch.tv/kreekcraft end card, ZEIPAN brand layers)
- `tools/fx.py` — the "pro edit": glitch entrance, slow push-in, jump zooms, zoom/whip/glitch transitions
  on cuts and sentence beats, punch-ins and shake on reactions, zoom-blur into the end card, SFX track
  (emoji pop-ups exist but are off by default)
- `tools/brand.py` — builds the brand kit; `apply` brands an already-rendered clip
- `tools/processed.txt` — Twitch clip slugs already reviewed
