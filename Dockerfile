FROM robpol86/makemkv
RUN dnf install -y ffmpeg
COPY hook-post-success-eject.sh /hook-post-success-eject.sh
