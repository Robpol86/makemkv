#!/bin/bash

# Run makemkvcon in headless mode to rip DVDs or Blu-rays.
# https://github.com/Robpol86/makemkv/blob/master/run.sh
# Save as (chmod +x): /run.sh

set -e  # Exit script if a command fails.
set -u  # Treat unset variables as errors and exit immediately.
set -o pipefail  # Exit script if pipes fail instead of just the last program.

declare -i MKV_GID=${MKV_GID:-0}
declare -i MKV_UID=${MKV_UID:-0}

# Kill makemkvcon when not enough disk space. It keeps going no matter what.
low_space_term () {
    ret=0
    sed -u "/much as [0-9]\+ megabytes while there are only/q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: Terminating MakeMKV due to low disk space.\n"
    sync
    kill 0
}

# Kill makemkvcon to prevent overwriting/re-ripping.
no_overwrite () {
    ret=0
    sed -u "/Do you want to overwrite it/q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: Terminating MakeMKV due to file already exists.\n"
    sync
    kill 0
}

# Exit 1 if any title failed to rip.
catch_failed () {
    ret=0
    sed -u "/Copy complete. [0-9]\+ titles saved, [0-9]\+ failed./q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: One or more titles failed.\n"
    sync
    exit 1
}

# Update UID and GID of "mkv" user at runtime.
if [ "$MKV_UID" -ne "0" ] && [ "$MKV_UID" -ne "$(id -u mkv)" ]; then
    usermod -ou "$MKV_UID" mkv
fi
if [ "$MKV_GID" -ne "0" ] && [ "$MKV_GID" -ne "$(id -g mkv)" ]; then
    usermod -og "$MKV_GID" mkv
fi

# Rip media.
sudo -u mkv makemkvcon mkv --progress -same disc:0 all /output \
    |low_space_term \
    |no_overwrite \
    |catch_failed
eject
