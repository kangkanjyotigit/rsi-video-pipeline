#!/usr/bin/bash
set -e
P="C:/Users/kangk/Desktop/Projects/rsi-video"
M="$P/scenes/media/videos/rsi/1080p30"
O="$P/out"
> "$O/clist.txt"
for i in 0 1 2 3 4 5; do
  ffmpeg -y -v error -i "$M/S$i.mp4" -i "$P/audio/seg$i.wav" \
    -map 0:v -map 1:a -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 160k \
    -shortest "$O/part$i.mp4"
  echo "file '$O/part$i.mp4'" >> "$O/clist.txt"
done
ffmpeg -y -v error -f concat -safe 0 -i "$O/clist.txt" -c copy "$O/rsi_nosub.mp4"
ffmpeg -y -v error -i "$O/rsi_nosub.mp4" -i "$O/rsi_video.srt" \
  -c copy -c:s mov_text "$O/rsi_video_final.mp4"
echo DONE
ffprobe -v error -show_entries format=duration,size -of default "$O/rsi_video_final.mp4"
