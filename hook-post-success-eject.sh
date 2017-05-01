#!/bin/bash

# After successfully ripping the disc, strip out subtitles and other languages
# from each MKV file.

DIR_ORIGINAL=${DIR_FINAL}/.original
DIR_WORKING=${DIR_FINAL}/.working

mkdir "$DIR_ORIGINAL" "$DIR_WORKING"

for src_file in "$DIR_FINAL"/*.mkv; do
    filename=$(basename "$src_file")
    dst_file="$DIR_WORKING/$filename"
    ffmpeg -i "$src_file" -map 0:0 -map 0:1 -acodec copy -vcodec copy -sn "$dst_file"
    mv "$src_file" "$DIR_ORIGINAL"
    mv "$dst_file" "$DIR_FINAL"
done
