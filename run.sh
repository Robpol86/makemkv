#!/bin/bash

# Run makemkvcon in headless mode to rip DVDs or Blu-rays.
# https://github.com/Robpol86/makemkv/blob/master/run.sh
# Save as (chmod +x): /run.sh

set -e  # Exit script if a command fails.
set -u  # Treat unset variables as errors and exit immediately.
set -o pipefail  # Exit script if pipes fail instead of just the last program.

# Kill makemkvcon when not enough disk space. It keeps going no matter what.
catch_low_space () {
    ret=0
    sed "/much as [0-9]\+ megabytes while there are only/q5" -- "$@" || ret=$?
    [ ${ret} -ne 5 ] && return
    echo -e "\nERROR: Terminating MakeMKV due to low disk space.\n"
    kill 0
}


# Rip media.
makemkvcon mkv -r --progress -same disc:0 all /output |catch_low_space
