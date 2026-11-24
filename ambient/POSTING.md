# Lantern Rain Room — uploads

Channel: Lantern Rain Room (@lanternrainroom), Zapier YouTube connection "YouTube #3"
(connection_id 0288fac3-da80-8ed6-8011-d7ad183241cf). The Zapier upload limit (~5 per 24 h) is shared
by ALL YouTube connections, so channels share one daily budget.
Everything is our own: AI-made picture (Canva), AI sound effects (ElevenLabs SFX v3, seamless loops),
LICENSE NOTE: the loops were made on the ElevenLabs FREE plan, which has no commercial licence and requires
crediting ElevenLabs. Every description carries "Sound effects created with ElevenLabs." Before the channel
applies for monetization, regenerate the loops on a paid ElevenLabs month (or replace them with CC0 audio).

mixed into a non-repeating hour with tools/ambient_layers.py, fire animated with tools/ambient_loop.py.

SEO rules for this channel
- Title starts with the words people search ("rain and fireplace sounds", "rain sounds for sleeping"),
  then the scene, then the length. One or two emojis at most.
- First two lines of the description repeat the main keywords in a natural sentence (they show in search).
- 3 hashtags at the end (YouTube shows the first three above the title).
- Category 10 (Music), not made for kids, English.
- Every Short links to its full-length video in the first line of the description.
- No text on the picture (user's rule): only the small faded LANTERN RAIN ROOM tag at the bottom
  (ambient/shorts/brand-tag.ass). Hooks go in the title, not on the video.

Audio QA (run before every upload): no clipping (true peak below -1 dBFS), no click-like jumps,
no tonal whine in a high-resolution spectrum, steady level (no per-second jumps over 4 dB),
long videos about -20 LUFS, Shorts about -16 LUFS. Video 01 passed: peak -1.4 dBFS, 1 click-like
event in the hour (a soft fire pop), no tones, level range -24 to -19 dB.

---

## 01 — Rain and Fireplace, cozy cabin (1 hour)
File: `ambient/01-cozy-cabin-rain-fireplace-1h.mp4` (1920x1080, 12 fps, H.264 + AAC 128k, -19.6 LUFS)
Picture: `img/cabin-rain-fire.jpg` · Loops: rain-a, rain-b (0 dB), fire-a, fire-b (-3 dB, pops tamed)

**Title:** Rain and Fireplace Sounds for Sleeping 🌧️🔥 Cozy Cabin Ambience | 1 Hour

**Description:**
Rain and fireplace sounds for sleeping, studying and relaxing: soft rain on the windows of a quiet log
cabin and a gently crackling fire beside a warm lantern.

✔ Gentle rain + soft fire crackle, no music, no talking
✔ Even volume, no sudden loud sounds
✔ Great for sleep, study, reading, focus and stress relief

Subscribe to Lantern Rain Room for new cozy rain and fire ambience every week.

Sound effects created with ElevenLabs.

rain sounds for sleeping, fireplace sounds, rain and fireplace, cozy cabin ambience, rain on window,
crackling fire, sleep sounds, study ambience, relaxing sounds, white noise for sleep

#rainsounds #fireplace #sleepsounds

**Tags:** rain and fireplace sounds, rain sounds for sleeping, fireplace sounds, cozy cabin, sleep sounds,
crackling fire, rain on window, study ambience, relaxing sounds, ambience, 1 hour

---

## S01 — Short: fireplace close-up (40 s, seamless loop, no on-screen text)
File: `ambient/shorts/s01-rain-outside-fire-inside.mp4` (1080x1920, 30 fps, -16 LUFS; audio tail
crossfades into the head, so replays loop without a seam). Upload AFTER video 01 and put its link first.

**Title:** Rain outside, fire inside 🌧️🔥 #rainsounds #fireplace #sleep

**Description:**
Full 1-hour version 👉 {LINK TO VIDEO 01}
Rain and fireplace sounds in a cozy log cabin. Put it on, breathe out, and rest. 🌧️🔥
Sound effects created with ElevenLabs.
#rainsounds #fireplace #sleep

**Tags:** rain sounds, fireplace, cozy, sleep sounds, rain and fireplace, relaxing, shorts

---

## 02 — Heavy snowfall at night, cabin window (45 minutes)
File: `ambient/02-snowy-night-window-45m.mkv` (1920x1080, 15 fps H.264 + Opus 64k, -20 LUFS, < 95 MB)
Picture: `img/snow-window.jpg` (ElevenLabs image, upscaled) · Snow: tools/ambient_loop.py with
`ambient/snow-window.json` (3 depth layers, only behind the glass via img/snow-window-mask.png).
Sound: our own soft "snowy night hush" (no wind character), tools/wind_synth.py
`snow-hush-a.wav 180 31 --howl 0 --depth 0.2 --indoor --strength 0.7` and `snow-hush-b.wav 180 47 --howl 0
--depth 0.25 --indoor --strength 0.7`, mixed with ambient_layers.py (`hush:3:…`, OPUS_KBPS=64).
Why 45 min: heavy, smooth snowfall needs more bitrate; 45 minutes keeps the file under GitHub's 100 MB.

**Title:** Heavy Snowfall at Night ❄️ Cozy Cabin Window | Soft Snow Ambience for Sleep & Relaxation

**Description:**
Heavy snowfall at night, seen from a warm cabin window: snow drifting over a frozen lake and pine forest
under the full moon, a lantern glowing on the windowsill. ❄️🌙
Soft, steady snowy-night ambience for sleep, study, reading and calm.

✔ Gentle, steady sound, no music, no talking
✔ Even volume, no sudden noises

Subscribe to Lantern Rain Room for new cozy ambience every week.

Image created with ElevenLabs.

snowfall ambience, snow falling, snowy night, cozy cabin, winter ambience, sleep sounds, relaxing snow,
snowfall for sleep, winter window, calm ambience

#snowfall #winterambience #sleepsounds

**Tags:** snowfall ambience, snow falling, heavy snowfall, snowy night, cozy cabin window, winter ambience,
sleep sounds, relaxing, snow for sleep, calm

---

## S02 — Short: snowfall over the frozen lake (40 s, seamless loop, no on-screen text)
File: `ambient/shorts/s02-snowfall.mp4` — upload AFTER video 02 and put its link first.

**Title:** Snow falling at night ❄️ breathe out… #snowfall #winter #sleep

**Description:**
Full snowfall video 👉 {LINK TO VIDEO 02}
Heavy snow falling over a frozen lake under the full moon. ❄️🌙
Image created with ElevenLabs.
#snowfall #winter #sleep

**Tags:** snowfall, snow falling, winter, cozy, sleep sounds, relaxing, shorts

---

## 03 — Christmas Fireplace, cozy living room (1 hour)
File: `ambient/03-christmas-fireplace-1h.mkv` (1920x1080, 15 fps, H.264 + Opus 64k, about -21 LUFS, peaks -4 dBFS)
Picture: `img/christmas-fireplace.jpg` (Image created with ElevenLabs) · Sound: fire-a, fire-b only (crackles tamed)
Animated: fire, twinkling tree lights, candles, quiet snow behind the window. No wind, no rain, no music.

**Title:** Christmas Fireplace 🎄🔥 Crackling Fire & Twinkling Tree Lights | Cozy Christmas Ambience 1 Hour

**Description:**
Christmas fireplace ambience for a cozy, calm evening: a gently crackling log fire, twinkling Christmas
tree lights and soft snow falling outside the window of a warm living room.

✔ Crackling fire only: no music, no talking, no wind
✔ Even volume, softened crackles, nothing sudden
✔ Perfect for sleep, reading, studying, holiday dinners or just relaxing

Subscribe to Lantern Rain Room for a new cozy Christmas ambience every few days this December.

Image created with ElevenLabs. Sound effects created with ElevenLabs.

christmas fireplace, christmas ambience, crackling fireplace, cozy christmas, fireplace sounds,
christmas tree lights, winter ambience, fireplace for sleep, holiday ambience, relaxing fire sounds

#christmasfireplace #christmasambience #fireplace

**Tags:** christmas fireplace, christmas ambience, fireplace sounds, crackling fire, cozy christmas,
christmas tree, fireplace 1 hour, christmas living room, winter ambience, sleep sounds, holiday ambience

---

## 04 — Snowy Christmas Village at night (1 hour)
File: `ambient/04-christmas-village-snowfall-1h.mkv` (1920x1080, 12 fps, HEVC + Opus 40k, -23 LUFS, peaks -8.5 dBFS, QA PASS, 82.7 MB)
Picture: `img/christmas-village.jpg` (Image created with ElevenLabs) · Sound: snow-hush-a/b only (soft, no hiss)
Animated: soft bokeh snowfall (no wind), twinkling village tree, flickering lanterns.

**Title:** Snowy Christmas Village at Night ❄️🎄 Gentle Snowfall Ambience for Sleep & Relaxation | 1 Hour

**Description:**
Gentle snowfall over a quiet Christmas village at night: warm glowing cottages, a twinkling Christmas tree
in the square and soft snow falling without a breath of wind.

✔ Soft, calm snow hush: no music, no talking, no wind
✔ Even volume all the way through
✔ Great for sleep, study, reading and Christmas relaxation

Subscribe to Lantern Rain Room for a new cozy Christmas ambience every few days this December.

Image created with ElevenLabs.

christmas village, snowfall ambience, snowy night, christmas ambience, falling snow, winter village,
snow for sleep, christmas lights, peaceful winter night, relaxing snow

#christmasambience #snowfall #christmasvillage

**Tags:** christmas village, snowfall, snowy night, christmas ambience, falling snow, winter ambience,
snow sounds, christmas lights, sleep ambience, relaxing, 1 hour
