# Zeipan — KreekCraft GTA 6 clips

Vertical clips of KreekCraft's GTA 6 livestream moments for the ClipLaunch "KreekCraft GTA 6 Clipping" campaign on Content Rewards.
Watch KreekCraft live: https://twitch.tv/kreekcraft

Also clips for the AsianJeff GTA 6 clipping campaign on Content Rewards ($1 / 1K views, $10 min per clip). Watch AsianJeff live: https://twitch.tv/asianjeff

## Layout
- `NN-*.mp4` — first batch (01–10), titles/descriptions in `POSTING.md`
- `daily/<YYYY-MM-DD>/` — clips made by the daily job, each with its own `POSTING.md`
- `tools/render.py` — renderer (facecam + overlay top, gameplay bottom, hook, captions, profanity bleeps, twitch.tv/kreekcraft end card)
- `tools/processed.txt` — Twitch clip slugs already reviewed
- `brand.yaml` — our edit package (frame color, channel badge/logo, context strip, punch-in zoom, replay, sfx, series name); `tools/render.py` reads it
- `tools/series.tsv` — "GTA 6 Streamer Moments #N" numbers already used in titles
- `tools/uploaded.tsv` — videos already on the Zeipan channel; check it before every upload so nothing goes up twice

## Edit package (brand.yaml)
Every clip rendered by `tools/render.py` gets:
- a thin brand-colored frame and the Zeipan logo (`assets/logo.png`, drawn by `tools/make_logo.py`) at the top the whole time
- an intro sting: the big Zeipan logo pops over the gameplay for the first 0.8 s with a pop sound (the clip and hook already play underneath, so no dead intro time)
- a context strip: `<Streamer> • GTA 6 • Day N` (day counted from the streamer's `day1`, US Eastern dates)
- our own hook line (never the Twitch clip title), word-highlighted captions, profanity bleeps
- a sudden 1.2x punch-in on the gameplay at reaction peaks found in the audio (with a whoosh)
- a punchline sound effect from `assets/sfx`
- an ending that replays the main moment zoomed in at 0.5x speed with the twitch.tv call to action, so the Short loops back into the hook
- the streamer's facecam + overlay panel is never zoomed, blurred or covered
- titles carry the series number: `... | GTA 6 Streamer Moments #N`

## Sound effects
All files in `assets/sfx` (`boom.wav`, `ding.wav`, `pop.wav`, `rewind.wav`) are synthesized from scratch by
`tools/make_sfx.sh` (ffmpeg math sources, no recorded samples). They are our own work and are released under
**CC0 1.0 Universal** (public domain dedication): free to use commercially, no attribution required.
Any third-party effect added later must be listed here with its source URL, author and license.
