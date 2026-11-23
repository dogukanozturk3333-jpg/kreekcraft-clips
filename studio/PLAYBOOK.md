# ZEIPAN Studio – Playbook

Every video goes through the same 8 stations. Nothing is uploaded that skipped a station.

## 1. Scout (daily)
`python3 -I tools/scout.py --range 24hr --top 25 > studio/candidates.md`
Only streamers who allow / pay for clipping: KreekCraft, Kai Cenat, Clix, Lacy.
Auto-blocked titles: sexual content, strip clubs, drugs, gambling, violence against women, animal harm.

## 2. Topic score (weekly + whenever news breaks)
Research the week's GTA 6 talk (news, Reddit, X, YouTube). Score each topic 1–10 on:
search momentum · competition · viral trigger (hype/shock/debate) · longevity · production ease (do we own permitted footage?).
Total /50 → the top topic decides the week's compilation theme. Never cover piracy / leaks / malware.

## 3. Visual review (every clip)
Contact sheet of 8 frames. Reject: nudity or sexual scenes, censorship emojis, drugs, real-person drama,
non-GTA screens. Note facecam position for the crop.

## 4. Title lab (every video)
Write 10 titles (2 curiosity gap, 3 number/list, 2 high stakes, 1 story with a streamer or Lucia/Jason, 1 contrast, 1 search-first),
6–12 words, must be delivered by the footage. Pick one, write why it wins, add `#shorts`.
Description: 1–2 line story, streamer Twitch links, search line with 4–6 keywords, 6–8 hashtags.

## 5. Hook (first 1.5 s)
On-screen hook box = the payoff in ≤ 6 words. The clip must start on motion, never on a loading/black frame.
Compilations: hook names the theme + count ("TOP 3 …", "STREAMERS FOUND …").

## 6. Edit (tools/render.py + tools/brand.py)
Facecam top / gameplay bottom, word-highlighted captions, profanity bleep, punch-in zooms on peaks,
ZEIPAN logo intro + badge + follow end card, streamer credit tag. Crop gameplay ABOVE the game's own subtitles.

## 7. QA checklist (before upload)
- [ ] 1080x1920, 30 fps, −14 LUFS, no black frames in the first 2 s
- [ ] no uncensored swear text anywhere (game subtitles cropped)
- [ ] streamer credited on screen + in description
- [ ] title promise is visible in the video
- [ ] not already uploaded (tools/uploaded.tsv)

## 8. Publish + review
Upload via Zapier (≈5/day limit) spread through the day; log in tools/uploaded.tsv.
Weekly: compare views per format (single vs. compilation vs. theme) and move the calendar towards the winner.
