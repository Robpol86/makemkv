#!/bin/bash

# Define function that strips out subtitles and other languages from an MKV
# file. Also override move_back() since this hook script takes care of moving
# instead.

# Disable move_back function.
move_back () {
    debug ${0^^} ${FUNCNAME^^}: IGNORED
}

# Run ffmpeg on a file and then move it to the final destination. Outputs an MP4 file instead of MKV.
run_ffmpeg () {
    debug ${0^^} ${FUNCNAME^^}: START
    local src_file="$1"
    local eph_file="${src_file%.*}.mp4"
    local dst_file="$DIR_FINAL/$(basename "$eph_file")"
    sudo -u mkv ffmpeg -i "$src_file" -map 0:0 -map 0:1 -acodec copy -vcodec copy -sn "$eph_file"
    sudo -u mkv mv "$eph_file" "$dst_file"
    debug ${0^^} ${FUNCNAME^^}: EXIT
}
