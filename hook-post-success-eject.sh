#!/bin/bash

# After successfully ripping the disc, strip out subtitles and other languages
# from each MKV file.

DIR_ORIGINAL=${DIR_FINAL}/.original
DIR_WORKING=${DIR_FINAL}/.working

sudo -u mkv mkdir "$DIR_ORIGINAL" "$DIR_WORKING"

for src_file in "$DIR_FINAL"/*.mkv; do
    filename=$(basename "$src_file")
    dst_file="$DIR_WORKING/${filename%.*}.mp4"
    sudo -u mkv ffmpeg -i "$src_file" -map 0:0 -map 0:1 -acodec copy -vcodec copy -sn "$dst_file"
    sudo -u mkv mv "$src_file" "$DIR_ORIGINAL"
    sudo -u mkv mv "$dst_file" "$DIR_FINAL"
done

sudo -u mkv rmdir "$DIR_WORKING"
