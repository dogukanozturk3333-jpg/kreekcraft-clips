# Brain Warp Lab — puzzles & illusions (Shorts)

## SEO + Shorts rules (apply to every upload)
- Every video is 1080x1920 and under 60 s, so YouTube files it under Shorts automatically; still put
  " #shorts" at the end of the title and #shorts first in the description hashtags.
- Title: hook + the searched phrase ("find the odd one out", "optical illusion", "color test",
  "hidden letter"), max ~60 characters before " #shorts", one or two emojis.
- Description line 1 repeats the main keyword in a sentence; line 2 is the comment prompt; then 4 hashtags
  (#shorts + three topic tags). Tags: the format's tag list.
- After uploading, add the video to its playlist with Zapier "Add Video to Playlist"
  (or the raw API playlistItems POST), connection 02b64918-4742-8527-9d26-eacc99111817:
    emoji odd-one-out → PLfptmS3q7Yic        illusions → PLOodmHfHNYPw
    color test → PLddGkAWopl60               hidden letter/number → PLMmNY7SqOeyQ
    emoji math → PLB_B8aQbcGEg               spot the difference → PLa634PXFH_-M
    long-form episodes → PLA0sAqxxCuGA
- Thumbnails: python3 -I channel2/thumbs.py short VIDEO KIND studio/thumbs/NAME.jpg (episodes: thumbs.py episode N),
  apply with Zapier youtube_update_video_thumbnail using a commit-SHA raw URL (avoids GitHub's raw cache).
- Instagram (when connected): post the same file as a Reel with the same caption (title + description).

Not connected yet: the user opens the channel with a new Google account and adds it in Zapier with
"Add connection" (YouTube), then uploads use that connection_id. Zapier's ~5 uploads per 24 h are
shared with the other channels.

## Format 1 — Find the odd one out (`channel2/oddone2.py SEED OUT.mp4`, v2; v1 oddone.py is retired)
28 s, motion-designed (animated background, popping grid, circular countdown with heartbeat,
sliding level changes, zoom-and-ring reveal, end screen with 1/2/3 buttons + logo, original music bed): three levels (easy / medium / hard), countdown with ticks, the answer circled, then
"How many did you find? Comment 1, 2 or 3" (comments push the Short). Every seed is a new video.
Emoji art: Noto Color Emoji (SIL OFL). Voice: Kokoro am_michael (offline). Sounds: generated.

Title (rotate):
- Find the Odd One Out 🧠 Can You Beat Level 3?
- Only Sharp Eyes Find All 3 👀 Odd One Out
- Find the Odd Emoji in 7 Seconds ⏱️
Description: Find the odd one out in all three levels before time runs out! 🧠 How many did you get?
Comment 1, 2 or 3 👇  New brain puzzles every day.
#shorts #puzzle #brainteaser #oddoneout
Tags: find the odd one out, odd one out, emoji puzzle, brain teaser, puzzle, spot the difference, brain test
Category 24 (Entertainment), not made for kids.

## Starter pack — titles per video (description/tags as above, same for all)
- 001: Find the Odd One Out 🧠 Can You Beat Level 3?
- 002: Only Sharp Eyes Find All 3 👀 Odd One Out
- 003: Find the Odd Emoji in 7 Seconds ⏱️
- 004: Can You Spot It? 😳 Find the Odd One Out
- 005: Test Your Eyes 👁️ Find the Odd One Out
- 006: Level 3 Is Evil 😈 Find the Odd Emoji
- 007: How Fast Are Your Eyes? Odd One Out ⚡
- 008: Find It Before Time Runs Out ⏰ Odd One Out
- 009: Your Brain vs Level 3 🧠 Find the Odd Emoji
- 010: Can You Find All 3? 🔍 Odd One Out Challenge

## Format 2 — Optical illusions (`channel2/illusion.py TYPE OUT.mp4`)
Classic perception effects (public scientific phenomena) in our own designs: spiral (motion aftereffect),
lilac (lilac chaser), troxler (Troxler fading), afterimage (colour afterimage). Ends with "Did it work?
YES / NO — tell us in the comments". Category 24, not made for kids.
Description: Try it with sound on and don't move your eyes 👀 Did it work? Comment YES or NO!
New brain puzzles and illusions every day.
#shorts #opticalillusion #illusion #brain
Tags: optical illusion, illusion, brain trick, eye test, mind blowing, perception, brain teaser

- lilac-01: Stare at the Cross… a GREEN Dot Appears 🟢 (Optical Illusion)
- spiral-01: Stare for 15 Seconds, Then Look at the Fire 🌀 Your Brain Will Melt It
- troxler-01: Stare at the Dot and Watch the Colors DISAPPEAR 👀
- afterimage-01: This Black & White Photo Turns to COLOR 🤯 (Stare at the Dot)
Extra illusion titles:
- spiral-02: Stare at the Spiral, Then Look at the Snow ❄️ It Starts Moving!
- afterimage-02: This Snowy Night Is Black & White… or Is It? 🤯 (Stare at the Dot)

## Watermark (all videos from 2026-11-23 evening on)
channel2/brandmark.py: faint diagonal @brainwarplab across the centre + logo/handle tag at the bottom,
so re-uploads can't simply crop the brand away.

## Format 3 — Hidden letter / number (`oddone2.py SEED OUT.mp4 text`) → channel2/text/txt-NNN.mp4
Same motion design; grids of letters/numbers with one look-alike (W/M, q/p, O/0, 81/18 …).
Description: Find the odd one out in all three levels before time runs out! 🔍 How many did you get?
Comment 1, 2 or 3 👇  New brain puzzles every day.
#shorts #puzzle #brainteaser #findthedifference
Tags: find the odd one out, hidden letter, find the number, brain teaser, puzzle, eye test, brain test
- txt-001: Find the Odd Letter 🔍 Level 3 Is Brutal
- txt-002: Only 3 Seconds to Spot It 👀 Find the Odd Letter
- txt-003: Can You Find the Hidden Number? 🔢
- txt-004: Your Eyes vs Level 3 🔍 Odd Letter Challenge
- txt-005: Spot the Odd Character Before Time Runs Out ⏱️
- txt-006: Find the Hidden Letter 🧠 3 Levels
- txt-007: Sharp Eyes Only 👁️ Find the Odd One Out
- txt-008: Find It in 7 Seconds 🔍 Letters Edition
- txt-009: Level 1 Easy… Level 3? 😳 Find the Odd Letter
- txt-010: Hidden Number Challenge 🔢 Can You Find All 3?
- txt-011: This Puzzle Tricks Your Eyes 👀 Odd Letter
- txt-012: Find the Odd One Out 🔍 Letters & Numbers

## Format 4 — Color vision test (`oddone2.py SEED OUT.mp4 color`) → channel2/color/col-NNN.mp4
One tile is a slightly different shade; the gap shrinks every level (16% → 8.5% → 4.5% lightness).
Description: Find the tile with a different color before time runs out! 🎨 How many did you get?
Comment 1, 2 or 3 👇  New brain puzzles every day.
#shorts #colortest #eyetest #puzzle
Tags: color test, color vision test, find the different color, eye test, brain teaser, puzzle, brain test
- col-001: Find the Different Color 🎨 Level 3 Is Almost Impossible
- col-002: How Good Are Your Eyes? 🎨 Color Test
- col-003: Spot the Different Shade 👁️ 3 Levels
- col-004: Color Vision Test 🎨 Can You Pass Level 3?
- col-005: Find the Odd Color in 7 Seconds ⏱️
- col-006: Your Eyes vs Level 3 🎨 Color Challenge
- col-007: Only Sharp Eyes See This Color 👀
- col-008: Find the Different Tile 🎨 Before Time Runs Out
- col-009: Color Test: Easy, Medium… Impossible? 😳
- col-010: Which Square Is Different? 🎨
- col-011: Test Your Color Vision 👁️ 3 Levels
- col-012: Find the Odd Shade 🎨 Can You Beat It?

## Emoji titles 011–015
- 011: Find the Odd Emoji 🧠 Level 3 Is Sneaky
- 012: Spot It in 5 Seconds 👀 Odd One Out
- 013: Emoji Challenge: Find the Odd One 🔍
- 014: Your Brain vs 3 Levels 🧠 Odd Emoji
- 015: Find the Odd One Out ⏱️ Beat the Timer

## Format 5 — Emoji math (`channel2/emojimath.py SEED OUT.mp4`) → channel2/math/math-NNN.mp4
Three clue equations, a final line mixing + and × (order of operations), 8-second countdown, step-by-step
solution. ~22 s. Ends with "Did you get it? YES / NO".
Description: Can you solve this emoji math puzzle? 🧮 Work out each emoji, then solve the last line.
Comment your answer before the reveal 👇  New brain puzzles every day.
#shorts #mathpuzzle #brainteaser #emojipuzzle
Tags: emoji math, math puzzle, brain teaser, riddle, order of operations, iq test, puzzle
- math-001: Can You Solve This Emoji Math? 🧮 Watch the Last Line
- math-002: Can You Get the Last Line Right? 🤔
- math-003: Emoji Math Puzzle 🍎 Watch the Order of Operations
- math-004: Solve It Before the Timer Ends ⏱️ Emoji Math
- math-005: This Emoji Equation Splits the Comments 😳
- math-006: Can You Find the Answer? 🧠 Emoji Math
- math-007: Emoji Math: Easy… Until the Last Line 🤯
- math-008: Comment Your Answer! 🧮 Emoji Puzzle
- math-009: Brain Teaser: What's the Final Number? 🔢
- math-010: Emoji Math Challenge 🧠 Can You Beat It?
- math-011: Quick Math With Emojis ⏱️ Try It
- math-012: Do You Know What Comes First? ✖️➕ Emoji Math
(No made-up statistics in titles: never quote a % or claim "most people fail".)

## Format 6 — Spot the difference (`channel2/spotdiff.py SEED OUT.mp4`) → channel2/spotdiff/diff-NNN.mp4
Two emoji scenes (garden / ocean / space / kitchen / farm), 3 differences (missing, swapped, shrunk),
12-second countdown, differences circled one by one. ~21 s.
Description: Find 3 differences between the two pictures before time runs out! 🔎 How many did you find?
Comment 1, 2 or 3 👇  New brain puzzles every day.
#shorts #spotthedifference #puzzle #brainteaser
Tags: spot the difference, find the difference, find 3 differences, puzzle, brain teaser, eye test
- diff-001: Find 3 Differences in 12 Seconds 🔎 Garden
- diff-002: Spot the Difference 🌊 Ocean Edition
- diff-003: Find 3 Differences 🚀 Space Edition
- diff-004: Spot 3 Differences Before Time Runs Out 🍳
- diff-005: Find the Difference 🐄 Farm Edition
- diff-006: Can You Spot All 3? 🔎 Garden
- diff-007: Sharp Eyes Only 👀 Ocean Spot the Difference
- diff-008: Find 3 Differences 🪐 Can You Beat the Timer?
- diff-009: Spot the Difference 🧀 Kitchen Edition
- diff-010: 3 Differences, 12 Seconds 🔎 Farm
