#!/bin/bash

# If eject fails (usually over IPMI) still run ffmpeg on successfully ripped
# files.

source /hook-post-success-eject.sh
