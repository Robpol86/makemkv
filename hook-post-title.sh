#!/bin/bash

# Executed right after an MKV file is done ripping. Just runs run_ffmpeg()
# function from hook-pre-rip.sh.

run_ffmpeg "$TITLE_PATH" &
