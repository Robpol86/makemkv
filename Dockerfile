FROM robpol86/makemkv
RUN dnf install -y ffmpeg
COPY hook-post-title.sh /
COPY hook-pre-rip.sh /
