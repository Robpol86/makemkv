FROM frolvlad/alpine-glibc
MAINTAINER Robpol86 <robpol86@gmail.com>

RUN apk add --no-cache bash expat ffmpeg-libs libc6-compat libressl-dev libstdc++ sudo && \
    ln -s /lib/libcrypto.so.38 /lib/libcrypto.so.10 && \
    adduser -Ds /sbin/nologin mkv && \
    addgroup mkv cdrom && \
    sudo -u mkv mkdir /home/mkv/.MakeMKV

COPY lib/libdriveio.so.0 /lib/libdriveio.so.0
COPY lib/libmakemkv.so.1 /lib/libmakemkv.so.1

VOLUME /output
WORKDIR /output
COPY bin/env.sh /env.sh
COPY bin/rip.sh /rip.sh
COPY etc/settings.conf /home/mkv/.MakeMKV/settings.conf
COPY lib/force_umask.so /force_umask.so

CMD ["/rip.sh"]
