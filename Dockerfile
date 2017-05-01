FROM alpine:latest
MAINTAINER Robpol86 <robpol86@gmail.com>

RUN apk add --no-cache bash sudo && \
    adduser -Ds /sbin/nologin mkv && \
    addgroup mkv cdrom && \
    sudo -u mkv mkdir /home/mkv/.MakeMKV

VOLUME /output
WORKDIR /output
COPY bin/env.sh /env.sh
COPY bin/rip.sh /rip.sh
COPY etc/settings.conf /home/mkv/.MakeMKV/settings.conf
COPY lib/force_umask.so /force_umask.so

CMD ["/rip.sh"]
