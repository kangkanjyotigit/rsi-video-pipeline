#!/usr/bin/bash
cd "/c/Users/kangk/Desktop/Projects/rsi-video"
uv run --python 3.11 python tts_multi.py >> tts4.log 2>&1
echo "EXIT:$?" >> tts4.log
