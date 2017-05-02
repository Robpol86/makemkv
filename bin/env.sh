# Functions and variables to be used by scripts in this Docker container.

# Define main variables with default options if not explicitly set by user.
declare -xi MKV_GID=${MKV_GID:-0}
declare -xi MKV_UID=${MKV_UID:-0}
declare -xl DEBUG=${DEBUG:-}
declare -xl FAILED_EJECT=${FAILED_EJECT:-}
declare -xl NO_EJECT=${NO_EJECT:-}
export DEVNAME=${DEVNAME:-}
export DIR_FINAL=
export DIR_WORKING=
export ID_FS_LABEL=${ID_FS_LABEL:-}
export ID_FS_UUID=${ID_FS_UUID:-}
export UMASK=${UMASK:-$(umask)}

# Set false booleans to null for fancy bash tricks in rip.sh.
if [ "$DEBUG" != "true" ]; then DEBUG=; fi
if [ "$FAILED_EJECT" != "true" ]; then FAILED_EJECT=; fi
if [ "$NO_EJECT" != "true" ]; then NO_EJECT=; fi

# Detect the device.
if [ -z "$DEVNAME" ]; then
    for _device in /dev/cdrom /dev/sr[0-9]*; do
        if [ -b "$_device" ]; then
            DEVNAME="$_device"
            break
        fi
    done
    unset _device
fi

# Get disc label/UUID if not run through udev rule.
if [ -n "$DEVNAME" ] && [ -b "$DEVNAME" ]; then
    if [ -z "$ID_FS_LABEL" ]; then ID_FS_LABEL=$(blkid -o value -s LABEL "$DEVNAME" || true); fi
    if [ -z "$ID_FS_UUID" ]; then ID_FS_UUID=$(blkid -o value -s UUID "$DEVNAME" || true); fi
fi

# Write debug statements to stderr.
debug () {
    if [ "$DEBUG" == "true" ]; then
        echo $@ >&2
    fi
}

# Source hook script if available.
hook () {
    local -x _HOOK_SCRIPT="/hook-$1.sh"
    if [ -s "$_HOOK_SCRIPT" ]; then
        debug "FIRING HOOK: $_HOOK_SCRIPT"
        source "$_HOOK_SCRIPT"
        debug "END OF HOOK: $_HOOK_SCRIPT"
    fi
}

# Called when something errors out.
on_err () {
    # Touch failed file.
    if [ -d "$DIR_FINAL" ]; then
        local -x _FAILED_FILE="$DIR_FINAL/failed"
        hook pre-on-err-touch
        sudo -u mkv touch "$_FAILED_FILE"
        hook post-on-err-touch
    fi

    # Eject
    if [ "$NO_EJECT" != "true" ] && [ "$FAILED_EJECT" == "true" ]; then
        hook pre-failed-eject
        echo "Ejecting due to failure..."
        eject ${DEBUG:+--verbose} "$DEVNAME"
        hook post-failed-eject
    fi
}

# Prepare the environment before ripping.
prepare () {
    # Update UID and GID of "mkv" user at runtime.
    if [ "$MKV_UID" -ne "0" ] && [ "$MKV_UID" -ne "$(id -u mkv)" ]; then
        usermod -ou "$MKV_UID" mkv
    fi
    if [ "$MKV_GID" -ne "0" ] && [ "$MKV_GID" -ne "$(id -g mkv)" ]; then
        groupmod -og "$MKV_GID" mkv
    fi

    # Change cdrom gid to match device's group.
    if [ -n "$DEVNAME" ] && [ -b "$DEVNAME" ] && [ "$(stat -c %G "$DEVNAME")" != "cdrom" ]; then
        groupmod -o --gid "$(stat -c %g "$DEVNAME")" cdrom
    fi

    # Set umask.
    umask "$UMASK"
    EDITOR='tee -a' visudo <<< "Defaults umask = $UMASK"

    # Determine destination directory and set its permissions.
    DIR_FINAL=$(mktemp -d "/output/${ID_FS_LABEL:-nolabel}_${ID_FS_UUID:-nouuid}_XXX")
    chown mkv:mkv "$DIR_FINAL"
    DIR_WORKING="$DIR_FINAL/.rip"
    sudo -u mkv mkdir "$DIR_WORKING" && chmod $(stat -c %a "$_") "$DIR_FINAL"
}

# Kill makemkvcon when not enough disk space. It keeps going no matter what.
low_space_term () {
    local ret=0
    sed -u "/much as [0-9]\+ megabytes while there are only/q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: Terminating MakeMKV due to low disk space.\n" >&2
    sync
    kill 0
}

# Exit 1 if any title failed to rip. makemkvcon always exits 0 for some reason.
catch_failed () {
    local ret=0
    sed -u "/Copy complete. [0-9]\+ titles saved, [0-9]\+ failed./q5" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: One or more titles failed.\n" >&2
    sync
    exit 1
}

# Move media from incoming directory to movie directory.
move_back () {
    sudo -u mkv mv "$DIR_WORKING/"* "$DIR_FINAL/"
    sudo -u mkv rmdir "$DIR_WORKING"
}
