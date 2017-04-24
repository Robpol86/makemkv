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
    test "$(stat -c %s ${MKV} |tee /dev/stderr)" -gt 17345210 # target size: 17345216
    test "$(stat -c %s ${MKV} |tee /dev/stderr)" -lt 17345220 # target size: 17345216
}

# Assert failures
assert_failed () {
    local ret=0
    docker run -it --device=/dev/cdrom -v /tmp/MakeMKV:/output robpol86/makemkv 2>&1 || ret=$?
    test ${ret} -gt 0
}

# Clean before running test.
sudo umount /tmp/MakeMKV &> /dev/null || true
rm -rf /tmp/MakeMKV
sudo rm -f /etc/udev/rules.d/85-makemkv.rules

# Run test cases.
case "$1" in
    manual)
        # Run manually from README.
        cdemu load 0 sample.iso
        source <(sed -n '/^Now go ahead and run the image:$/{:a;n;/```$/b;p;ba}' README.md |tail -n +3)
        verify
        ;;
    udev)
        # Run via udev from README.
        mkdir /tmp/MakeMKV
        sed -n '/^# Save as:.\+makemkv.rules/{:a;n;/```/b;p;ba}' README.md |sudo tee /etc/udev/rules.d/85-makemkv.rules
        cdemu load 0 sample.iso
        for _ in $(seq 1 20); do sleep 0.5; if stat ${MKV_GLOB} &>/dev/null; then break; fi; done
        verify
        ;;
    low_space)
        # Test low space handling.
        mkdir /tmp/MakeMKV
        dd if=/dev/zero of=/tmp/fs.bin bs=1M count=5
        mkfs.ext4 -F /tmp/fs.bin
        sudo mount -t ext4 -o loop /tmp/fs.bin /tmp/MakeMKV
        cdemu load 0 sample.iso
        assert_failed |grep "ERROR: Terminating MakeMKV due to low disk space."
        ;;
    *)
        echo "INVALID TEST CASE"
        exit 1
esac
