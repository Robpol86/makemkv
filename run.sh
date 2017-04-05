#!/bin/bash

# Run makemkvcon in headless mode to rip DVDs or Blu-rays.
# https://github.com/Robpol86/makemkv/blob/master/run.sh
# Save as (chmod +x): /run.sh

set -e  # Exit script if a command fails.
set -u  # Treat unset variables as errors and exit immediately.
set -o pipefail  # Exit script if pipes fail instead of just the last program.

declare -i MKV_GID=${MKV_GID:-0}
declare -i MKV_UID=${MKV_UID:-0}
declare -l DEBUG=${DEBUG:-} && [ "$DEBUG" == "true" ] || DEBUG=
declare -l NO_EJECT=${NO_EJECT:-} && [ "$NO_EJECT" == "true" ] || NO_EJECT=
declare -l ROBUST=${ROBUST:-} && [ "$ROBUST" == "true" ] || ROBUST=

# Print environment.
if [ "$DEBUG" == "true" ]; then
    set -x  # Print command traces before executing command.
    env |sort
fi

# Determine destination directory.
ID_FS_LABEL=${ID_FS_LABEL:-$(blkid -o value -s LABEL)}
ID_FS_UUID=${ID_FS_UUID:-$(blkid -o value -s UUID)}
DIRECTORY=/output/${DIRECTORY-${ID_FS_LABEL:-${ID_FS_UUID:-}}}

# Determine device file for ddrescue and eject.
DEVICE=
for d in /dev/cdrom /dev/sr[0-9]*; do
    if [ -b "$d" ]; then
        DEVICE="$d"
        break
    fi
done

# Kill makemkvcon when not enough disk space. It keeps going no matter what.
low_space_term () {
    local ret=0
    sed -u "/much as [0-9]\+ megabytes while there are only/q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: Terminating MakeMKV due to low disk space.\n" >&2
    sync
    kill 0
}

# Kill makemkvcon to prevent overwriting/re-ripping.
no_overwrite () {
    local ret=0
    sed -u "/Do you want to overwrite it/q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: Terminating MakeMKV due to file already exists.\n" >&2
    sync
    kill 0
}

# Exit 1 if any title failed to rip.
catch_failed () {
    local ret=0
    sed -u "/Copy complete. [0-9]\+ titles saved, [0-9]\+ failed./q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: One or more titles failed.\n" >&2
    sync
    exit 1
}

# Update UID and GID of "mkv" user at runtime.
if [ "$MKV_UID" -ne "0" ] && [ "$MKV_UID" -ne "$(id -u mkv)" ]; then
    usermod -ou "$MKV_UID" mkv
fi
if [ "$MKV_GID" -ne "0" ] && [ "$MKV_GID" -ne "$(id -g mkv)" ]; then
    groupmod -og "$MKV_GID" mkv
fi

# Create destination directory.
if [ ! -e "$DIRECTORY" ]; then
    sudo -u mkv mkdir -p "$DIRECTORY"
fi

# Rip media.
echo "Ripping..."
src=disc:0
if [ "$ROBUST" == "true" ]; then
    src="iso:$DIRECTORY/encrypted.iso"
    sudo -u mkv ddrescue -b 2048 -d ${DEBUG:+-v} "$DEVICE" "${src:4}"
    echo "Done ripping to ISO. Converting (lossless) to MKV..."
fi
sudo -u mkv makemkvcon mkv --progress -same "$src" all "$DIRECTORY" \
    |low_space_term \
    |no_overwrite \
    |catch_failed

# Eject.
if [ "$NO_EJECT" != "true" ]; then
    echo "Ejecting..."
    if [ -z "$DEVICE" ]; then
        echo -e "\nERROR: Unable to find optical device to eject.\n" >&2
        exit 1
    fi
    eject ${DEBUG:+--verbose} "$DEVICE"
fi

# Cleanup.
if [ "$ROBUST" == "true" ]; then
    sudo -u mkv rm ${DEBUG:+-v} "${src:4}"  # Delete ISO since makemkvcon finished.
fi

echo "Done after $(date -u -d @$SECONDS +%T)"
