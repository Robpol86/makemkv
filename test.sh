#!/bin/bash

set -e  # Exit script if a command fails.
set -u  # Treat unset variables as errors and exit immediately.
set -x  # Print command traces before executing command.
set -o pipefail  # Exit script if pipes fail instead of just the last program.

# Run manually.
cdemu load 0 sample.iso
mkdir /tmp/MakeMKV
docker run -it --device=/dev/cdrom -e MKV_GID=$(id -g) -e MKV_UID=$(id -u) -v /tmp/MakeMKV:/output robpol86/makemkv

# Verify no extra files remain.
test $(find /tmp/MakeMKV -print |tee /dev/stderr |wc -l) -eq 3
test $(ls -l /tmp/MakeMKV/Sample_2017-04-15-15-16-14-00_???/title00.mkv |tee /dev/stderr |wc -l) -eq 1
MKV=$(ls /tmp/MakeMKV/Sample_2017-04-15-15-16-14-00_???/title00.mkv |tee /dev/stderr)

# Verify mkv file stat.
test "$(stat -c %u ${MKV} |tee /dev/stderr)" == "$UID"
test "$(stat -c %g ${MKV} |tee /dev/stderr)" == "$(id -g)"
test "$(stat -c %a ${MKV} |tee /dev/stderr)" == 644
test "$(stat -c %s ${MKV} |tee /dev/stderr)" == 17345216
