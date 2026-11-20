#!/bin/sh
# Builds the punchline sound effects in assets/sfx from math (ffmpeg aevalsrc), no samples.
# They are our own work, released as CC0 1.0 (see README "Sound effects").
set -e
D=$(dirname "$0")/../assets/sfx
mkdir -p "$D"
# boom: pitch-dropping sub hit with a short transient
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.9*sin(2*PI*(90*t-30*t*t))*exp(-3.5*t)+0.35*sin(2*PI*(180*t-60*t*t))*exp(-6*t)+0.35*(random(0)*2-1)*exp(-90*t)':s=48000:d=1.1" \
  -af "lowpass=f=2500,afade=t=out:st=0.9:d=0.2,aformat=channel_layouts=stereo" "$D/boom.wav"
# ding: bright bell
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.45*sin(2*PI*1568*t)*exp(-4*t)+0.22*sin(2*PI*3136*t)*exp(-7*t)+0.15*sin(2*PI*2352*t)*exp(-5*t)':s=48000:d=1.2" \
  -af "afade=t=in:d=0.004,afade=t=out:st=1.0:d=0.2,aformat=channel_layouts=stereo" "$D/ding.wav"
# pop: quick rising blip
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.8*sin(2*PI*(500*t+5000*t*t))*exp(-35*t)':s=48000:d=0.18" \
  -af "afade=t=in:d=0.003,aformat=channel_layouts=stereo" "$D/pop.wav"
# rewind: tape-rewind sweep, played as the slow-motion replay starts
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.5*sin(2*PI*(1800*t-1400*t*t))*(0.6+0.4*sin(2*PI*28*t))+0.12*(random(0)*2-1)':s=48000:d=0.55" \
  -af "bandpass=f=1500:width_type=o:w=2,afade=t=in:d=0.05,afade=t=out:st=0.35:d=0.2,volume=1.6,aformat=channel_layouts=stereo" "$D/rewind.wav"
ls -la "$D"
