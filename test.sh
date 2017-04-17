#!/bin/bash

set -e  # Exit script if a command fails.
set -u  # Treat unset variables as errors and exit immediately.
set -x  # Print command traces before executing command.
set -o pipefail  # Exit script if pipes fail instead of just the last program.

MKV_GLOB=/tmp/MakeMKV/Sample_2017-04-15-15-16-14-00_???/title00.mkv

# Verify generated MKV file.
verify () {
    # Verify no extra files remain.
    test $(find /tmp/MakeMKV -print |tee /dev/stderr |wc -l) -eq 3
    test $(ls -l ${MKV_GLOB} |tee /dev/stderr |wc -l) -eq 1
    local MKV=$(ls ${MKV_GLOB} |tee /dev/stderr)

    # Verify mkv file stat.
    test "$(stat -c %u ${MKV} |tee /dev/stderr)" == "$UID"
    test "$(stat -c %g ${MKV} |tee /dev/stderr)" == "$(id -g)"
    test "$(stat -c %a ${MKV} |tee /dev/stderr)" == 644
    test "$(stat -c %s ${MKV} |tee /dev/stderr)" == 17345216

    # Cleanup.
    rm -r /tmp/MakeMKV; mkdir $_
}

# Run manually.
cdemu load 0 sample.iso
source <(sed -n '/^Now go ahead and run the image:$/{:a;n;/```$/b;p;ba}' README.md |tail -n +3)
verify

# Run via udev.
sed -n '/^# Save as:.\+85-makemkv.rules/{:a;n;/```/b;p;ba}' README.md |sudo tee /etc/udev/rules.d/85-makemkv.rules
cdemu load 0 sample.iso
for _ in $(seq 1 20); do sleep 0.5; if stat ${MKV_GLOB} &>/dev/null; then break; fi; done
verify
