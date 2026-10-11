#!/usr/bin/bash
cd "/c/Users/kangk/Desktop/Projects/rsi-video"
uv run --python 3.11 --with manim python calibrate.py >> calibrate.log 2>&1
echo "EXIT:$?" >> calibrate.log
