#!/bin/bash

# Run makemkvcon in headless mode to rip DVDs or Blu-rays.
# https://github.com/Robpol86/makemkv/blob/master/bin/rip.sh
# Save as (chmod +x): /rip.sh

set -E  # CalL ERR traps when using -e.
set -e  # Exit script if a command fails.
set -u  # Treat unset variables as errors and exit immediately.
set -o pipefail  # Exit script if pipes fail instead of just the last program.

# Source function library.
source /env.sh

# Print environment.
if [ "$DEBUG" == "true" ]; then
    set -x  # Print command traces before executing command.
    env |sort
fi

# Verify the device.
if [ -z "$DEVNAME" ]; then
    echo -e "\nERROR: Unable to find optical device.\n" >&2
    exit 1
fi
if [ ! -b "$DEVNAME" ]; then
    echo -e "\nERROR: Device $DEVNAME not a block-special file.\n" >&2
    exit 1
fi

# Setup trap for hooks and FAILED_EJECT.
trap on_err ERR

# Prepare the environment before ripping.
prepare

# Rip media.
echo "Ripping..."
sudo -u mkv LD_PRELOAD=/force_umask.so makemkvcon mkv ${DEBUG:+--debug} --progress -same --directio true \
    "dev:$DEVNAME" all "$DIR_WORKING" \
    |low_space_term \
    |catch_failed

# Move media from incoming directory to movie directory.
sudo -u mkv mv "$DIR_WORKING/"* "$DIR_FINAL/"
sudo -u mkv rmdir "$DIR_WORKING"

# Eject.
if [ "$NO_EJECT" != "true" ]; then
    echo "Ejecting..."
    eject ${DEBUG:+--verbose} "$DEVNAME"
fi

echo Done after $(date -u -d @$SECONDS +%T) with $(basename "$DIR_FINAL")
